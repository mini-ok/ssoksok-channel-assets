import sys
from bg import painted
for k in sys.argv[1:]:
    painted(k); print(k, flush=True)
