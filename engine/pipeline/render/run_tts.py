import sys, os, json, time, wave, re
sys.path.insert(0, "/home/claude/shorts-health")
import numpy as np
import tts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asr_qa
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
        e = expected(c["tts"]); best = None; tries = 0; qa_log = ""; leaked = False
        spoken = tts.clean_text(c["tts"])
        for attempt in range(14):
            act = c.get("act", "") if attempt < 3 else ""
            # 낭독이 잡히면 지시문을 줄이고(min), 그래도 반복되면 지시문 없이(none) 합성한다
            mode = None if (attempt < 3 or not leaked) else ("min" if attempt < 6 else "none")
            try:
                x = tts.squeeze_gaps(tts.trim_edges(tts.synth(c["tts"], c.get("sid", 0), lang, act, mode)))
            except RuntimeError as ex:
                if "429" in str(ex) or "TTS 5" in str(ex):
                    time.sleep(20 + attempt * 4); continue
                raise
            tries += 1
            d = len(x) / tts.SR / tts.SPEED
            r = d / e
            ok_dur = 0.55 <= r <= 1.6
            # 받아쓰기 검수: 물결표·연기 지시문 낭독, 군더더기, 빠진 말을 잡는다(백엔드가 없으면 통과)
            qa_ok, heard, why = asr_qa.check(x, tts.SR, spoken, lang_s, tts.build_prompt(c.get("sid", 0), lang, act, mode))
            score = abs(r - 1) + (0 if qa_ok else 5)
            if best is None or score < best[2]: best = (r, x, score, why)
            if ok_dur and qa_ok: break
            print("retry", c["id"], round(d, 2), round(e, 2), "noact" if attempt >= 2 else "act", "| QA:", why, "|", heard.strip()[:60], flush=True)
            qa_log = why
            if why.startswith("leak"): leaked = True
            resyn += 1
        x = best[1]
        x = tts.speed_up(x, tts.SPEED)
        x = np.concatenate([x, np.zeros(int(tts.TAIL * tts.SR), dtype=np.float32)])
        tts.save_wav(dst, x)
        print(c["id"], round(len(x) / tts.SR, 2), "ratio", round(best[0], 2), "QA", best[3], flush=True)
        if not (best[3].startswith("ok") or best[3].startswith("asr-")): print("QA-FAIL-KEPT", c["id"], best[3], flush=True)
    w = wave.open(dst); d = w.getnframes() / w.getframerate(); w.close()
    man.append(dict(id=c["id"], dur=round(d, 3), sr=tts.SR))
json.dump(man, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False)
print("done", ep, "chars", tts.CHARS, "total", round(sum(m["dur"] for m in man), 1), "resynth", resyn)
