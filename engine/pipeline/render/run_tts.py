import sys, os, json, time, wave, re
sys.path.insert(0, "/home/claude/shorts-health")
import numpy as np
import tts
ep = sys.argv[1]
lang_s, chunks = tts.load_script(ep)
lang = "en-US" if lang_s == "en" else "ko-KR"
out = os.path.join(ep, "audio"); os.makedirs(out, exist_ok=True)

def expected(text):
    if lang_s == "ko":
        return len(re.sub(r"[\s\.\,\!\?…\-—'\"]", "", text)) / 7.7 + 0.5
    return len(text.split()) / 3.1 + 0.5

man = []
resyn = 0
for c in chunks:
    dst = os.path.join(out, c["id"] + ".wav")
    if not os.path.exists(dst):
        e = expected(c["tts"]); best = None; tries = 0
        for attempt in range(14):
            act = c.get("act", "") if attempt < 3 else ""
            try:
                x = tts.squeeze_gaps(tts.trim_edges(tts.synth(c["tts"], c.get("sid", 0), lang, act)))
            except RuntimeError as ex:
                if "429" in str(ex) or "TTS 5" in str(ex):
                    time.sleep(20 + attempt * 4); continue
                raise
            tries += 1
            d = len(x) / tts.SR / tts.SPEED
            r = d / e
            if best is None or abs(r - 1) < abs(best[0] - 1): best = (r, x)
            if 0.55 <= r <= 1.6: break
            print("retry", c["id"], round(d, 2), round(e, 2), "noact" if attempt >= 2 else "act", flush=True)
            resyn += 1
        x = best[1]
        x = tts.speed_up(x, tts.SPEED)
        x = np.concatenate([x, np.zeros(int(tts.TAIL * tts.SR), dtype=np.float32)])
        tts.save_wav(dst, x)
        print(c["id"], round(len(x) / tts.SR, 2), "ratio", round(best[0], 2), flush=True)
    w = wave.open(dst); d = w.getnframes() / w.getframerate(); w.close()
    man.append(dict(id=c["id"], dur=round(d, 3), sr=tts.SR))
json.dump(man, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False)
print("done", ep, "chars", tts.CHARS, "total", round(sum(m["dur"] for m in man), 1), "resynth", resyn)
