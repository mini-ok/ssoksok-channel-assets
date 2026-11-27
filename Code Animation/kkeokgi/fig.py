"""로봇 뼈대 — 포즈 보간(꺾기: 3프레임에 넘어가 살짝 넘쳤다 멎음)과 순운동학. 시간의 순수 함수."""
import math, bisect
import numpy as np
import nums as N
_T = [s[0] * N.BL for s in N.SEQ]

def pose(t):
    i = max(0, bisect.bisect_right(_T, t) - 1); b, name, D, spin = N.SEQ[i]
    cur = np.array(N.P[name], np.float32)
    if i == 0: return cur, i, 0.0
    prev = np.array(N.P[N.SEQ[i - 1][1]], np.float32); tau = t - _T[i]; u = min(1.0, tau / D)
    c1 = 1.9; p = 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2            # back-out: 넘쳤다 돌아옴
    p += 0.035 * math.exp(-max(0, tau - D) / 0.05) * math.sin(2 * math.pi * 16 * max(0, tau - D)) * (u >= 1)
    out = prev + (cur - prev) * p
    if spin: out[11] += 360 * (u * u * (3 - 2 * u))
    out[12] = prev[12] + (cur[12] - prev[12]) * min(1, u) + (0 if cur[12] else 0)
    return out, i, tau

def d(a): a = math.radians(a); return np.array([math.sin(a), math.cos(a)], np.float32)

def joints(t):
    """디자인 좌표의 관절 사전."""
    p, i, tau = pose(t); ual, fal, uar, far, thl, shl, thr, shr, sp, hd, x, rot, lift = [float(v) for v in p]
    Lg = N.L; J = {}
    J['P'] = np.zeros(2, np.float32); u = d(180 - sp); v = np.array([-u[1], u[0]], np.float32)
    J['C'] = u * Lg['sp']; J['SL'] = J['C'] - v * Lg['sh']; J['SR'] = J['C'] + v * Lg['sh']
    J['N'] = J['C'] + u * Lg['neck']; J['H'] = J['N'] + d(180 - sp - hd) * Lg['head']
    J['EL'] = J['SL'] + d(ual) * Lg['ua']; J['HL'] = J['EL'] + d(fal) * Lg['fa']
    J['ER'] = J['SR'] + d(uar) * Lg['ua']; J['HR'] = J['ER'] + d(far) * Lg['fa']
    J['PL'] = np.array([-Lg['hip'], 0], np.float32); J['PR'] = np.array([Lg['hip'], 0], np.float32)
    J['KL'] = J['PL'] + d(thl) * Lg['th']; J['FL'] = J['KL'] + d(shl) * Lg['shn']; J['TL'] = J['FL'] + d(shl - 80) * Lg['foot']
    J['KR'] = J['PR'] + d(thr) * Lg['th']; J['FR'] = J['KR'] + d(shr) * Lg['shn']; J['TR'] = J['FR'] + d(shr + 80) * Lg['foot']
    r = math.radians(rot); R = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]], np.float32)
    for k in J: J[k] = R @ J[k]
    low = max(float(J[k][1]) for k in J) + 22
    off = np.array([N.DW / 2 + x, N.GROUND - low - lift], np.float32)
    for k in J: J[k] = J[k] + off
    J['_ha'] = sp + hd + rot
    return J, i, tau

ENDS = ['HL', 'HR', 'FL', 'FR', 'H']
_em = {}
def emitters(i):
    """i번째 동작에서 가장 많이 움직인 끝점 둘(먹 튀김·고리·선이 여기서 나온다)."""
    if i not in _em:
        a, _, _ = joints(_T[i] - 1e-3) if i > 0 else joints(0); b, _, _ = joints(_T[i] + N.SEQ[i][2] + 0.2 if i < len(_T) - 1 else _T[i] + 1)
        mv = sorted(ENDS, key=lambda k: -float(np.hypot(*(b[k] - a[k]))))[:2]
        _em[i] = [(k, b[k].copy(), (b[k] - a[k])) for k in mv]
    return _em[i]
