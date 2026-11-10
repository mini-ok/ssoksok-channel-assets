"""출력 배율. JEOM_SCALE=2 → 1920×1080(최종), 기본 1 → 960×540(애니마틱). 캐시·프레임 폴더 이름에 SUF를 붙여 배율끼리 섞이지 않게 한다."""
import os
S = float(os.environ.get('JEOM_SCALE', '1'))
W, H = int(round(960 * S)), int(round(540 * S))
SUF = '' if S == 1 else f'_{W}'
