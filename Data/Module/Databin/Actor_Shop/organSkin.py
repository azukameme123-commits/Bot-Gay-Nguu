import os
import struct


def _le2bytes_to_int(b):
    if len(b) < 2:
        return b[0] if len(b) == 1 else 0
    return b[0] + (b[1] * 256)


def _int_to_le2hex(val):
    try:
        h = hex(val)
        h_len = len(h)
        if h_len <= 3:
            result = h[2:3].zfill(2) + "00"
        elif h_len == 4:
            result = h[2:4] + "00"
        elif h_len == 5:
            result = h[3:5] + "0" + h[2]
        elif h_len == 6:
            result = h[4:6] + h[2:4]
        else:
            return None
        return bytes.fromhex(result)
    except Exception:
        return None


def hieuungvethan(ID_SKIN, OganSkin):
    ID = ID_SKIN
    with open(OganSkin, "rb") as file:
        Begin = file.read(140)
    if len(Begin) < 12:
        raise ValueError(f"File quá nhỏ, không đọc được header: {OganSkin}")

    CHUNK_SIZE = struct.unpack_from('<I', Begin, 8)[0]
    if CHUNK_SIZE < 8:
        raise ValueError(f"Chunk size không hợp lệ: {CHUNK_SIZE}")

    OZ = struct.pack('<I', CHUNK_SIZE - 4)

    IDN = _int_to_le2hex(int(ID))
    if IDN is None:
        raise ValueError(f"Không thể convert ID_SKIN: {ID}")
        
    ALL_ID = []
    MD = int(ID[0:3] + "00")
    for _ in range(21):
        ALL_ID.append(str(MD))
        MD += 1

    if ID not in ALL_ID:
        raise ValueError(f"ID_SKIN '{ID}' không nằm trong range tạo ra. Kiểm tra lại giá trị ID.")
    ALL_ID.remove(ID)

    for x in range(20):
        IDK = _int_to_le2hex(int(ALL_ID[x]))
        if IDK is None:
            raise ValueError(f"Không thể convert ALL_ID[{x}]: {ALL_ID[x]}")
        ALL_ID[x] = IDK

    with open(OganSkin, "rb") as file:
        file.seek(140)
        All = []
        Max0 = b"\x00\x00"

        while True:
            Read = file.read(CHUNK_SIZE)
            if not Read:
                break
            if len(Read) < CHUNK_SIZE:
                break

            if IDN in Read:
                All.append(Read)

            if len(Read) >= 6:
                try:
                    Max_val = Read[4] + (Read[5] * 256)
                    result = _int_to_le2hex(Max_val)
                    if result is not None:
                        Max0 = result
                except Exception:
                    pass

    if not All:
        raise ValueError(f"Không tìm thấy chunk nào chứa IDN {IDN.hex()} trong file.")

    with open(OganSkin, "ab") as file:
        for i in range(len(ALL_ID)):
            for j in range(len(All)):
                CT = All[j]

                if IDN in CT:
                    CT = CT.replace(IDN, ALL_ID[i])
                elif i > 0:
                    CT = CT.replace(ALL_ID[i - 1], ALL_ID[i])

                new_val = _le2bytes_to_int(Max0) + 1
                CTN = _int_to_le2hex(new_val)
                if CTN is None:
                    CTN = b"\x01\x00"

                old_pattern = OZ + CT[4:6]
                if len(CTN) == 1:
                    CT = CT.replace(old_pattern, OZ + CTN + b"\x00", 1)
                elif len(CTN) == 2:
                    CT = CT.replace(old_pattern, OZ + CTN, 1)

                All[j] = CT
                file.write(CT)
                Max0 = CT[4:6]

    with open(OganSkin, "rb") as file:
        data = file.read()

    data = data.replace(Begin[12:14], Max0, 1)

    with open(OganSkin, "wb") as file:
        file.write(data)
