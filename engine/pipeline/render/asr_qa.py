"""합성 조각 받아쓰기 검수(사용자 지시 2026-10-26): 성우가 '물결표'나 연기 지시문('경쾌한 속도로')을 읽거나 말을 빼먹은 조각을 잡는다.

흐름: 합성한 조각을 음성 인식(ASR)으로 받아 적어 → 원문과 비교 → 이상하면 호출한 쪽(run_tts.py)이 다시 합성한다.
백엔드(ASR_BACKEND, 기본 auto): stt = Google Cloud Speech-to-Text(서비스 계정 키, 프로젝트에서 API가 켜져 있어야 함)
                               whisper = faster-whisper small(CPU, 첫 실행에 모델 내려받기)
                               off = 검수 끔(경고만). auto = stt 시도 → whisper → off.
check()가 (ok, 받아쓴 글, 사유)를 돌려준다. 백엔드를 못 쓰면 ok=True, 사유='asr-unavailable'로 통과시킨다(제작을 막지 않는다).
"""
import base64, difflib, io, os, re, sys, wave
import numpy as np

_state = {"backend": None, "whisper": None, "warned": False}

# 연기 지시·기호 낭독에서 자주 나오는 낱말(원문에 없는데 받아쓰기에 있으면 의심)
LEAK_WORDS_KO = ["물결", "템포", "속도로", "경쾌", "연기", "말투", "목소리", "톤으로", "내레이터", "어린이 교육", "씩씩하게", "느끼하게", "호들갑", "또박또박", "숨차", "한숨 섞어"]
LEAK_WORDS_EN = ["tilde", "wave dash", "squiggle", "narrator", "tempo", "speak", "voice", "tone"]


def norm(s, lang):
    s = s.lower()
    return re.sub(r"[^0-9a-z가-힣]", "", s) if lang == "ko" else re.sub(r"[^0-9a-z ]", "", s).strip()


def _wav_bytes(x, sr):
    b = io.BytesIO()
    w = wave.open(b, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    return b.getvalue()


def _stt(x, sr, lang_s):
    import requests, tts
    r = requests.post("https://speech.googleapis.com/v1/speech:recognize",
                      headers={"Authorization": "Bearer " + tts.token(), "x-goog-user-project": tts.PROJECT},
                      json={"config": {"languageCode": "ko-KR" if lang_s == "ko" else "en-US", "encoding": "LINEAR16",
                                       "sampleRateHertz": sr, "enableAutomaticPunctuation": False},
                            "audio": {"content": base64.b64encode(_wav_bytes(x, sr)).decode()}}, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"STT {r.status_code}: {r.text[:200]}")
    return " ".join(a["alternatives"][0]["transcript"] for a in r.json().get("results", []))


def _whisper(x, sr, lang_s):
    if _state["whisper"] is None:
        from faster_whisper import WhisperModel
        _state["whisper"] = WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(16000, sr)
    y = resample_poly(np.asarray(x, dtype=np.float32), 16000 // g, sr // g).astype(np.float32)   # PyAV 없이 배열을 바로 넘긴다
    segs, _ = _state["whisper"].transcribe(y, language=lang_s, beam_size=3, temperature=0, condition_on_previous_text=False)
    return " ".join(s.text for s in segs)


def _pick_backend(x, sr, lang_s):
    want = os.environ.get("ASR_BACKEND", "auto")
    order = ["stt", "whisper"] if want == "auto" else ([] if want == "off" else [want])
    for b in order:
        try:
            (_stt if b == "stt" else _whisper)(x[: sr], sr, lang_s)   # 1초로 시험
            return b
        except Exception as e:
            print("asr backend", b, "unavailable:", str(e)[:120], file=sys.stderr, flush=True)
    return "off"


def transcribe(x, sr, lang_s):
    if _state["backend"] is None:
        _state["backend"] = _pick_backend(x, sr, lang_s)
        print("ASR backend:", _state["backend"], flush=True)
    b = _state["backend"]
    if b == "off":
        return None
    return (_stt if b == "stt" else _whisper)(x, sr, lang_s)


def check(x, sr, text, lang_s, prompt=""):
    """x: float32 모노 파형(속도 변경 전). text: 읽어야 할 글(기호 정리 뒤). prompt: 연기 지시문 전체.
    돌려주는 값: (ok, 받아쓴 글, 사유)"""
    try:
        heard = transcribe(x, sr, lang_s)
    except Exception as e:
        return True, "", "asr-error:" + str(e)[:80]
    if heard is None:
        return True, "", "asr-unavailable"
    ne, nh = norm(text, lang_s), norm(heard, lang_s)
    if not nh:
        return False, heard, "empty"
    # 1) 낭독 의심 낱말: 원문에는 없는데 받아쓰기에만 있는 연기 지시·기호 낱말
    words = LEAK_WORDS_KO if lang_s == "ko" else LEAK_WORDS_EN
    for w in words:
        nw = norm(w, lang_s)
        if nw and nw in nh and nw not in ne:
            return False, heard, f"leak-word:{w}"
    # 2) 지시문 조각: 지시문의 4글자 창이 원문에는 없는데 받아쓰기에 있으면 낭독 의심(한국어)
    if lang_s == "ko" and prompt:
        npm = norm(prompt, "ko")
        for i in range(len(npm) - 5):
            g = npm[i:i + 6]
            if g in nh and g not in ne:
                return False, heard, f"leak-prompt:{g}"
    # 3) 앞뒤에 낀 군더더기 / 빠진 말
    sm = difflib.SequenceMatcher(None, ne, nh, autojunk=False)
    ratio = sm.ratio()
    blocks = [b for b in sm.get_matching_blocks() if b.size >= 2]
    if blocks:
        head_extra = blocks[0].b - blocks[0].a if blocks[0].b > blocks[0].a else 0
        tail_extra = (len(nh) - (blocks[-1].b + blocks[-1].size)) - (len(ne) - (blocks[-1].a + blocks[-1].size))
        lim = 6 if lang_s == "ko" else 14
        if head_extra >= lim:
            return False, heard, f"extra-head:{head_extra}"
        if tail_extra >= lim:
            return False, heard, f"extra-tail:{tail_extra}"
    cover = sum(bk.size for bk in sm.get_matching_blocks()) / max(1, len(ne))
    if len(ne) >= 8 and cover < 0.5:
        return False, heard, f"missing:{cover:.2f}"
    if ratio < (0.45 if lang_s == "ko" else 0.5):
        return False, heard, f"low-ratio:{ratio:.2f}"
    return True, heard, f"ok:{ratio:.2f}/{cover:.2f}"
