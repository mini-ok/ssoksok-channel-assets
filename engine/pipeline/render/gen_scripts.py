import sys, os, json
sys.path.insert(0, '/home/claude/work/sit')
import eps
def w(d, lang, tx, ids, sids):
    os.makedirs(d, exist_ok=True)
    ch = [dict(id=i, tts=tx[i][0], sid=sids[i], act=tx[i][2]) for i in ids]
    open(d + "/script.py", "w").write("LANG = %r\nCHUNKS = %s\n" % (lang, repr(ch)))
R = "/home/claude/work/ep/"
lsid = {c["id"]: c["sid"] for c in eps.L}
lids = [c["id"] for c in eps.L if c["sid"] is not None]
w(R + "ko_long", "ko", eps.KO, lids, lsid); w(R + "en_long", "en", eps.EN, lids, lsid)
for nm, S, tk, te in (("A", eps.SA, eps.SKO_A, eps.SEN_A), ("B", eps.SB, eps.SKO_B, eps.SEN_B)):
    sid = {c["id"]: c["sid"] for c in S}; ids = [c["id"] for c in S]
    w(R + "ko_" + nm, "ko", tk, ids, sid); w(R + "en_" + nm, "en", te, ids, sid)
print("ok", len(lids))
