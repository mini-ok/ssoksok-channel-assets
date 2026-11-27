"""사람 비례 실루엣(옆모습) — 키 170cm 기준 관절(cm) → 마스크, 그리고 바닥·벽 그림자.
단위: cm, 화면 좌표(y 아래로). 각도는 '아래 = 0°, 앞(보는 쪽) = 90°, 위 = 180°'(팔다리), 몸통은 수직에서 앞으로 기운 각.
비례는 표준 인체 비례를 근사한 값이고 사진 참고로 조정 전이다(관문 ①).
"""
import math
import numpy as np
import cv2

LEN = dict(ankle=7, shank=38, thigh=41, torso=52, neck=8, head=24, ua=31, fa=26, hand=18, foot=25)   # 서 있을 때 합 170
POSE0 = dict(lean=0, nb=0, hd=0, uaN=0, faN=5, uaF=0, faF=5, thN=0, shN=0, ftN=90, thF=0, shF=0, ftF=90)


def _d(a, f):
    r = math.radians(a); return np.array([math.sin(r) * f, math.cos(r)])


def fk(p, face=1):
    """관절 위치(cm, 골반 = 원점). 순수 함수."""
    p = {**POSE0, **p}; f = face; L = LEN; J = {}
    u = np.array([math.sin(math.radians(p['lean'])) * f, -math.cos(math.radians(p['lean']))])
    J['P'] = np.zeros(2); J['C7'] = u * L['torso']; J['S'] = J['C7'] - u * 5
    nv = np.array([math.sin(math.radians(p['lean'] + p['nb'])) * f, -math.cos(math.radians(p['lean'] + p['nb']))])
    J['N'] = J['C7'] + nv * L['neck']
    hv = np.array([math.sin(math.radians(p['hd'])) * f, -math.cos(math.radians(p['hd']))]); J['hv'] = hv
    J['HC'] = J['N'] + hv * (L['head'] * 0.5 - 1)
    for s in 'NF':
        J['E' + s] = J['S'] + _d(p['ua' + s], f) * L['ua']; J['W' + s] = J['E' + s] + _d(p['fa' + s], f) * L['fa']
        J['T' + s] = J['W' + s] + _d(p['fa' + s] + 8, f) * L['hand']
        J['K' + s] = J['P'] + _d(p['th' + s], f) * L['thigh']; J['A' + s] = J['K' + s] + _d(p['sh' + s], f) * L['shank']
        fv = _d(p['ft' + s], f); nn = np.array([-fv[1] * f, fv[0] * f]) if f > 0 else np.array([fv[1], -fv[0]])
        nn = np.array([-fv[1], fv[0]]) * (1 if f > 0 else -1); J['fv' + s] = fv; J['fn' + s] = nn
        J['H' + s] = J['A' + s] + nn * 3.5; J['O' + s] = J['H' + s] + fv * (L['foot'] - 4)
    return J


def _cap(m, a, b, ra, rb, s):
    n = max(2, int(np.hypot(*(b - a)) * s / max(1.0, min(ra, rb) * s * 0.5)))
    for i in range(n + 1):
        t = i / n; c = a + (b - a) * t; cv2.circle(m, (int(round(c[0])), int(round(c[1]))), max(1, int(round((ra + (rb - ra) * t) * s))), 1.0, -1)


def sil(p, W, H, ox, oy, s, rot=0.0, rc=(0, 0), face=1, cloth=1.0, ss=2):
    """실루엣 마스크(0..1, H×W). 골반을 (ox,oy)px에 두고 rc(cm, 골반 기준) 둘레로 rot도 회전. s = px/cm."""
    J = fk(p, face); r = math.radians(rot); R = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]]); rc = np.array(rc, float)
    def X(q): v = R @ (np.array(q, float) - rc) + rc; return np.array([ox + v[0] * s, oy + v[1] * s]) * ss
    m = np.zeros((H * ss, W * ss), np.float32); S = s * ss; c = cloth
    def cap(a, b, ra, rb): _cap(m, X(a), X(b), ra * S, rb * S, 1.0)
    P, C7 = J['P'], J['C7']; u = (C7 - P) / np.linalg.norm(C7 - P); back = np.array([u[1], -u[0]]) * face   # 몸 뒤쪽 방향
    # 몸통: 척추를 따라 두께가 달라지는 캡슐 사슬(엉덩이 → 허리 → 가슴 → 어깨)
    ch = [(0.00, 10.5 * c, 1.5), (0.20, 9.0 * c, 0.5), (0.45, 9.0 * c, 0.0), (0.75, 10.6 * c, -0.8), (1.00, 8.0 * c, 0.0)]
    pts = [(P + u * (t * 52) + back * sh, rr) for t, rr, sh in ch]
    for (a, ra), (b, rb) in zip(pts[:-1], pts[1:]): cap(a, b, ra, rb)
    cap(J['C7'], J['N'], 5.3, 4.9)
    # 머리: 타원 + 턱 + 뒤통수(머리카락)
    hc = X(J['HC']); hvr = R @ J['hv']; ang = math.degrees(math.atan2(hvr[1], hvr[0])) + 90
    sdv = np.array([-hvr[1], hvr[0]]) * (1 if face > 0 else -1) * -1                    # 얼굴 쪽
    cv2.ellipse(m, (int(hc[0]), int(hc[1])), (int(9.6 * S), int(11.8 * S)), ang, 0, 360, 1.0, -1)
    jaw = hc - hvr * 5.0 * S + sdv * -0.0
    cv2.ellipse(m, (int((hc - hvr * 4.0 * S - sdv * 1.0 * S)[0]), int((hc - hvr * 4.0 * S - sdv * 1.0 * S)[1])), (int(7.2 * S), int(8.0 * S)), ang, 0, 360, 1.0, -1)
    hair = hc + hvr * 1.2 * S + sdv * 1.5 * S
    cv2.ellipse(m, (int(hair[0]), int(hair[1])), (int(10.8 * S), int(12.6 * S)), ang, 0, 360, 1.0, -1)
    nose = hc + sdv * 9.8 * S + hvr * -0.5 * S; cv2.circle(m, (int(nose[0]), int(nose[1])), int(1.9 * S), 1.0, -1)
    chin = hc + sdv * 6.0 * S - hvr * 9.6 * S; cv2.circle(m, (int(chin[0]), int(chin[1])), int(2.6 * S), 1.0, -1)
    # 팔·손
    for s_ in 'FN':
        cap(J['S'], J['E' + s_], 5.0 * c, 4.2 * c); cap(J['E' + s_], J['W' + s_], 4.2 * c, 3.2); cap(J['W' + s_], J['T' + s_], 3.4, 2.2)
    # 다리·발(바지 헐렁하게)
    for s_ in 'FN':
        cap(J['P'], J['K' + s_], 9.5 * c, 6.6 * c); cap(J['K' + s_], J['A' + s_], 6.3 * c, 4.6 * c)
        cap(J['A' + s_], J['H' + s_], 4.4, 4.0); cap(J['H' + s_], J['O' + s_], 4.2, 3.0)
    m = cv2.GaussianBlur(m, (0, 0), 2.0 * ss); m = np.clip((m - 0.42) * 7.5, 0, 1)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA), J, (R, rc, ox, oy, s)


def point(J, key, T):
    R, rc, ox, oy, s = T; v = R @ (np.array(J[key], float) - rc) + rc; return np.array([ox + v[0] * s, oy + v[1] * s])


def floor_shadow(mask, yf, lx, ky, x_contact, soft=(2.0, 16.0), reach=380.0):
    """바닥 그림자: 높이 h=yf-y 인 점이 (x+lx·h, yf−ky·h)로. 접촉점에서 멀수록 번진다."""
    H, W = mask.shape
    A = np.float32([[1, -lx, lx * yf], [0, -ky, yf * (1 + ky)]])   # x'=x+lx·h, y'=yf+ky·h (h=yf−y, 바닥 아래쪽=보는 이 쪽으로)
    sh = cv2.warpAffine(mask, A, (W, H), flags=cv2.INTER_LINEAR)
    a = cv2.GaussianBlur(sh, (0, 0), soft[0]); b = cv2.GaussianBlur(sh, (0, 0), soft[1])
    x = np.arange(W, dtype=np.float32)[None, :]; w = np.exp(-np.abs(x - x_contact) / reach)
    return a * w + b * (1 - w)


def wall_shadow(mask, anchor, scale, dx, dy, blur):
    H, W = mask.shape
    A = np.float32([[scale, 0, anchor[0] - anchor[0] * scale + dx], [0, scale, anchor[1] - anchor[1] * scale + dy]])
    return cv2.GaussianBlur(cv2.warpAffine(mask, A, (W, H), flags=cv2.INTER_LINEAR), (0, 0), blur)
