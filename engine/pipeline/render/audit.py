import sys, os, json, re, glob, wave
sys.path.insert(0, "/home/claude/work/sit")
import importlib.util
def load(ep):
    spec = importlib.util.spec_from_file_location("s", ep + "/script.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def expected(lang, text):
    t = re.sub(r"[\s\.\,\!\?…\-—'\"]", "", text)
    if lang == "ko": return len(t) / 7.4 + 0.5
    return len(text.split()) / 3.0 + 0.5
bad = []
for ep in [a for a in sys.argv[1:] if not a.startswith("--")]:
    m = load(ep)
    for c in m.CHUNKS:
        p = f"{ep}/audio/{c['id']}.wav"
        if not os.path.exists(p): continue
        w = wave.open(p); d = w.getnframes() / w.getframerate() - 0.35; w.close()
        e = expected(m.LANG, c["tts"]); r = d / e
        flag = r > 1.6 or r < 0.55
        if flag: bad.append((ep, c["id"])); print(f"BAD {os.path.basename(ep)} {c['id']} dur {d:.2f} exp {e:.2f} r {r:.2f}")
if "--delete" in sys.argv: pass
json.dump(bad, open("/home/claude/work/bad.json", "w"))
print(len(bad), "bad")
