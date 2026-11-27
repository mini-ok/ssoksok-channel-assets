import numpy as np, cv2, sys, nums as N, fig as F
names = list(N.P.keys()); cols = 8; rows = (len(names) + cols - 1) // cols
img = np.full((rows * 270, cols * 240, 3), 235, np.uint8)
N.SEQ[:] = [(i, n, 0.1, 0) for i, n in enumerate(names)]; F._T[:] = [i * N.BL for i in range(len(names))]
for i, n in enumerate(names):
    J, _, _ = F.joints(i * N.BL + 0.3); ox, oy = (i % cols) * 240, (i // cols) * 270
    q = lambda k: (int(ox + 120 + (J[k][0] - 960) * 0.25), int(oy + (J[k][1]) * 0.25 + 20))
    for a, b in [('P','C'),('C','N'),('N','H'),('SL','SR'),('SL','EL'),('EL','HL'),('SR','ER'),('ER','HR'),('PL','PR'),('PL','KL'),('KL','FL'),('FL','TL'),('PR','KR'),('KR','FR'),('FR','TR')]:
        cv2.line(img, q(a), q(b), (30, 30, 30) if 'L' not in a + b else (40, 40, 200), 3, cv2.LINE_AA)
    cv2.circle(img, q('H'), 10, (30, 30, 30), -1); cv2.line(img, (ox, oy + int(N.GROUND * .25) + 20), (ox + 240, oy + int(N.GROUND * .25) + 20), (150, 150, 150), 1)
    cv2.putText(img, n, (ox + 6, oy + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
cv2.imwrite(sys.argv[1], img)
