# -*- coding: utf-8 -*-
"""
Protect.py — thuat toan ma hoa PLOK (port nguyen tu main.py "Dap nat chim Plok V4").

  * AES-128 CBC thuan Python + SM4 CBC thuan Python (khong can pycryptodome).
  * encrypt_bundle : file UnityFS thuong -> file ma hoa Plok (co UsesAssetBundleEncryption,
                     header size AES ma hoa little-endian + dao byte, blocksinfo SM4-CBC).
  * decrypt_bundle : file Plok -> UnityFS thuong (giai ma + verify round-trip + UnityPy load).
  * is_plok_bundle : kiem tra 1 file co dang mang Plok hay khong.

Giao dien (in_path, out_path) giu nguyen nhu Protect.py cu nen core/ khong phai doi.
"""
import hashlib as hh
import io
import os
import re
import sys
import tempfile as tf
import zipfile as zf
from pathlib import Path as PT

sd = PT(__file__).resolve().parent

# UnityPy duoc import LAZY ben trong cac ham de tranh circular import
# (lib/sm4.py -> Protect -> UnityPy -> ArchiveStorageManager -> sm4).
_up = None
_AF = None
_AO = None
_BF = None
_CH = None


def _upy():
    global _up, _AF, _AO, _BF, _CH
    if _up is None:
        import UnityPy as up
        from UnityPy.enums import ArchiveFlags as AF
        from UnityPy.enums import ArchiveFlagsOld as AO
        from UnityPy.files.BundleFile import BundleFile as BF
        from UnityPy.helpers import CompressionHelper as CH
        _up, _AF, _AO, _BF, _CH = up, AF, AO, BF, CH
    return _up, _AF, _AO, _BF, _CH

sb = bytes.fromhex("637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b27509832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cfd0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdbe0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9ee1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16")
si = bytes(sb.index(i) for i in range(256))
rc = (0, 1, 2, 4, 8, 16, 32, 64, 128, 27, 54)
ss = bytes.fromhex("d690e9fecce13db716b614c228fb2c052b679a762abe04c3aa441326498606999c4250f491ef987a33540b43edcfac62e4b31ca9c908e89580df94fa758f3fa64707a7fcf37317ba83593c19e6854fa8686b81b27164da8bf8eb0f4b70569d351e240e5e6358d1a225227c3b01217887d40046579fd327524c3602e7a0c4c89eeabf8ad240c738b5a3f7f2cef96115a1e0ae5da49b341a55ad933230f58cb1e31df6e22e8266ca60c02923ab0d534e6fd5db3745defd8e2f03ff6a726d6c5b518d1baf92bbddbc7f11d95c411f105ad80ac13188a5cd7bbd2d74d012b8e5b4b08969974a0c96777e65b9f109c56ec68418f07dec3adc4d2079ee5f3ed7cb3948")
fk = (0xa3b1bac6, 0x56aa3350, 0x677d9197, 0xb27022dc)
kc = (0x00070e15, 0x1c232a31, 0x383f464d, 0x545b6269, 0x70777e85, 0x8c939aa1, 0xa8afb6bd, 0xc4cbd2d9, 0xe0e7eef5, 0xfc030a11, 0x181f262d, 0x343b4249, 0x50575e65, 0x6c737a81, 0x888f969d, 0xa4abb2b9, 0xc0c7ced5, 0xdce3eaf1, 0xf8ff060d, 0x141b2229, 0x30373e45, 0x4c535a61, 0x686f767d, 0x848b9299, 0xa0a7aeb5, 0xbcc3cad1, 0xd8dfe6ed, 0xf4fb0209, 0x10171e25, 0x2c333a41, 0x484f565d, 0x646b7279)


def xo(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def xt(v):
    return ((v << 1) ^ (0x11B if v & 0x80 else 0)) & 255


def ml(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = xt(a)
        b >>= 1
    return r


def ek(k):
    e = list(k)
    n = 16
    q = 1
    while n < 176:
        t = e[n - 4:n]
        if n % 16 == 0:
            t = [sb[x] for x in t[1:] + t[:1]]
            t[0] ^= rc[q]
            q += 1
        for x in t:
            e.append(e[n - 16] ^ x)
            n += 1
    return tuple(bytes(e[i:i + 16]) for i in range(0, 176, 16))


def sh(s, iv=False):
    for r in range(1, 4):
        v = [s[r + 4 * c] for c in range(4)]
        v = v[-r:] + v[:-r] if iv else v[r:] + v[:r]
        for c, x in enumerate(v):
            s[r + 4 * c] = x


def mx(s, iv=False):
    for c in range(4):
        i = c * 4
        a, b, d, e = s[i:i + 4]
        if iv:
            s[i] = ml(a, 14) ^ ml(b, 11) ^ ml(d, 13) ^ ml(e, 9)
            s[i + 1] = ml(a, 9) ^ ml(b, 14) ^ ml(d, 11) ^ ml(e, 13)
            s[i + 2] = ml(a, 13) ^ ml(b, 9) ^ ml(d, 14) ^ ml(e, 11)
            s[i + 3] = ml(a, 11) ^ ml(b, 13) ^ ml(d, 9) ^ ml(e, 14)
        else:
            s[i] = ml(a, 2) ^ ml(b, 3) ^ d ^ e
            s[i + 1] = a ^ ml(b, 2) ^ ml(d, 3) ^ e
            s[i + 2] = a ^ b ^ ml(d, 2) ^ ml(e, 3)
            s[i + 3] = ml(a, 3) ^ b ^ d ^ ml(e, 2)


def ab(b, k, dc=False):
    rk = ek(k)
    if dc:
        s = list(xo(b, rk[10]))
        for r in range(9, 0, -1):
            sh(s, True)
            s[:] = [si[x] for x in s]
            s[:] = xo(bytes(s), rk[r])
            mx(s, True)
        sh(s, True)
        s[:] = [si[x] for x in s]
        return xo(bytes(s), rk[0])
    s = list(xo(b, rk[0]))
    for r in range(1, 10):
        s[:] = [sb[x] for x in s]
        sh(s)
        mx(s)
        s[:] = xo(bytes(s), rk[r])
    s[:] = [sb[x] for x in s]
    sh(s)
    return xo(bytes(s), rk[10])


def rl(v, n):
    return ((v << n) | (v >> (32 - n))) & 0xFFFFFFFF


def ta(v):
    return ss[(v >> 24) & 255] << 24 | ss[(v >> 16) & 255] << 16 | ss[(v >> 8) & 255] << 8 | ss[v & 255]


def sk(k):
    w = [int.from_bytes(k[i:i + 4], "big") ^ fk[i // 4] for i in range(0, 16, 4)]
    r = []
    for i in range(32):
        x = ta(w[i + 1] ^ w[i + 2] ^ w[i + 3] ^ kc[i])
        w.append(w[i] ^ x ^ rl(x, 13) ^ rl(x, 23))
        r.append(w[-1])
    return tuple(r)


def sx(b, rk):
    w = [int.from_bytes(b[i:i + 4], "big") for i in range(0, 16, 4)]
    for i in range(32):
        x = ta(w[i + 1] ^ w[i + 2] ^ w[i + 3] ^ rk[i])
        w.append(w[i] ^ x ^ rl(x, 2) ^ rl(x, 10) ^ rl(x, 18) ^ rl(x, 24))
    return b"".join(x.to_bytes(4, "big") for x in w[-1:-5:-1])


def cb(d, k, v, dc=False, sm=False):
    o = bytearray()
    p = v
    rk = sk(k) if sm else None
    if sm and dc:
        rk = tuple(reversed(rk))
    for i in range(0, len(d), 16):
        b = d[i:i + 16]
        if dc:
            x = sx(b, rk) if sm else ab(b, k, True)
            o += xo(x, p)
            p = b
        else:
            x = xo(b, p)
            x = sx(x, rk) if sm else ab(x, k)
            o += x
            p = x
    return bytes(o)


def l4(d, us=0):
    i = 0
    o = bytearray()
    n = len(d)
    while i < n:
        t = d[i]
        i += 1
        a = t >> 4
        if a == 15:
            while True:
                x = d[i]
                i += 1
                a += x
                if x != 255:
                    break
        o += d[i:i + a]
        i += a
        if i >= n:
            break
        q = d[i] | d[i + 1] << 8
        i += 2
        if q <= 0 or q > len(o):
            raise ValueError("LZ4")
        a = t & 15
        if a == 15:
            while True:
                x = d[i]
                i += 1
                a += x
                if x != 255:
                    break
        a += 4
        p = len(o) - q
        for _ in range(a):
            o.append(o[p])
            p += 1
    if us and len(o) != us:
        raise ValueError("LZ4 size")
    return bytes(o)


class AC:
    def __init__(self, k, v):
        self.k = bytes(k)
        self.v = bytes(v)

    def decrypt(self, d):
        return cb(bytes(d), self.k, self.v, True)

    def encrypt(self, d):
        return cb(bytes(d), self.k, self.v)


class S4:
    def __init__(self, k):
        self.k = bytes(k)

    def decrypt(self, d, initial=None):
        return cb(bytes(d), self.k, bytes(initial), True, True)

    def encrypt(self, d, initial=None):
        return cb(bytes(d), self.k, bytes(initial), False, True)


class IM:
    pass


def er(*a, **k):
    raise RuntimeError("Tính năng không dùng")


def cm():
    cr = ty.ModuleType("Crypto")
    ci = ty.ModuleType("Crypto.Cipher")
    ae = ty.ModuleType("Crypto.Cipher.AES")
    ae.MODE_CBC = 2
    ae.new = lambda k, m, v: AC(k, v)
    ci.AES = ae
    cr.Cipher = ci
    sys.modules["Crypto"] = cr
    sys.modules["Crypto.Cipher"] = ci
    sys.modules["Crypto.Cipher.AES"] = ae
    sm = ty.ModuleType("sm4")
    sm.SM4Key = S4
    sys.modules["sm4"] = sm
    lz = ty.ModuleType("lz4")
    lb = ty.ModuleType("lz4.block")
    lb.decompress = l4
    lb.compress = er
    lz.block = lb
    sys.modules["lz4"] = lz
    sys.modules["lz4.block"] = lb
    br = ty.ModuleType("brotli")
    br.compress = er
    br.decompress = er
    sys.modules["brotli"] = br
    for n in ("texture2ddecoder", "etcpak"):
        m = ty.ModuleType(n)
        m.__getattr__ = lambda x: er
        sys.modules[n] = m
    pi = ty.ModuleType("PIL")
    im = ty.ModuleType("PIL.Image")
    dr = ty.ModuleType("PIL.ImageDraw")
    im.Image = IM
    im.FLIP_TOP_BOTTOM = 0
    im.FLIP_LEFT_RIGHT = 1
    im.ROTATE_180 = 2
    im.ROTATE_270 = 3
    im.BICUBIC = 4
    im.open = er
    im.new = er
    im.merge = er
    im.frombytes = er
    im.composite = er
    dr.ImageDraw = IM
    pi.Image = im
    pi.ImageDraw = dr
    sys.modules["PIL"] = pi
    sys.modules["PIL.Image"] = im
    sys.modules["PIL.ImageDraw"] = dr
    tb = ty.ModuleType("tabulate")
    tb.tabulate = lambda rows, headers=(): "\n".join("\t".join(map(str, r)) for r in rows)
    sys.modules["tabulate"] = tb


import types as ty


def ux():
    """Giai nen UnityPy_1.zip (neu co canh tool) va chen vao sys.path — port nguyen tu main.py."""
    zp = sd / "UnityPy_1.zip"
    if not zp.is_file():
        return None, None
    if hh.sha256(zp.read_bytes()).hexdigest() != "64ffc34ceb0737743b62539156d926b09ef2be3e39f0eaab0e6341715c580c41":
        raise ImportError("UnityPy_1.zip không đúng bản đã gửi")
    tt = tf.TemporaryDirectory(prefix="plok_")
    rt = PT(tt.name).resolve()
    with zf.ZipFile(zp) as ar:
        ar.extractall(rt)
    for n in list(sys.modules):
        if n == "UnityPy" or n.startswith("UnityPy."):
            del sys.modules[n]
    cm()
    sys.path.insert(0, str(rt))
    import atexit as ax
    ax.register(tt.cleanup)
    return tt, rt


t0, rt = ux()


def vu(_rt):
    if _rt is None:
        return
    for n, m in tuple(sys.modules.items()):
        if n != "UnityPy" and not n.startswith("UnityPy."):
            continue
        p = getattr(m, "__file__", None)
        if p:
            PT(p).resolve().relative_to(_rt)


def kt():
    k = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
    p = bytes.fromhex("00112233445566778899aabbccddeeff")
    if ab(p, k).hex() != "69c4e0d86a7b0430d8cdb78070b4c55a":
        raise RuntimeError("AES lỗi")
    k = bytes.fromhex("0123456789abcdeffedcba9876543210")
    if sx(k, sk(k)).hex() != "681edf34d206965e86b3e94f536e4246":
        raise RuntimeError("SM4 lỗi")


kt()

ak = b"\xE3\x05\x62\x14\xD6\x0A\x20\x25\x36\x96\x1B\x07\x74\xDC\x24\x02"
ai = b"\x1D\x6E\xEB\x4C\x86\xA9\x45\x44\x45\x72\x12\x21\x2B\x43\x25\x2F"
iv = b"\x79\x7B\xCD\x5D\x7D\x7B\xB1\x11\x43\xD0\x0D\x71\x3C\xDA\xA8\x08"


def z0(fh):
    b = bytearray()
    while len(b) <= 512:
        c = fh.read(1)
        if not c:
            raise ValueError("Header thiếu")
        if c == b"\0":
            return b.decode("utf-8")
        b += c
    raise ValueError("Header lỗi")


def vt(s):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", s or "")
    if not m:
        raise ValueError("Unity version lỗi")
    return tuple(map(int, m.groups()))


def fg(s, n):
    _, AF, AO, _, _ = _upy()
    v = vt(s)
    o = v < (2020,) or v[0] == 2020 and v < (2020, 3, 34) or v[0] == 2021 and v < (2021, 3, 2) or v[0] == 2022 and v < (2022, 1, 1)
    return AO(n) if o else AF(n)


def hb(b):
    f = io.BytesIO(b)
    if z0(f) != "UnityFS":
        raise ValueError("Không phải UnityFS")
    v = int.from_bytes(f.read(4), "big")
    z0(f)
    e = z0(f)
    h = f.tell()
    x = f.read(16)
    n = int.from_bytes(f.read(4), "big")
    g = fg(e, n)
    p = f.tell()
    if v >= 7:
        p = (p + 15) & ~15
    _, AF, _, _, _ = _upy()
    a = bool(g & g.UsesAssetBundleEncryption)
    if a:
        y = x[7::-1] + x[8:12][::-1] + x[12:16][::-1]
        d = AC(ak, ai).decrypt(y)
        s = int.from_bytes(d[:8], "little")
        c = int.from_bytes(d[8:12], "little")
        u = int.from_bytes(d[12:16], "little")
    else:
        s = int.from_bytes(x[:8], "big")
        c = int.from_bytes(x[8:12], "big")
        u = int.from_bytes(x[12:16], "big")
    if not 0 < s <= len(b) or not 0 < c <= s or not 0 < u:
        raise ValueError("Header size lỗi")
    ae = bool(g & g.BlocksInfoAtTheEnd)
    pd = isinstance(g, AF) and bool(g & AF.BlockInfoNeedPaddingAtStart)
    if ae:
        o = s - c
        q = (p + 15) & ~15 if pd else p
        d = o - q
    else:
        o = p
        q = o + c
        if pd:
            q = (q + 15) & ~15
        d = s - q
    if o < p or q < p or d < 0 or o + c > s or q + d > s:
        raise ValueError("Vị trí bundle lỗi")
    return {"g": g, "n": n, "e": e, "h": h, "o": o, "c": c, "u": u, "s": s, "a": a, "d": d, "b": b[o:o + c]}


def dz(b, u, f):
    _, _, _, _, CH = _upy()
    z = f & 0x3F
    if z == 0:
        d = b
    elif z == 1:
        d = CH.decompress_lzma(b)
    elif z in (2, 3):
        d = CH.decompress_lz4(b, u)
    else:
        raise ValueError(f"Nén {z} không hỗ trợ")
    if len(d) != u:
        raise ValueError("BlocksInfo size lỗi")
    return d


def gs(b, p, n, sg=False):
    return int.from_bytes(b[p:p + n], "big", signed=sg), p + n


def ps(b, d, a):
    od = (1, 2, 0) if a else (2, 1, 0)
    ee = None
    for m in od:
        try:
            p = 16
            c, p = gs(b, p, 4, True)
            if not 0 < c <= 4096:
                raise ValueError("block count")
            z = 0
            for _ in range(c):
                if m == 1:
                    f, p = gs(b, p, 2)
                    t, p = gs(b, p, 2)
                    x, p = gs(b, p, 4)
                    u, p = gs(b, p, 4)
                elif m == 2:
                    u, p = gs(b, p, 4)
                    x, p = gs(b, p, 4)
                    f, p = gs(b, p, 2)
                    t, p = gs(b, p, 2)
                else:
                    u, p = gs(b, p, 4)
                    x, p = gs(b, p, 4)
                    f, p = gs(b, p, 2)
                    t = 0
                if t or x > 0x40000000 or u > 0x40000000:
                    raise ValueError("block")
                z += x
            c, p = gs(b, p, 4, True)
            if not 0 < c <= 4096:
                raise ValueError("node count")
            for _ in range(c):
                a0, p = gs(b, p, 8, True)
                a1, p = gs(b, p, 8, True)
                f, p = gs(b, p, 4)
                e = b.find(b"\0", p)
                if e < 0 or e - p > 512:
                    raise ValueError("path")
                b[p:e].decode("utf-8")
                p = e + 1
            if p != len(b) or z != d:
                raise ValueError("layout")
            return
        except Exception as ex:
            ee = ex
    raise ValueError(f"BlocksInfo lỗi: {ee}")


def sm(b, dc=False):
    n = len(b) // 16 * 16
    k = S4(iv)
    x = k.decrypt(b[:n], initial=bytearray(iv)) if dc else k.encrypt(b[:n], initial=bytearray(iv))
    return x + b[n:]


def bi(b, m):
    x = sm(m["b"], True) if m["a"] else m["b"]
    d = dz(x, m["u"], m["n"])
    ps(d, m["d"], m["a"])
    return x


def hd(s, c, u):
    p = s.to_bytes(8, "little") + c.to_bytes(4, "little") + u.to_bytes(4, "little")
    e = AC(ak, ai).encrypt(p)
    return e[7::-1] + e[8:12][::-1] + e[12:16][::-1]


def vl(b):
    up, _, _, BF, _ = _upy()
    e = up.load(io.BytesIO(b))
    vu(rt)
    f = getattr(e, "file", None)
    if not isinstance(f, BF) or not f.files:
        raise ValueError("UnityPy không load được")


def dc(b):
    m = hb(b)
    if not m["a"]:
        raise ValueError("File chưa có Plok")
    x = bi(b, m)
    o = bytearray(b)
    o[m["o"]:m["o"] + m["c"]] = x
    n = int(m["g"]) & ~int(m["g"].UsesAssetBundleEncryption)
    o[m["h"]:m["h"] + 16] = m["s"].to_bytes(8, "big") + m["c"].to_bytes(4, "big") + m["u"].to_bytes(4, "big")
    o[m["h"] + 16:m["h"] + 20] = n.to_bytes(4, "big")
    q = bytes(o)
    bi(q, hb(q))
    vl(q)
    return q


def ec(b):
    m = hb(b)
    if m["a"]:
        raise ValueError("Plok đã nằm trong file")
    x = bi(b, m)
    o = bytearray(b)
    o[m["o"]:m["o"] + m["c"]] = sm(x)
    n = int(m["g"]) | int(m["g"].UsesAssetBundleEncryption)
    o[m["h"]:m["h"] + 16] = hd(m["s"], m["c"], m["u"])
    o[m["h"] + 16:m["h"] + 20] = n.to_bytes(4, "big")
    q = bytes(o)
    bi(q, hb(q))
    return q


def ck(b, m):
    try:
        x = dc(b) if m == 1 else ec(b)
        if m == 1 and ec(x) != b:
            raise ValueError("Vòng Plok không khớp")
        if m == 2 and dc(x) != b:
            raise ValueError("Vòng Plok không khớp")
        return x
    except Exception:
        return None


def is_plok_bundle(path):
    """True neu file la UnityFS va da mang Plok (co UsesAssetBundleEncryption)."""
    try:
        data = PT(path).read_bytes()
        if not data.startswith(b"UnityFS\0"):
            return False
        return hb(data)["a"]
    except Exception:
        return False


def encrypt_bundle(in_path, out_path):
    """Ma hoa Plok: doc -> ec() -> verify round-trip dc() == goc -> ghi."""
    b = PT(in_path).read_bytes()
    q = ck(b, 2)
    if q is None:
        raise ValueError("Ma hoa Plok that bai (file khong phu hop hoac verify loi)")
    PT(out_path).parent.mkdir(parents=True, exist_ok=True)
    t = PT(out_path).with_name(PT(out_path).name + ".tmp")
    t.write_bytes(q)
    os.replace(t, out_path)
    return {"out_size": len(q)}


def decrypt_bundle(in_path, out_path):
    """Giai ma Plok: doc -> dc() -> verify round-trip ec() == goc -> ghi."""
    b = PT(in_path).read_bytes()
    q = ck(b, 1)
    if q is None:
        raise ValueError("Giai ma Plok that bai (file chua co Plok hoac verify loi)")
    PT(out_path).parent.mkdir(parents=True, exist_ok=True)
    t = PT(out_path).with_name(PT(out_path).name + ".tmp")
    t.write_bytes(q)
    os.replace(t, out_path)
    return {"out_size": len(q)}
