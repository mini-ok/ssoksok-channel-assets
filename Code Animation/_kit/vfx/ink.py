"""먹·물감 합성: 안료를 흡광도로 쌓고, 화면은 종이 × exp(−흡광도 합).
알파 합성과 달리 옅은 번짐 두 겹이 유약처럼 어두워지고, 색 먹이 탁하지 않게 섞인다.
(출처: 50위 '먹물 서예 놀이' 형식을 제3자가 재구성한 저장소 jungrok5/motion-skills ink-word-world의 방식과 수치.
 원작자 수치가 아니다. 양 기준: 붓 끌기 0.22, 글자 찍기 0.7, 튀김 0.2~0.6, 지나간 자국 0.07. 한 점 1.0을 넘으면 구멍처럼 보인다.)

    k = pigment((0.10, 0.09, 0.08))                 # 흰 종이 위에서 보이는 색(RGB) → 채널별 흡광 계수
    out = composite(paper_bgr, [(wet, k), (dry, k)])  # wet·dry: (H,W) 먹 양 ≥ 0
    ok, info = check(wet + dry)                      # 한 점 1.0 초과·평균 과다 검사
    paper = fibres(paper_bgr, fib, 0.06)             # 섬유는 종이보다 밝게만
"""
import numpy as np

SUMI = (0.10, 0.09, 0.08)       # 따뜻한 검정 먹(RGB, 흰 종이 위 진한 한 겹의 색)
POINT_CAP = 1.0                 # 한 점 먹 양 상한
MEAN_CAP = 1.1                  # 재구성 저장소의 '평균 먹 양' 검사 값(그 저장소 단위 기준, 우리 단위로는 check()의 mean_cap 인자로 조정)


def pigment(rgb_on_white):
    """흰 종이 위에서 보이는 색(RGB 0..1) → 채널별 −ln 값(BGR 순서)."""
    c = np.clip(np.array(rgb_on_white[::-1], np.float32), 1e-3, 1.0)
    return -np.log(c)


def composite(paper, layers, cap_point=POINT_CAP):
    """paper: (H,W,3) BGR 0..1. layers: [(양 지도 (H,W), 흡광 계수 (3,))]. 양은 한 점 cap_point에서 자른다."""
    absorb = np.zeros(paper.shape, np.float32)
    for amt, k in layers:
        absorb += np.clip(amt, 0, cap_point)[..., None].astype(np.float32) * np.asarray(k, np.float32)
    return np.clip(paper * np.exp(-absorb), 0, 1)


def check(amount, cap_point=POINT_CAP, mean_cap=0.35, inked=0.02):
    """'구멍'(한 점 과다)과 '회색 안개'(화면 전체가 먹으로 덮임)를 숫자로 막는다.
    mean_cap은 먹이 올라간 화소(양 > inked)만의 평균 상한이 아니라 화면 전체 평균 상한이다(기본 0.35는 우리 쪽 임시값)."""
    mx, mean = float(amount.max()), float(amount.mean())
    cover = float((amount > inked).mean())
    info = dict(max=mx, mean=mean, cover=cover, over_point=float((amount > cap_point).mean()))
    return (info['over_point'] < 1e-4 and mean <= mean_cap), info


def fibres(paper, fib, amount=0.06):
    """섬유 지도(0..1)를 종이보다 밝게만 더한다(어두운 긁힌 선처럼 보이지 않게)."""
    return np.clip(paper + amount * np.clip(fib, 0, 1)[..., None] * (1 - paper), 0, 1)


def dry_step(wet, dry, rate=0.02, edge_boost=0.5):
    """한 단계 마름: 젖은 먹 일부가 마른 얼룩으로 옮겨 가고, 가장자리에 더 진하게 남는다(테두리 얼룩)."""
    import cv2
    moved = wet * rate
    edge = np.abs(cv2.Laplacian(wet.astype(np.float32), cv2.CV_32F, ksize=3))
    edge = edge / (edge.max() + 1e-6)
    return wet - moved, dry + moved * (1 + edge_boost * edge)
