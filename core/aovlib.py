import os as c, sys as d

# Uu tien ban texture2ddecoder da cai qua pip cua chinh may dang chay (neu
# co) hon ban .pyd dong san trong lib/. File .pyd dong san bien dich rieng
# cho 1 phien ban Python cu the (ABI khac phien ban se khong nap duoc, loi
# "No module named 'texture2ddecoder._texture2ddecoder'"), trong khi ban cai
# qua pip luon dung dung phien ban Python dang chay. Phai thu TRUOC khi lib/
# duoc chen vao sys.path o duoi -- neu thanh cong, sys.modules se cache lai
# ban nay, moi lan 'import texture2ddecoder' sau (ke ca tu ben trong UnityPy)
# se dung lai ban cache thay vi tim lai qua sys.path.
try:
    import texture2ddecoder  # noqa: F401
except ImportError:
    pass

e = c.path.dirname(c.path.abspath(__file__))
f = c.path.dirname(e)
h = [c.path.join(f, 'lib'), f, c.path.dirname(f), c.getcwd()]
aY_found_lib = False
for b in h:
    if b and c.path.isdir(b):
        if c.path.isdir(c.path.join(b, 'UnityPy')) or c.path.isfile(c.path.join(b, 'Protect.py')):
            aY_found_lib = True
            if b not in d.path:
                d.path.insert(0, b)
try:
    import UnityPy
except ImportError as a:
    if not aY_found_lib:
        raise SystemExit("\n[X] Khong thay thu muc 'UnityPy' (ban fork AOV).\n    Chep 'UnityPy/' va 'Protect.py' vao thu muc lib/ cua tool.\n    -> %s\n" % a)
    aY_hint = ''
    if 'texture2ddecoder' in str(a):
        aY_hint = ("\n    Nguyen nhan thuong gap: file .pyd dong san trong lib/texture2ddecoder/\n"
                   "    duoc bien dich rieng cho 1 phien ban Python khac voi phien ban\n"
                   "    ban dang chay (kiem tra bang: python --version).\n"
                   "    Cach sua: mo terminal, chay lenh:\n"
                   "        pip install texture2ddecoder\n"
                   "    (se tu dong lay dung ban khop phien ban Python cua ban).\n")
    raise SystemExit("\n[X] Co 'UnityPy/' trong lib/ nhung import bi loi (khong phai do thieu thu muc).\n    -> %s\n%s" % (a, aY_hint))
try:
    import Protect as g
except ImportError as a:
    raise SystemExit("\n[X] Khong thay 'Protect.py' (chua key AES/SM4 cua AOV).\n    Chep 'Protect.py' vao thu muc lib/ cua tool.\n    -> %s\n" % a)
decrypt_bundle = g.decrypt_bundle
encrypt_bundle = g.encrypt_bundle
