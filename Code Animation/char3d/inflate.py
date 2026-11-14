"""2D 캐릭터 실루엣(chars.py 경로)을 부풀려 3D 메시(GLB)로 만든다.
사용: python3 inflate.py <name> <out_dir>   → <out_dir>/<name>_body.glb (+ 부속: _hair, _shell_* 등)
좌표: chars.py 픽셀(y 아래 +) → 3D 1단위 = 300px, y 위 +. 원점은 2D 원점 그대로."""
import sys, os, numpy as np, cv2, trimesh
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
import scipy.sparse as sps
from scipy.sparse.linalg import spsolve

def poisson_height(inside):
    idx = -np.ones(inside.shape, int); ys, xs = np.nonzero(inside); n = len(ys); idx[ys, xs] = np.arange(n)
    rows, cols, vals = [np.arange(n)], [np.arange(n)], [np.full(n, 4.0)]
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        j = idx[ys + dy, xs + dx]; ok = j >= 0
        rows.append(np.arange(n)[ok]); cols.append(j[ok]); vals.append(np.full(ok.sum(), -1.0))
    A = sps.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n))
    sol = spsolve(A, np.ones(n)); h = np.zeros(inside.shape); h[ys, xs] = sol; return h

def bez(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3

def path(start, curves):
    P = lambda a: np.array(a, float); pts = []; cur = P(start)
    for c in curves:
        pts.append(bez(cur, P(c[0]), P(c[1]), P(c[2]))); cur = P(c[2])
    return np.vstack(pts)

def oval(cx, cy, w, h, n=160):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); return np.stack([cx + w / 2 * np.cos(t), cy + h / 2 * np.sin(t)], 1)

def circle(cx, cy, r): return oval(cx, cy, 2 * r, 2 * r)

def rrect(x, y, w, h, rx, ry, n=24):
    pts = []
    for (cx, cy, a0) in ((x + w - rx, y + ry, -np.pi / 2), (x + w - rx, y + h - ry, 0), (x + rx, y + h - ry, np.pi / 2), (x + rx, y + ry, np.pi)):
        t = np.linspace(a0, a0 + np.pi / 2, n); pts.append(np.stack([cx + rx * np.cos(t), cy + ry * np.sin(t)], 1))
    return np.vstack(pts)

heart_outline = lambda: path((0, 150), [((-210, 30), (-160, -150), (-60, -140)), ((-20, -136), (0, -110), (0, -84)),
                                       ((0, -110), (20, -136), (60, -140)), ((160, -150), (210, 30), (0, 150))])
# 각 부위: polys(채울 다각형 목록), H(앞으로 부푸는 높이), back(뒤쪽 비율)
SHAPES = {
    'heart': {'body': dict(polys=[heart_outline()], H=0.34, back=0.85)},
    'brain': {'body': dict(polys=[oval(0, 10, 290, 260)], H=0.36, back=0.9),
              'hair': dict(polys=[circle(-72, -112, 58), circle(-8, -140, 66), circle(66, -116, 58), circle(-34, -96, 50), circle(36, -98, 50)], H=0.2, back=0.85)},
    'gut':   {'body': dict(polys=[rrect(-145, -130, 290, 270, 130, 120)], H=0.37, back=0.9)},
    'liver': {'body': dict(polys=[path((-160, 10), [((-170, -110), (-40, -140), (40, -120)), ((140, -100), (175, -30), (150, 40)),
                                                 ((125, 120), (30, 140), (-40, 130)), ((-120, 120), (-155, 80), (-160, 10))])], H=0.33, back=0.85)},
}
# 몸 표면에서 띠 모양으로 떼어 내 살짝 띄운 껍질(두건·고글 끈). 2D y 경계가 x에 따라 정해진다
def bandana_bottom(x):   # 간 두건 아랫선(chars.py bd 경로 근사)
    return -66 - 0.04 * x - max(0.0, 1 - (x / 125) ** 2) * 40
SHELLS = {
    'liver': {'shell_bandana': dict(top=None, bottom=bandana_bottom, off=0.014)},
    'gut':   {'shell_band': dict(top=lambda x: -99, bottom=lambda x: -73, off=0.012)},
}

def inflate(spec, res=2.5):
    polys = spec['polys']; allp = np.vstack(polys)
    pad = 30; x0, y0 = allp.min(0) - pad; x1, y1 = allp.max(0) + pad
    W, Hh = int((x1 - x0) / res) + 1, int((y1 - y0) / res) + 1
    mask = np.zeros((Hh, W), np.uint8)
    for p in polys: cv2.fillPoly(mask, [np.round((p - [x0, y0]) / res * 8).astype(np.int32)], 1, cv2.LINE_AA, shift=3)
    Hm = spec['H']; h = poisson_height(mask > 0)
    ztop = gaussian_filter(Hm * np.sqrt(np.clip(h / h.max(), 0, 1)) ** 0.9, 1.0) * (mask > 0)
    nz = int(2 * Hm * 300 / res) + 8; zs = (np.arange(nz) - nz / 2) * res / 300.0
    zt = ztop[None] * np.where(zs[:, None, None] >= 0, 1.0, spec['back'])
    F = np.abs(zs)[:, None, None] - zt; F[:, mask == 0] = 0.02; F = gaussian_filter(F, 0.8)
    v, f, _, _ = marching_cubes(F, 0.0, spacing=(res / 300.0,) * 3)
    zc = v[:, 0] - (nz / 2) * res / 300.0; X = v[:, 2] + x0 / 300.0; Y = -(v[:, 1] + y0 / 300.0)
    m = trimesh.Trimesh(np.stack([X, Y, zc], 1), f[:, ::-1], process=True)
    trimesh.smoothing.filter_taubin(m, iterations=20); m.fix_normals()
    if m.volume < 0: m.invert()          # 안팎이 뒤집힌 경우 바로잡음(면이 바깥을 보게)
    return m

def shell_from(m, top, bottom, off):
    c = m.triangles_center; xs, ys2d = c[:, 0] * 300, -c[:, 1] * 300
    ok = np.ones(len(c), bool)
    if top is not None: ok &= ys2d > np.array([top(x) for x in xs])
    if bottom is not None: ok &= ys2d < np.array([bottom(x) for x in xs])
    s = m.submesh([np.nonzero(ok)[0]], append=True)
    s.vertices = s.vertices + s.vertex_normals * off
    return s

if __name__ == '__main__':
    name, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    meshes = {}
    for part, spec in SHAPES[name].items():
        m = inflate(spec); meshes[part] = m; m.export(f'{out}/{name}_{part}.glb')
        print(name, part, len(m.vertices), np.round(m.bounds, 3).tolist())
    for part, sp in SHELLS.get(name, {}).items():
        s = shell_from(meshes['body'], sp['top'], sp['bottom'], sp['off']); s.export(f'{out}/{name}_{part}.glb')
        print(name, part, len(s.vertices), np.round(s.bounds, 3).tolist())
