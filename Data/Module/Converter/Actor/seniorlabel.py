import struct
import json
import os

HEADER_SIZE = 140
COUNT_OFFSET = 0x0C

FIXED_HEADER_HEX = ("4D5345530700000045000000060000006161616161616161616161616161616161616161616161616161616161616161000000000000000000000000000000005554462D380000000000000000000000000000000000000000000000000000003636373965353133363065653235633833386135656537346166393661333634000000008C00000000000000")

def bytes_to_json(path):
    with open(path, "rb") as f:
        data = f.read()

    block_count = struct.unpack_from("<I", data, COUNT_OFFSET)[0]

    offset = HEADER_SIZE
    result = []

    for i in range(block_count):
        base = offset

        block_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        skin_id = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        label_len = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        label_bytes = data[offset:offset + label_len]
        label = label_bytes.rstrip(b"\x00").decode("utf-8", errors="ignore")
        offset += label_len

        flag = struct.unpack_from("<I", data, offset)[0]
        unk1 = struct.unpack_from("<I", data, offset + 4)[0]
        enable = struct.unpack_from("<I", data, offset + 16)[0]

        result.append({
            "ID": skin_id,
            "Label": label,
            "Flag": flag,
            "Unk1": unk1,
            "Enable": enable
        })

        offset = base + 4 + block_len

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def json_to_bytes(path):
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)

    header = bytearray.fromhex(FIXED_HEADER_HEX)

    struct.pack_into("<I", header, COUNT_OFFSET, len(items))

    binary_data = bytearray()
    binary_data.extend(header)

    for e in items:
        label_bytes = e["Label"].encode("utf-8") + b"\x00"
        label_len = len(label_bytes)

        block_len = 4 + 4 + label_len + 20

        binary_data.extend(struct.pack("<I", block_len))
        binary_data.extend(struct.pack("<I", int(e["ID"])))
        binary_data.extend(struct.pack("<I", label_len))
        binary_data.extend(label_bytes)

        binary_data.extend(struct.pack("<I", int(e["Flag"])))
        binary_data.extend(struct.pack("<I", int(e["Unk1"])))
        binary_data.extend(struct.pack("<I", 0))
        binary_data.extend(struct.pack("<I", 0))
        binary_data.extend(struct.pack("<I", int(e["Enable"])))

    with open(path, "wb") as f:
        f.write(binary_data)


def SeniorLabelJson(filepath, mode):
    if mode == 1:
        bytes_to_json(filepath)
    elif mode == 2:
        json_to_bytes(filepath)