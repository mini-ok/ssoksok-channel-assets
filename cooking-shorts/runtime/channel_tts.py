import re, base64, importlib.util, io, json, os, shutil, subprocess, sys, tempfile, time, wave
import numpy as np
import requests

SR = 24000
ENGINE = os.environ.get("TTS_ENGINE", "gemini")
MODEL = os.environ.get("TTS_MODEL", "gemini-2.5-flash-tts")
G_URL = "https://us-texttospeech.googleapis.com/v1/text:synthesize"
C_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"   # chirp 대체용, 키는 프록시가 붙인다
PROJECT = "ssokssok-health-tts"
SPEED = float(os.environ.get("TTS_SPEED", "1.3"))    # 사용자 지시(2026-10-26): 쇼츠·롱폼 모두 1.3배
TAIL = 0.35   # 조각 끝 여유 무음(다음 조각과 붙지 않게)
# sid: (음성, 한국어 연기 지시, 영어 연기 지시)
SID = {
    0: ("Despina", "밝고 다정한 어린이 교육 애니메이션 내레이터. 경쾌한 속도로, 살짝 웃음기 있게, 문장 끝은 또렷하게.", "Warm, playful kids' animation narrator. Brisk and bright, a smile in the voice."),
    5: ("Orus", "걱정 많은 완벽주의 기획팀장. 빠르게 정리하다가 당황하면 말이 꼬인다.", "A worried perfectionist team lead. Quick, organized, flustered when things go wrong."),
    1: ("Puck", "열정 과다 영업 에이스. 숨차지만 씩씩하고 힘차게.", "An overenthusiastic sales ace. Breathless but upbeat and energetic."),
    2: ("Aoede", "수다쟁이 총무팀 직원. 소문 전하듯 신나고 호들갑스럽게.", "A chatty office gossip. Excited, a little dramatic."),
    3: ("Charon", "묵묵히 야근하는 과장. 낮고 차분하게, 한숨 섞어, 다정함이 묻어나게.", "A quiet, overworked manager. Low and calm, a tired sigh, secretly kind."),
    4: ("Fenrir", "단순 명쾌한 헬스 덕후. 우렁차고 자신만만하게.", "A cheerful gym buff. Loud, simple, confident."),
    6: ("Kore", "원칙주의 보안팀장. 또박또박 단호하게, 살짝 과장된 진지함.", "A by-the-book security chief. Crisp, firm, comically serious."),
    7: ("Leda", "소심하고 졸린 신입. 작고 조심스럽게, 하품 섞어.", "A shy, sleepy new hire. Soft, hesitant, yawning."),
    8: ("Zephyr", "피로 보고서 담당. 지치고 축 처진 목소리.", "The fatigue-report clerk. Drained and droopy."),
    10: ("Achird", "투정 많고 억울한 소화1팀 위 대리. 빠르고 높게, 호들갑스럽게, 그래도 책임감 있게.", "The stomach, an overworked junior staffer. Fast, high, whiny but dutiful."),
    9: ("Sadachbia", "능글맞은 외부 컨설턴트. 여유롭고 장난스럽게, 말끝을 늘인다.", "A smug, smooth consultant. Relaxed, teasing, drawn-out endings."),
}
CHARS = 0
_tok = {"t": None, "exp": 0}

def token():
    if _tok["t"] and time.time() < _tok["exp"] - 120:
        return _tok["t"]
    from google.oauth2 import service_account
    import google.auth.transport.requests as tr
    info = json.loads(base64.b64decode(os.environ["GCP_TTS_SA_KEY_B64"]))
    c = service_account.Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    c.refresh(tr.Request())
    _tok["t"], _tok["exp"] = c.token, time.time() + 3000
    return c.token

def load_script(ep):
    spec = importlib.util.spec_from_file_location("ep_script", os.path.join(ep, "script.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, "LANG", "ko"), m.CHUNKS

def decode(r):
    w = wave.open(io.BytesIO(base64.b64decode(r.json()["audioContent"])))
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

_TILDE = re.compile(r"[~〜～]+")
_SYM = re.compile(r"[♪♬♥♡★☆↑↓→←▶▲▼✔✓※·]|[\U0001F000-\U0001FAFF\u2600-\u27BF]")
def clean_text(text):
    """성우가 '물결표' 등 기호를 읽지 않게 한다. 기호를 그냥 지우면 앞뒤 문장이 붙어 읽히므로
    물결표는 뒤에 문장부호가 없으면 마침표로 바꿔 문장 경계(쉼·억양)를 지킨다. 그 밖의 기호는 공백으로 바꾼다.
    (자막 disp는 그대로)"""
    def _t(m):
        before = text[:m.start()].rstrip()[-1:]
        if before in ".!?…," or re.match(r"\s*[.!?…,]", text[m.end():]):
            return ""
        if before.isalnum() and text[m.end():m.end()+1].isalnum():   # 3~5, A~B 같은 범위
            return " "
        return "."
    t = _TILDE.sub(_t, text)
    t = _SYM.sub(" ", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip() or text

def build_prompt(sid, lang, act="", mode=None):
    """Gemini-TTS에 보내는 연기 지시문. mode=None 전체, "min" 인물 한 문장만, "none" 지시문 없음.
    지시문이 읽을 글보다 훨씬 길면 모델이 지시문을 소리 내어 읽는다(예: '네.' 한 마디에 지시문 전체를 읽음, 2026-10-26 검수에서 확인).
    그래서 아주 짧은 글(synth가 자동 판단)과 재시도 때는 'min'/'none'을 쓴다."""
    voice, ko, en = SID.get(sid, SID[0])
    base = ko if lang == "ko-KR" else en
    if mode == "none":
        return ""
    if mode == "min":
        return re.split(r"(?<=[.。])\s", base)[0]
    pace = " 평소 대화보다 살짝 빠르고 경쾌한 템포로, 늘어지지 않게." if lang == "ko-KR" else " Slightly faster than normal conversation, lively, never dragging."
    return base + pace + (" " + act if act else "")

def synth(text, sid, lang, act="", mode=None):
    global CHARS
    text = clean_text(text)
    voice, ko, en = SID.get(sid, SID[0])
    if ENGINE == "gemini":
        spoken = len(re.sub(r"[\s.,!?…\-—'\"]", "", text))
        if mode is None and spoken < 10:      # 아주 짧은 글은 지시문을 읽기 쉬워 한 문장짜리로 줄인다
            mode = "min"
        prompt = build_prompt(sid, lang, act, mode)
        url, hd = G_URL, {"Authorization": "Bearer " + token(), "x-goog-user-project": PROJECT}
        body = {"input": ({"text": text, "prompt": prompt} if prompt else {"text": text}), "voice": {"languageCode": lang, "name": voice, "modelName": MODEL},
                "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SR}}
    else:
        url, hd = C_URL, {}
        body = {"input": {"text": text}, "voice": {"languageCode": lang, "name": f"{lang}-Chirp3-HD-{voice}"},
                "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": SR}}
    for wait in (0, 2, 4, 8, 16):
        time.sleep(wait)
        r = requests.post(url, headers=hd, json=body, timeout=120)
        if r.status_code == 200:
            CHARS += len(text)
            return decode(r)
        if r.status_code not in (429, 500, 502, 503, 504):
            break
    raise RuntimeError(f"TTS {r.status_code}: {r.text[:300]}")

def trim_edges(x, keep=0.06):
    """앞뒤의 긴 무음만 줄인다(문장 안 쉼과 숨은 건드리지 않는다)."""
    win = int(0.01 * SR); n = len(x) // win
    if n == 0:
        return x
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1))
    idx = np.where(e > max(0.003, 0.02 * e.max()))[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] * win - int(keep * SR)); b = min(len(x), (idx[-1] + 1) * win + int(keep * SR))
    return x[a:b]

def squeeze_gaps(x, max_gap=0.32):
    """문장 안의 긴 침묵(연기 중 생긴 늘어짐)을 max_gap초로 줄인다. 목소리 자체는 건드리지 않는다."""
    win = int(0.01 * SR); n = len(x) // win
    if n == 0:
        return x
    e = np.sqrt((x[:n * win].reshape(n, win) ** 2).mean(1))
    quiet = e < max(0.003, 0.02 * e.max())
    keep, i, lim = [], 0, int(max_gap / 0.01)
    while i < n:
        j = i
        while j < n and quiet[j] == quiet[i]:
            j += 1
        if quiet[i] and j - i > lim:
            h = lim // 2
            keep.append(x[i * win:(i + h) * win]); keep.append(x[(j - (lim - h)) * win:j * win])
        else:
            keep.append(x[i * win:j * win])
        i = j
    keep.append(x[n * win:])
    return np.concatenate(keep)

def save_wav(path, x):
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

def speed_up(x, speed):
    if abs(speed - 1.0) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        save_wav(a, x)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", a, "-filter:a", f"atempo={speed}", "-ar", str(SR), "-ac", "1", b], check=True)
        w = wave.open(b)
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

def main(ep):
    lang_s, chunks = load_script(ep)
    lang = "en-US" if lang_s == "en" else "ko-KR"
    out = os.path.join(ep, "audio"); os.makedirs(out, exist_ok=True)
    reuse = os.environ.get("REUSE")
    src = {m["id"]: m for m in json.load(open(os.path.join(reuse, "audio", "manifest.json")))} if reuse else {}
    manifest = []
    for c in chunks:
        cid = c["id"]; dst = os.path.join(out, cid + ".wav")
        if reuse and cid in src:
            shutil.copy(os.path.join(reuse, "audio", cid + ".wav"), dst); manifest.append(dict(src[cid])); continue
        x = squeeze_gaps(trim_edges(synth(c["tts"], c.get("sid", 0), lang, c.get("act", ""))))
        x = speed_up(x, SPEED)
        x = np.concatenate([x, np.zeros(int(TAIL * SR), dtype=np.float32)])
        save_wav(dst, x)
        manifest.append({"id": cid, "dur": round(len(x) / SR, 3), "sr": SR})
        print(f"{cid:12s} sid{c.get('sid', 0)} {len(x) / SR:6.2f}s")
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False)
    print(f"engine {ENGINE}/{MODEL}  total {sum(m['dur'] for m in manifest):.1f}s  chars_used {CHARS}")

if __name__ == "__main__":
    if sys.argv[1] == "--check":
        x = synth("테스트", 0, "ko-KR"); print("OK", ENGINE, round(len(x) / SR, 2), "s")
    else:
        main(sys.argv[1])
