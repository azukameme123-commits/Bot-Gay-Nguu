import sys
import subprocess

def install_and_import(package, import_name=None):
    try:
        if import_name:
            __import__(import_name)
        else:
            __import__(package)
    except ImportError:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--no-cache-dir", package
        ])
        if import_name:
            __import__(import_name)
        else:
            __import__(package)

install_and_import("pycryptodome", "Crypto")
install_and_import("pyzstd")

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os
import pyzstd
import random
from concurrent.futures import ThreadPoolExecutor

import os
import pyzstd

def Zstd(ZSTD_DICT, path):

    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                Zstd(ZSTD_DICT, file_path)
        return

    if not os.path.isfile(path):
        return

    try:
        with open(path, "rb") as f:
            data = f.read()

        is_zstd = data.startswith(b"\x28\xb5\x2f\xfd")

        if is_zstd:
            pos = data.find(b"\x28\xb5\x2f\xfd")
            if pos != -1:
                data = data[pos:]

            try:
                output = pyzstd.decompress(data, zstd_dict=ZSTD_DICT)
            except:
                print(f"[DECOMPRESS FAIL] {path}")
                return

        else:
            try:
                compressed = pyzstd.compress(data)
            except Exception as e:
                print(f"[COMPRESS FAIL] {path}: {path} | {e}")
                return

            header = b"\x22\x4a\x00\xef"
            size = len(data).to_bytes(4, "little")

            output = header + size + compressed

        with open(path, "wb") as f:
            f.write(output)

    except Exception as e:
        print(f"[ERROR] {path}: {e}")
    
def giai(strin, ZSTD_DICT):
    posdecompress = strin.find(b"\x28\xb5\x2f\xfd")
    if posdecompress != -1:
        strin = strin[posdecompress:]
        try:
            return pyzstd.decompress(strin, zstd_dict=ZSTD_DICT)
        except:
            return None
    return None
    
MAGIC = bytes.fromhex("22 4A 67")
IV = b"\x00" * 16

def _key(name: str) -> bytes:
    h = 0
    for ch in name:
        c = ord(ch)
        if 97 <= c <= 122:
            c -= 32
        h = ((h * 31) + c) & 0xFFFFFFFF

    k = bytearray(bytes.fromhex(
        "99 64 b1 b0 6b 03 8d 7f b7 7d b6 a7 54 90 8b 73"
    ))

    for i in range(len(k)):
        k[i] ^= (h >> ((i & 3) * 8)) & 0xFF

    return bytes(k)


def _encrypt_file(in_path):
    with open(in_path, "rb") as f:
        pt = f.read()

    if pt.startswith(MAGIC):
        return

    name = os.path.splitext(os.path.basename(in_path))[0]
    key = _key(name)

    cipher = AES.new(key, AES.MODE_CBC, IV)
    ct = cipher.encrypt(pad(pt, AES.block_size))

    hdr = (0).to_bytes(4, "little") + len(pt).to_bytes(4, "little")

    with open(in_path, "wb") as f:
        f.write(MAGIC + hdr[3:] + ct)


def AesJg(path):
    if os.path.isfile(path):
        _encrypt_file(path)
        return

    if not os.path.isdir(path):
        return

    for file in os.listdir(path):
        full = os.path.join(path, file)
        if os.path.isfile(full) and file.endswith((".bytes", ".xml")):
            _encrypt_file(full)
            
ZSTD_FLAG = b"\xef"

def encrypt_file(ZSTD_DICT, input_path):
    name_only, ext = os.path.splitext(os.path.basename(input_path))
    try:
        with open(input_path, "rb") as f:
            original_data = f.read()

        if original_data[:3] == MAGIC:
            return

        if ZSTD_DICT is not None:
            compressed = pyzstd.compress(original_data, ZSTD_LEVEL, ZSTD_DICT)
        else:
            compressed = pyzstd.compress(original_data, ZSTD_LEVEL)

        key = _key(name_only)
        cipher = AES.new(key, AES.MODE_CBC, IV)
        ct = cipher.encrypt(pad(compressed, AES.block_size))
        header = MAGIC + ZSTD_FLAG + len(original_data).to_bytes(4, "little")

        with open(input_path, "wb") as f:
            f.write(header + ct)

    except Exception as e:
        pass

def Zstd_Aes(ZSTD_DICT, path):
    files = []
    if os.path.isdir(path):
        for f in os.listdir(path):
            if f.endswith((".bytes", ".xml")):
                files.append(os.path.join(path, f))
    elif os.path.isfile(path):
        files.append(path)

    for f in files:
        encrypt_file(ZSTD_DICT, f)
        
def No_Enc(ZSTD_DICT, path):
    pass
