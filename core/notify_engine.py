# -*- coding: utf-8 -*-
"""
Notify (thong bao ha) engine — SHADOW INSERT (dung chuan Dn da audit).

Sau khi audit byte-level file Dn (thong bao ha da xac nhan hoat dong):
  * ResBillboardSkinCfg.bytes      : KHONG DUNG (identical Goc).
  * ResKillBillboardCfg.bytes      : KHONG DUNG (identical Goc).
  * ResBillboardCfg.bytes          : *only* file bi mod.
  * ResSkinExclusiveBattleEffectCfg.bytes : KHONG DUNG (copy nguyen).

Ky thuat mod (xac nhan bang so sanh Goc vs Dn tren id=0x42):
  Cach cu (zero-out field): SAI — game van doc duoc id that.
  Cach dung ("shadow insert"):
    1. Xac dinh record goc cua id=X trong ResBillboardCfg.bytes.
       Record co dang [len:u32][payload:len bytes], voi 4 byte dau cua
       payload = id LE (kich thuoc bao gom len+4 byte).
    2. Nhan doi (clone) NGUYEN block record do (len+4 byte tinh ca prefix).
    3. Trong ban copy, chi doi 4 byte id (bytes 4..7 ke tu prefix, tuc
       bytes 0..3 cua payload) thanh 00 00 00 00. Cac field khac (skinResID,
       cac cot khac, string...) giu NGUYEN xi — ke ca reference toi id goc
       ben trong record.
    4. Chen block clone id=0 nay NGAY TRUOC record goc (khong phai sau,
       khong phai cuoi file, khong xoa gi).
    5. Kich thuoc file tang dung len+4 byte cho moi id mod. KHONG cap
       nhat recordCount trong header (loader doc het stream/toi null,
       khong kiem so record khop).
  Co che phia game: khi loader duyet table, record id=0 voi payload tro
  toi cung skinRes duoc doc TRUOC -> "chiem slot" va lam record that
  (id=X) bi vo hieu hoa/ghi de trong dictionary theo thu tu parse, nhung
  resource asset thuc (skinResID) van duoc nap. Do do billboard hien thi
  nhung logic kill/lock/check theo id khong match -> mod skin qua mat
  kiem tra id.

resolve skin_id -> billboard_id: doc ResBillboardSkinCfg.bytes,
  pattern = 0C 00 00 00 | <bb_id 4B LE> | 01 00 00 00 | <skin_id 4B LE>
  -> tra bb_id (4B LE) de dung lam TARGET_ID cho shadow insert.
"""
import os
import re
import shutil
import struct
import tempfile


# Ten 4 file (giu nguyen de tuong thich pipeline)
SKIN_CFG      = 'ResBillboardSkinCfg.bytes'
BILLBOARD_CFG = 'ResBillboardCfg.bytes'
KILL_CFG      = 'ResKillBillboardCfg.bytes'
EXCLUSIVE_CFG = 'ResSkinExclusiveBattleEffectCfg.bytes'
ALL_FILES = (SKIN_CFG, BILLBOARD_CFG, KILL_CFG, EXCLUSIVE_CFG)

# Record area cua MSES container bat dau tai offset 0x8C
_RECORD_START = 0x8C


# ------------------------------------------------------------- I/O helpers
def _read(folder, name):
    with open(os.path.join(folder, name), 'rb') as f:
        return f.read()


def _write(folder, name, data):
    with open(os.path.join(folder, name), 'wb') as f:
        f.write(data)


# ------------------------------------------------------------- STEP 1: resolve
def _iter_skin_cfg_records(data):
    """Duyet moi record [len:u32][payload] trong vung record (tu offset 0x8C).

    Generator tra ve (offset, payload) — KHONG gia dinh do dai record,
    khong gia dinh co bao nhieu field ben trong => dung duoc voi moi
    format record (12B, 16B, chuoi string, ...), mien la van theo kieu
    length-prefix cua MSES container.
    """
    i = _RECORD_START
    n = len(data)
    while i + 8 <= n:
        ln = struct.unpack('<I', data[i:i + 4])[0]
        # Guard: len hop le (payload it nhat 8 byte: flag+skin_id hoac
        # bb_id+skin_id; toi da 512B de tranh doc bay)
        if ln < 8 or ln > 512 or i + 4 + ln > n:
            break
        yield i, data[i + 4:i + 4 + ln]
        i += 4 + ln


def extract_billboard_id(work_folder, skin_id):
    """Doc ResBillboardSkinCfg.bytes, tra ve bb_id (bytes 4B LE) hoac None.

    KHONG phu thuoc format mau. Chien luoc 2 tang:
      Tang 1 (parser): duyet tung record [len][payload], tim skin_id (4B LE)
        o bat ky vi tri nao trong payload; khi thay, bb_id = dword NGAY TRUOC
        do (bo qua dword flag = 1 neu co). Ho tro ca record 12B chuan
        (bb_id|01|skin_id) lan cac format khac.
      Tang 2 (fallback): neu parser khong thay (file lech cau truc header),
        quet regex mo: bat ky (4B bb_id) | 01 00 00 00 | skin_id nao trong
        file (khong bat buoc prefix 0C 00 00 00).
    """
    path = os.path.join(work_folder, SKIN_CFG)
    if not os.path.isfile(path):
        return None

    data = _read(work_folder, SKIN_CFG)
    skin_id = int(skin_id)
    skin_hex = struct.pack('<I', skin_id)

    # ---- Tang 1: parser record-based (khong can format mau) ----
    for _off, payload in _iter_skin_cfg_records(data):
        # Tim moi vi tri xuat hien cua skin_id trong payload
        start = 0
        while True:
            p = payload.find(skin_hex, start)
            if p == -1:
                break
            # skin_id phai canh le 4 byte (field dword)
            if p % 4 == 0 and p >= 4:
                # dword ngay truoc skin_id
                prev = struct.unpack('<I', payload[p - 4:p])[0]
                if prev == 1 and p >= 8:
                    # co co flag 01 00 00 00 -> bb_id nam truoc co do
                    return payload[p - 8:p - 4]
                # khong co co -> dword ngay truoc chinh la bb_id
                return payload[p - 4:p]
            start = p + 1

    # ---- Tang 2: fallback regex mo (khong can prefix 0C 00 00 00) ----
    pattern = b'(.{4})\x01\x00\x00\x00' + re.escape(skin_hex)
    m = re.search(pattern, data, re.DOTALL)
    if m:
        return m.group(1)

    # ---- Tang 3: fallback tho — quet tay moi canh 4 byte ----
    pos = data.find(skin_hex, _RECORD_START)
    while pos != -1:
        if (pos - _RECORD_START) % 4 == 0 and pos >= _RECORD_START + 12:
            prev = struct.unpack('<I', data[pos - 4:pos])[0]
            if prev == 1:
                return data[pos - 8:pos - 4]
            return data[pos - 4:pos]
        pos = data.find(skin_hex, pos + 1)
    return None


# ------------------------------------------------------------- STEP 2: shadow insert
def patch_billboard(work_folder, bb_id):
    """Shadow-insert vao ResBillboardCfg.bytes.

    Duyet record area (bat dau tu offset 0x8C):
      moi record = [len:u32 LE][payload:len bytes]
      id record = payload[0:4] doc LE
    Neu id == bb_id (int) -> clone nguyen block (4+len byte), zero 4 byte
    id trong ban copy, chen NGAY TRUOC record goc.

    Chi mod TAT ca record ma id trung bb_id (thuong chi co 1). Sau khi
    chen 1 block, offset duyet cua vong lap nhay qua CA block chen len
    va block goc de tranh mod trung.

    Tra ve so lan chen (0 = MISS).
    """
    path = os.path.join(work_folder, BILLBOARD_CFG)
    if not os.path.isfile(path):
        return 0

    data = bytearray(_read(work_folder, BILLBOARD_CFG))
    size = len(data)
    bb_id_int = struct.unpack('<I', bb_id)[0]

    inserted = 0
    i = _RECORD_START
    # Duyet len list record theo length-prefix
    while i + 8 <= len(data):
        # Doc len prefix
        ln = struct.unpack('<I', bytes(data[i:i+4]))[0]
        # Guard: len phai hop ly, khong vuot qua file, va payload phai
        # du 4 byte cho id
        if ln < 4 or ln > 500 or i + 4 + ln > len(data):
            break

        payload_off = i + 4
        rec_id = struct.unpack('<I', bytes(data[payload_off:payload_off+4]))[0]
        block_size = 4 + ln  # bao gom prefix

        if rec_id == bb_id_int:
            # Clone nguyen block (bao gom len+4 byte prefix)
            block = bytes(data[i:i + block_size])
            # Zero 4 byte id trong ban copy (offset 4..8 trong block)
            clone = block[:4] + b'\x00\x00\x00\x00' + block[8:]
            # Chen block clone TRUOC record goc
            data[i:i] = clone
            inserted += 1
            # Nhay qua clone + record goc de khong mod lai
            i += block_size + block_size
        else:
            i += block_size

    if inserted > 0:
        _write(work_folder, BILLBOARD_CFG, bytes(data))
    return inserted


# ------------------------------------------------------------- STEP 3: kill (KHONG DUNG)
def patch_kill(work_folder, bb_id):
    """KHONG mod KillBillboardCfg — audit da chung minh mod trong Dn
    KHONG dung file nay. Giu ham de tuong thich API cu; luon tra 0.
    """
    return 0


def list_all_billboard_skins(databin_dir):
    """Liet ke TOAN BO (skin_id, bb_id) co trong ResBillboardSkinCfg.bytes.

    Dung de hien thi menu notify ma khong can notify.txt — bat ky skin nao
    co trong file config cua game deu patch duoc, khong theo format mau.
    Tra ve dict {skin_id_str: bb_id_int}.
    """
    out = {}
    path = os.path.join(databin_dir, SKIN_CFG)
    if not os.path.isfile(path):
        return out
    data = _read(databin_dir, SKIN_CFG)
    for _off, payload in _iter_skin_cfg_records(data):
        if len(payload) >= 12:
            bb_id = struct.unpack('<I', payload[0:4])[0]
            skin_id = struct.unpack('<I', payload[8:12])[0]
            if skin_id:
                out[str(skin_id)] = bb_id
    return out


# ------------------------------------------------------------- per-skin pipeline
def build_one_notify(skin_id, databin_src_dir, out_dir_Android, out_dir_ios, log=None):
    """Patch thong bao ha cho 1 skin_id bang shadow insert.

    Tra ve dict:
      {'status': 'NTF', 'billboard_ok': bool, 'kill_ok': bool,
       'bb_id_hex': '42000000', 'billboard_count': n, 'kill_count': 0}
      hoac {'status': 'skip', 'reason': '...'}
    """
    log = log or (lambda *a, **k: None)
    skin_id = int(skin_id)

    if not os.path.isdir(databin_src_dir):
        return {'status': 'skip', 'reason': 'no_databin_dir'}

    # Workspace rieng -> SOURCE files bat bien
    with tempfile.TemporaryDirectory() as work:
        for fn in ALL_FILES:
            src = os.path.join(databin_src_dir, fn)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(work, fn))

        # STEP 1: resolve bb_id tu SkinCfg (khong sua SkinCfg!)
        bb_id = extract_billboard_id(work, skin_id)
        if bb_id is None:
            # ID khong co trong SkinCfg -> copy nguyen ra output, khong sua
            for out_dir in (out_dir_Android, out_dir_ios):
                os.makedirs(out_dir, exist_ok=True)
                for fn in ALL_FILES:
                    src = os.path.join(work, fn)
                    if os.path.isfile(src):
                        shutil.copy2(src, os.path.join(out_dir, fn))
            return {'status': 'skip', 'reason': 'id_not_in_skin_cfg'}

        bb_id_int = struct.unpack('<I', bb_id)[0]
        log('   NTF     skin_id=%d  ->  bb_id=%d (%s)'
            % (skin_id, bb_id_int, bb_id.hex().upper()))

        # STEP 2: shadow insert vao BillboardCfg
        bill_count = patch_billboard(work, bb_id)

        # STEP 3: KillBillboardCfg -> KHONG DUNG (audit da xac nhan).
        # Giu bien de log tuong thich.
        kill_count = 0

        # Ghi ra ca 2 platform (Android va IOS)
        for out_dir in (out_dir_Android, out_dir_ios):
            os.makedirs(out_dir, exist_ok=True)
            for fn in ALL_FILES:
                src = os.path.join(work, fn)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(out_dir, fn))

    log('   NTF     BillboardCfg=%s(x%d shadow-insert)  ·  Kill/Skin=untouched'
        % ('OK' if bill_count else 'MISS', bill_count))

    return {
        'status': 'NTF' if bill_count > 0 else 'skip',
        'bb_id': bb_id,
        'bb_id_hex': bb_id.hex().upper(),
        'billboard_ok': bill_count > 0,
        'kill_ok': True,        # khong can mod -> coi nhu OK
        'billboard_count': bill_count,
        'kill_count': kill_count,
    }


def copy_only(databin_src_dir, out_dir_Android, out_dir_ios):
    """Skin KHONG co trong notify.txt -> chi copy nguyen 4 file ra output."""
    if not os.path.isdir(databin_src_dir):
        return
    for out_dir in (out_dir_Android, out_dir_ios):
        os.makedirs(out_dir, exist_ok=True)
        for fn in ALL_FILES:
            src = os.path.join(databin_src_dir, fn)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(out_dir, fn))


# ------------------------------------------------------------- out path helpers
def huanhua_out_dirs(skin_root):
    """<skin_root>/Android/Resources/1.63.1/databin/client/huanhua/
       <skin_root>/IOS/Resources/1.63.1/databin/client/huanhua/"""
    rel = ['Resources', '1.63.1', 'databin', 'client', 'huanhua']
    return (
        os.path.join(skin_root, 'Android', *rel),
        os.path.join(skin_root, 'IOS', *rel),
    )


# ------------------------------------------------------------- backward-compat shims
extract_target = extract_billboard_id


# ------------------------------------------------------------- CLI test
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('usage: notify_engine.py <databin_dir> <skin_id>')
        sys.exit(1)
    src = sys.argv[1]
    sid = int(sys.argv[2])
    out_a = os.path.join('/tmp/notify_test', 'Android')
    out_i = os.path.join('/tmp/notify_test', 'IOS')
    res = build_one_notify(sid, src, out_a, out_i, log=print)
    print('RESULT:', res)
