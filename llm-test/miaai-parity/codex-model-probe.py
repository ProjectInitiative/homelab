import litellm

cands = [
    "gpt-5.4",
    "gpt-5.4-pro",
    "gpt-5.4-mini",
    "gpt-5.3-codex",
    "gpt-5.3-codex-spark",
    "gpt-5.3-codex-mini",
    "gpt-5.3-instant",
    "gpt-5.3-chat-latest",
    "gpt-5.3",
    "codex-mini-latest",
]
for m in cands:
    try:
        r = litellm.completion(
            model="chatgpt/" + m,
            messages=[{"role": "user", "content": "Say PONG"}],
            max_tokens=5,
        )
        print(m, "OK", repr(r.choices[0].message.content)[:40], flush=True)
    except Exception as e:
        s = str(e)
        frag = s[s.find("detail") : s.find("detail") + 100] if "detail" in s else s[:100]
        print(m, "FAIL", frag, flush=True)
