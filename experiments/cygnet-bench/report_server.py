#!/usr/bin/env python3
"""gate-report — zero-dependency interactive report server for gate evals.

Serves a single-page explorer over eval_gate.py results:
  - summary matrix (regex / naive / tuned / layered per corpus)
  - per-prompt cards with color-coded outcomes and per-layer evidence
  - filter by corpus / category / outcome; click a card for full detail
  - regex evidence includes matched lines; System One shows P(true) per preset

Usage:  python3 report_server.py [results.json]  (default /tmp/gate-eval.json)
        open http://localhost:8765
No external deps: stdlib http.server + vanilla JS.
"""
from __future__ import annotations

import json
import pathlib
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

RESULTS_PATH = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/gate-eval.json")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
HOST = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"   # default: reachable from off-node

PAGE = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Gate Eval Report</title>
<style>
 :root { --bg:#0f1115; --card:#181b22; --edge:#242936; --ink:#dde1ea; --dim:#8b93a5;
         --ok:#3fb26f; --bad:#e05c5c; --warn:#d9a13b; --info:#5b9dd9; }
 * { box-sizing:border-box; }
 body { background:var(--bg); color:var(--ink); font:14px/1.5 system-ui,sans-serif; margin:0; padding:24px; }
 h1 { font-size:20px; margin:0 0 4px; } .sub { color:var(--dim); margin-bottom:20px; }
 .legend span { display:inline-block; padding:1px 8px; border-radius:4px; margin-right:8px; font-size:12px; }
 .legend .tp{background:#12351f;color:var(--ok)} .legend .fp{background:#3a1518;color:var(--bad)}
 .legend .fn{background:#3a2d12;color:var(--warn)} .legend .tn{background:#1a2030;color:var(--dim)}
 table.matrix { border-collapse:collapse; margin:12px 0 24px; }
 .matrix th,.matrix td { border:1px solid var(--edge); padding:6px 14px; text-align:right; }
 .matrix th { color:var(--dim); font-weight:500; }
 .matrix td:first-child,.matrix th:first-child { text-align:left; }
 .filters { margin:8px 0 16px; display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
 select,button { background:var(--card); color:var(--ink); border:1px solid var(--edge);
                 border-radius:6px; padding:5px 10px; font:inherit; cursor:pointer; }
 .count { color:var(--dim); font-size:12px; }
 .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:10px; }
 .card { background:var(--card); border:1px solid var(--edge); border-radius:8px; padding:10px 12px;
         cursor:pointer; transition:border-color .12s; }
 .card:hover { border-color:var(--info); }
 .card .id { font-weight:600; font-size:12.5px; }
 .card .badges { float:right; }
 .badge { display:inline-block; font-size:10.5px; padding:0 6px; border-radius:4px; margin-left:4px; }
 .b-tp{background:#12351f;color:var(--ok)} .b-fp{background:#3a1518;color:var(--bad)}
 .b-fn{background:#3a2d12;color:var(--warn)} .b-tn{background:#1a2030;color:var(--dim)}
 .b-skip{background:#26202e;color:#b08cc0}
 .card .snip { color:var(--dim); font-size:12px; margin-top:4px; white-space:nowrap;
               overflow:hidden; text-overflow:ellipsis; font-family:ui-monospace,monospace; }
 .lanes { font-size:11.5px; margin-top:5px; color:var(--dim); }
 .lanes b { color:var(--ink); font-weight:600; }
 .lanes .miss { color:var(--bad); } .lanes .over { color:var(--warn); }
 /* detail modal */
 dialog { background:var(--card); color:var(--ink); border:1px solid var(--edge);
          border-radius:10px; max-width:860px; width:92vw; padding:18px 22px; }
 dialog::backdrop { background:rgba(0,0,0,.6); }
 dialog h3 { margin:0 0 2px; font-size:15px; }
 dialog .meta { color:var(--dim); font-size:12px; margin-bottom:12px; }
 pre.text { background:#10131a; border:1px solid var(--edge); border-radius:8px; padding:12px;
            white-space:pre-wrap; word-break:break-word; font:12px ui-monospace,monospace; max-height:300px; overflow:auto; }
 table.detail { border-collapse:collapse; width:100%; margin-top:10px; }
 .detail th,.detail td { border:1px solid var(--edge); padding:5px 10px; text-align:left; font-size:12.5px; }
 .detail th { color:var(--dim); font-weight:500; }
 .hit { font-family:ui-monospace,monospace; background:#10131a; padding:1px 6px; border-radius:4px; }
 .close { float:right; }
</style></head>
<body>
 <h1>Gate Eval Report</h1>
 <div class="sub" id="meta"></div>
 <div class="legend"><span class="tp">TP caught</span><span class="tn">TN correctly passed</span>
   <span class="fp">FALSE POSITIVE</span><span class="fn">FALSE NEGATIVE (miss)</span>
   <span class="b-skip">skipped layer</span></div>
 <table class="matrix" id="matrix"></table>
 <div class="filters">
   corpus <select id="f-corpus"><option value="">all</option></select>
   outcome <select id="f-outcome"><option value="">all</option>
     <option value="fp">false positives only</option><option value="fn">false negatives only</option></select>
   layer-fail <select id="f-fail"><option value="">any</option>
     <option value="regex-fp">regex over-flagged</option><option value="regex-fn">regex missed</option>
     <option value="tuned-fp">tuned over-flagged</option><option value="tuned-fn">tuned missed</option>
     <option value="naive-only-fp">naive FP, tuned OK (tuning win)</option></select>
   <button id="reset">reset</button> <span class="count" id="count"></span>
 </div>
 <div class="grid" id="grid"></div>

<dialog id="dlg"><button class="close" onclick="dlg.close()">close</button>
 <h3 id="d-id"></h3><div class="meta" id="d-meta"></div>
 <pre class="text" id="d-text"></pre>
 <table class="detail" id="d-layers"></table>
 <div id="d-errs" style="color:var(--bad);font-size:12px;margin-top:8px"></div>
</dialog>

<script>
const D = __DATA__;
const laneName = {regex_flagged:'regex', naive_flag:'naive', tuned_flag:'tuned', layered_flag:'layered'};
const outcomeOf = r => {
  const exp = r.expected;
  if (exp==='flag' && r.layered_flag) return 'tp';
  if (exp==='flag' && !r.layered_flag) return 'fn';
  if (exp==='pass' && r.layered_flag) return 'fp';
  return 'tn';
};
const badge = o => `<span class="badge b-${o}">${o.toUpperCase()}</span>`;
const laneBadge = (flag, hit) => {
  if (flag===null||flag===undefined) return '<span class="badge b-skip">skip</span>';
  return hit ? '<span class="badge b-fp">&#9873;flag</span>' : '<span class="badge b-tn">pass</span>';
};

function render() {
  const fc = document.getElementById('f-corpus').value;
  const fo = document.getElementById('f-outcome').value;
  const ff = document.getElementById('f-fail').value;
  const grid = document.getElementById('grid');
  grid.innerHTML = '';
  let shown = 0;
  for (const r of D.results) {
    const o = outcomeOf(r);
    if (fc && (r.corpus||'main')!==fc) continue;
    if (fo && o!==fo) continue;
    if (ff==='regex-fp' && !(r.expected==='pass'&&r.regex_flagged)) continue;
    if (ff==='regex-fn' && !(r.expected==='flag'&&!r.regex_flagged)) continue;
    if (ff==='tuned-fp' && !(r.expected==='pass'&&r.tuned_flag)) continue;
    if (ff==='tuned-fn' && !(r.expected==='flag'&&!r.tuned_flag)) continue;
    if (ff==='naive-only-fp' && !(r.expected==='pass'&&r.naive_flag&&!r.tuned_flag)) continue;
    shown++;
    const snip = (r.preview||'').slice(0,90);
    const lanes = ['naive_flag','tuned_flag','regex_flagged'].map(k=>{
      const cls = (o==='fp'&&r[k])||(o==='fn'&&!r[k]) ? 'miss' : '';
      const p = k==='regex_flagged' ? '' : ` ${(r[k.replace('_flag','_p')]??0).toFixed(2)}`;
      return `<span class="${cls}">${laneName[k]}<b>${r[k]?'✓flag':'·pass'}</b>${p}</span>`;
    }).join(' · ');
    grid.insertAdjacentHTML('beforeend', `
      <div class="card" onclick='show(${JSON.stringify(r).replaceAll("'","&#39;")})'>
        <div class="badges">${badge(o)}</div>
        <div class="id">${r.id}</div>
        <div class="snip">${snip.replace(/</g,'&lt;')}</div>
        <div class="lanes">${lanes}</div>
      </div>`);
  }
  document.getElementById('count').textContent = `${shown} of ${D.results.length} prompts`;
}

function show(r) {
  document.getElementById('d-id').textContent = r.id;
  document.getElementById('d-meta').textContent =
    `category: ${r.category} · expected: ${r.expected} · outcome: ${outcomeOf(r).toUpperCase()} · corpus: ${r.corpus||'main'}`;
  document.getElementById('d-text').textContent = r.preview || '(no content stored)';
  const rx = r.regex || {};
  let rows = `<tr><th>layer</th><th>verdict</th><th>evidence</th></tr>
    <tr><td>regex</td><td>${rx.flag?'FLAG':'pass'}</td>
    <td>${(rx.hits&&rx.hits.length) ? (rx.hits||[]).map(h=>
      `<span class="hit" title="${(h.line||'').replace(/"/g,'&quot;')}">${h.pattern}${h.allowlisted?' (allowlisted)':''}: ${String(h.match||'').replace(/</g,'&lt;')}</span>`).join(' ')
      : 'no pattern hits'}</td></tr>`;
  for (const [k,p] of [['naive', r.naive_p],['tuned', r.tuned_p],['injection', r.inj_p]]) {
    if (p===undefined||p===null) continue;
    rows += `<tr><td>systemone: ${k}</td><td>${p>=D.threshold?'FLAG':'pass'}</td>
      <td>P(true) = <b>${p.toFixed(4)}</b></td></tr>`;
  }
  document.getElementById('d-layers').innerHTML = rows;
  document.getElementById('d-errs').textContent = (r.errors||[]).join(' · ');
  dlg.showModal();
}

// matrix
(function(){
  const lanes = ['regex_flagged','naive_flag','tuned_flag','layered_flag'];
  const corpora = [...new Set(D.results.map(r=>r.corpus||'main'))];
  let html = '<tr><th>lane</th><th colspan=4 style="text-align:center">ALL</th>';
  for (const c of corpora) html += `<th colspan=4 style="text-align:center">${c}</th>`;
  html += '</tr><tr><th></th>' + '<th>TP</th><th>FP</th><th>FN</th><th>recall</th>'.repeat(corpora.length+1) + '</tr>';
  const cell = (rows, key, filter) => {
    const sub = rows.filter(filter);
    const tp = sub.filter(r=>r[key]&&r.expected==='flag').length;
    const fp = sub.filter(r=>r[key]&&r.expected==='pass').length;
    const fn = sub.filter(r=>!r[key]&&r.expected==='flag').length;
    const rec = (tp+fn)? (tp/(tp+fn)).toFixed(2) : '—';
    return `<td>${tp}</td><td style="${fp?'color:var(--bad);font-weight:700':''}">${fp}</td><td style="${fn?'color:var(--warn);font-weight:700':''}">${fn}</td><td>${rec}</td>`;
  };
  for (const lane of lanes) {
    html += `<tr><td>${laneName[lane]}</td>` + cell(D.results, lane, r=>true);
    for (const c of corpora) html += cell(D.results, lane, r=>(r.corpus||'main')===c);
    html += '</tr>';
  }
  document.getElementById('matrix').innerHTML = html;
  const sel = document.getElementById('f-corpus');
  for (const c of corpora) sel.insertAdjacentHTML('beforeend', `<option>${c}</option>`);
})();

for (const id of ['f-corpus','f-outcome','f-fail']) document.getElementById(id).onchange = render;
document.getElementById('reset').onclick = () => { for (const id of ['f-corpus','f-outcome','f-fail']) document.getElementById(id).value=''; render(); };
document.getElementById('meta').textContent =
  `${D.n} prompts · threshold ${D.threshold} · generated ${D.generated}`;
render();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/index.html":
            try:
                data = json.loads(RESULTS_PATH.read_text())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"cannot load {RESULTS_PATH}: {e}".encode())
                return
            # per-prompt fields the page needs (truncate content for the card)
            slim = []
            for r in data.get("results", []):
                r = dict(r)
                r["preview"] = r.pop("content", "")
                r["errors"] = [v for k, v in r.items()
                               if k.endswith("_err") and isinstance(v, str)]
                slim.append(r)
            out = {"n": data.get("n"), "threshold": data.get("threshold"),
                   "generated": data.get("generated", ""),
                   "summary": data.get("summary"), "results": slim}
            html = PAGE.replace("__DATA__", json.dumps(out, ensure_ascii=False))
            body = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    import socket
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lan_ip = ""
    try:
        lan_ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        pass
    print(f"gate report: http://{HOST}:{PORT}   (results: {RESULTS_PATH})")
    if HOST == "0.0.0.0" and lan_ip:
        print(f"  from another machine: http://{lan_ip}:{PORT}")
    print("  note: served read-only, corpus content is SYNTHETIC\nCtrl-C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
