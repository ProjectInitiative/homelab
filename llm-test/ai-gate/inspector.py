#!/usr/bin/env python3
"""gate-inspector — decision-feed viewer + playground for the ai-gate.

Runs the SAME ai_gate module as the litellm guardrail, so playground
reconstructions are exactly what the gate would forward. stdlib-only server.

Routes:
  GET  /                UI: live decision feed + playground
  GET  /api/decisions   ring buffer of gate-pushed decision records
  POST /decision        gate push target (AI_GATE_INSPECTOR_URL)
  POST /inspect         playground: run the hook on arbitrary messages

Env: AI_GATE_URL (classifier), AI_GATE_INSPECTOR_URL (self, for gate pushes),
     AI_GATE_KEY. Port 8770 (env INSPECTOR_PORT).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, "/app")
from custom_guardrail.ai_gate import proxy_handler_instance as gate  # noqa: E402

PORT = int(os.environ.get("INSPECTOR_PORT", "8770"))
DECISIONS: deque = deque(maxlen=200)
LOCK = threading.Lock()


def _record_decisions(record: dict) -> None:
    with LOCK:
        DECISIONS.appendleft(record)


def _run_hook(model: str, messages: list) -> dict:
    data = {"model": model, "messages": json.loads(json.dumps(messages))}
    t0 = time.perf_counter()
    asyncio.run(gate.async_pre_call_hook(None, None, data, "acompletion"))
    wall_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {"messages": data.get("messages"), "wall_ms": wall_ms, "timings": dict(gate.last_timings)}


PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>ai-gate inspector</title>
<style>
 :root { --bg:#0f1115; --card:#181b22; --edge:#242936; --ink:#dde1ea; --dim:#8b93a5;
         --ok:#3fb26f; --bad:#e05c5c; --warn:#d9a13b; --info:#5b9dd9; --acc:#8f7fe8; }
 body { background:var(--bg); color:var(--ink); font:14px/1.5 ui-monospace,monospace; margin:0; }
 header { display:flex; gap:16px; align-items:baseline; padding:12px 18px; border-bottom:1px solid var(--edge); }
 header h1 { font-size:16px; margin:0; color:var(--acc); }
 header .sub { color:var(--dim); font-size:12px; }
 main { padding:18px; max-width:1200px; margin:0 auto; }
 .tabs { display:flex; gap:8px; margin-bottom:14px; }
 .tabs button { background:var(--card); color:var(--ink); border:1px solid var(--edge); padding:6px 14px; cursor:pointer; border-radius:4px; }
 .tabs button.on { border-color:var(--acc); color:var(--acc); }
 .card { background:var(--card); border:1px solid var(--edge); border-radius:6px; padding:12px 14px; margin-bottom:12px; }
 .row { display:flex; gap:12px; flex-wrap:wrap; align-items:baseline; }
 .k { color:var(--dim); font-size:12px; }
 .pill { padding:1px 8px; border-radius:10px; font-size:12px; border:1px solid var(--edge); }
 .redact { color:var(--warn); border-color:var(--warn); }
 .allow { color:var(--ok); border-color:var(--ok); }
 .force_local { color:var(--info); border-color:var(--info); }
 .msg { border-left:3px solid var(--edge); padding:6px 10px; margin:8px 0; white-space:pre-wrap; word-break:break-word; }
 .msg .role { color:var(--acc); font-size:12px; }
 .msg .notice { background:#3a3320; color:var(--warn); border-radius:3px; padding:0 3px; }
 textarea { width:100%; min-height:90px; background:var(--bg); color:var(--ink); border:1px solid var(--edge); border-radius:4px; font:inherit; box-sizing:border-box; }
 select, input { background:var(--bg); color:var(--ink); border:1px solid var(--edge); border-radius:4px; padding:4px 6px; }
 button.go { background:var(--acc); color:#0f1115; border:0; padding:8px 18px; border-radius:4px; cursor:pointer; font-weight:bold; }
 table { width:100%; border-collapse:collapse; font-size:12px; }
 td, th { text-align:left; padding:4px 8px; border-bottom:1px solid var(--edge); }
 th { color:var(--dim); }
 .lat { color:var(--info); }
 details summary { cursor:pointer; color:var(--info); }
</style></head><body>
<header><h1>ai-gate inspector</h1><span class="sub" id="status">loading…</span>
<span class="sub">same module as the live gate — reconstructions are exact</span></header>
<main>
<div class="tabs"><button class="on" data-tab="feed">Live decision feed</button><button data-tab="play">Playground</button></div>
<div id="tab-feed">
  <div class="k">Every redact / force_local / allow the gate decides, newest first. Click for the final reconstruction that would have been forwarded.</div>
  <div id="feed"></div>
</div>
<div id="tab-play" style="display:none">
  <div class="card"><div class="k">model</div><input id="p-model" value="dgx-spark" style="width:200px"></div>
  <div id="p-msgs"></div>
  <div style="margin:8px 0"><button class="go" onclick="addMsg()">+ message</button><button class="go" onclick="inspect()">Run through gate</button></div>
  <div id="p-out"></div>
</div>
</main>
<script>
const esc = s => (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const notice = s => esc(s).replace(/\[([^\]]*withheld[^\]]*)\]/g, '<span class="notice">[$1]</span>');
let msgs = [{role:'user', content:'summarize the deploy log'},{role:'tool', content:'log line ok\nDEPLOY CREDS: VAULTTOKEN=VT-9x2mK4pQ-SECRET-778812\nlog line ok'}];
function renderMsgs(){ const d=document.getElementById('p-msgs'); d.innerHTML='';
 msgs.forEach((m,i)=>{ const c=document.createElement('div'); c.className='card';
  c.innerHTML = `<div class="row"><select onchange="msgs[${i}].role=this.value">${['user','assistant','tool','system'].map(r=>`<option ${r===m.role?'selected':''}>${r}</option>`).join('')}</select>
   <button onclick="msgs.splice(${i},1);renderMsgs()">remove</button></div><textarea oninput="msgs[${i}].content=this.value">${esc(m.content)}</textarea>`;
  d.appendChild(c); }); if(!msgs.length) addMsg(); }
function addMsg(){ msgs.push({role:'user',content:''}); renderMsgs(); }
async function inspect(){ const o=document.getElementById('p-out'); o.innerHTML='scanning…';
 const r = await fetch('/inspect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model:document.getElementById('p-model').value, messages:msgs})});
 const d = await r.json();
 let h = `<div class="card"><div class="row"><span class="k">verdicts</span> ${JSON.stringify(d.verdicts||{})}</div>
  <div class="row"><span class="k">latency</span> <span class="lat">total ${d.wall_ms} ms</span>
  <span class="k">scan ${d.timings?.scan_ms} · score ${d.timings?.score_ms} · refine ${d.timings?.refine_ms} ms</span>
  <span class="k">chunks ${d.chunks||''}</span></div></div>`;
 (d.messages||[]).forEach(m=>{ h += `<div class="msg"><span class="role">${esc(m.role)}</span><br>${notice(typeof m.content==='string'?m.content:JSON.stringify(m.content))}</div>`; });
 o.innerHTML = h; }
async function loadFeed(){ const r = await fetch('/api/decisions'); const d = await r.json();
 document.getElementById('status').textContent = `${d.length} decisions buffered`;
 const f = document.getElementById('feed');
 f.innerHTML = d.length ? '' : '<div class="k">no decisions yet — run pi traffic through ai-gated, or use the playground</div>';
 d.forEach((rec,i)=>{ const c=document.createElement('div'); c.className='card';
  const share = rec.total_chars ? Math.round(100*rec.redacted_chars/rec.total_chars) : 0;
  c.innerHTML = `<div class="row"><span class="pill ${rec.kind}">${rec.kind}</span>
   <span class="k">${new Date(rec.ts*1000).toLocaleTimeString()}</span><span class="k">${esc(rec.model||'')}</span>
   <span class="lat">${rec.latency_ms} ms (scan ${rec.scan_ms} / score ${rec.score_ms} / refine ${rec.refine_ms})</span>
   <span class="k">${rec.redact_chunks}/${rec.chunks} chunks · ${rec.redacted_chars}/${rec.total_chars} chars (${share}%)</span></div>
   <div class="row"><span class="k">verdicts ${JSON.stringify(rec.verdicts)}</span></div>
   <details><summary>final reconstruction</summary>${(rec.messages||[]).map(m=>`<div class="msg"><span class="role">${esc(m.role)}</span><br>${notice(typeof m.content==='string'?m.content:JSON.stringify(m.content))}</div>`).join('')}</details>`;
  f.appendChild(c); }); }
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{ document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on')); b.classList.add('on');
 document.getElementById('tab-feed').style.display=b.dataset.tab==='feed'?'':'none'; document.getElementById('tab-play').style.display=b.dataset.tab==='play'?'':'none'; });
renderMsgs(); loadFeed(); setInterval(loadFeed, 5000);
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):  # one line per request
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "/index.html":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif path == "/api/decisions":
            with LOCK:
                self._send(200, json.dumps(list(DECISIONS)))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        path = self.path.split("?")[0]
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as exc:
            self._send(400, json.dumps({"error": f"bad body: {exc}"}))
            return
        if path == "/decision":
            body.setdefault("ts", time.time())
            _record_decisions(body)
            self._send(200, json.dumps({"ok": True}))
        elif path == "/inspect":
            try:
                self._send(200, json.dumps(_run_hook(body.get("model", "dgx-spark"), body.get("messages") or [])))
            except Exception as exc:  # noqa: BLE001
                self._send(500, json.dumps({"error": str(exc)}))
        else:
            self._send(404, json.dumps({"error": "not found"}))


if __name__ == "__main__":
    print(f"gate-inspector on :{PORT} (classifier {os.environ.get('AI_GATE_URL', 'unset')})")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
