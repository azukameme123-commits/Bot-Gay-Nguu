import struct
import json
import os

def B2Js(blocks_data):
    offset = 140
    blocks = []
    def rv(fmt, size):
        nonlocal offset
        value = struct.unpack_from(fmt, blocks_data, offset)[0]
        offset += size
        return value
    def rvb():
        return rv("<B", 1) == 1
    def S(): return rv("<I", 4)
    def S2(): return rv("<H", 2)
    def S8(): return rv("<Q", 8)
    def I(): return rv("<i", 4)
    def I2(): return rv("<h", 2)
    def I8(): return rv("<q", 8)
    def B1(): return rv("<B", 1)
    def B2(): return rvb()
    
    def Str():
        nonlocal offset
        length = S()
        raw_bytes = blocks_data[offset:offset + length]
        offset += length
        return raw_bytes.decode("utf-8", errors="replace").strip("\x00")



    while offset < len(blocks_data):
        block = {}
        try:
            blockinfo = S()
            block['ConfigID'] = S()
            block['bMoveType'] = B1()
            block['Name'] = Str()
            block['MoveSpeed'] = I()
            block['Acceleration'] = I()
            block['bIsModifyTranslation'] = B1()
            block['ModifyTranslation'] = []
            for _ in range(1):
                vl = {
                    "X": I2(),
                    "Y": I2(),
                    "Z": I2()
                }
                block['ModifyTranslation'].append(vl)
            block['bIsModifyDirection'] = B1()
            block['bModifyDirType'] = B1()
            block['bIsMoveRotate'] = B1()
            block['bHitPointType'] = B1()
            block['bIsIgnoreHeight'] = B1()
            block['bIsLockY'] = B1()
            block['bIsIgnoreCharCollisionSize'] = B1()
            block['bIsDelayLeave'] = B1()
            block['BindPosOffset'] = []
            for _ in range(1):
                vl = {
                    "X": I2(),
                    "Y": I2(),
                    "Z": I2()
                }
                block['BindPosOffset'].append(vl)
            block['BindRotOffset'] = []
            for _ in range(1):
                vl = {
                    "X": I2(),
                    "Y": I2(),
                    "Z": I2()
                }
                block['BindRotOffset'].append(vl)
            block['Scale'] = []
            for _ in range(1):
                vl = {
                    "X": I2(),
                    "Y": I2(),
                    "Z": I2()
                }
                block['Scale'].append(vl)
            block['PrefabPath'] = Str()


            
            blocks.append(block)
        except ValueError as e:
            print(f"Error reading block at offset {offset}: {e}")
            break

    return json.dumps(blocks, ensure_ascii=False, indent=4)

    



import hashlib


def JstoB(json_data, binary_file):
    blocks = json.loads(json_data)
    binary_data = bytearray()
    header = bytearray()
    header.extend(b'MSES\x07\x00\x00\x00')
    Blast = 0
    total_blocks = len(blocks)
    header.extend(struct.pack("<I", Blast))
    header.extend(struct.pack("<I", total_blocks))
    header.extend(b'\x61' * 32)
    header.extend(b'\x00' * 16 + b'UTF-8' + b'\x00' * 23)
    header.extend(b'\x00' * (140 - len(header)))
    binary_data.extend(header)

    def U(fmt, value):
        nonlocal block_data
        block_data.extend(struct.pack(fmt, value))
    def S1(value):
        nonlocal block_data
        block_data.extend(pack_string(value))
    for block in blocks:
        block_data = bytearray()
                
        U("<I", block.get('ConfigID', 0))
        block_data.append(block.get('bMoveType', 0))
        S1(block.get('Name', ""))
        U("<i", block.get('MoveSpeed', 0))
        U("<i", block.get('Acceleration', 0))
        block_data.append(block.get('bIsModifyTranslation', 0))
        for effect in block['ModifyTranslation']:
            U("<h", effect["X"])
            U("<h", effect["Y"])
            U("<h", effect["Z"])
        block_data.append(block.get('bIsModifyDirection', 0))
        block_data.append(block.get('bModifyDirType', 0))
        block_data.append(block.get('bIsMoveRotate', 0))
        block_data.append(block.get('bHitPointType', 0))
        block_data.append(block.get('bIsIgnoreHeight', 0))
        block_data.append(block.get('bIsLockY', 0))
        block_data.append(block.get('bIsIgnoreCharCollisionSize', 0))
        block_data.append(block.get('bIsDelayLeave', 0))
        for effect in block['BindPosOffset']:
            U("<h", effect["X"])
            U("<h", effect["Y"])
            U("<h", effect["Z"])
        for effect in block['BindRotOffset']:
            U("<h", effect["X"])
            U("<h", effect["Y"])
            U("<h", effect["Z"])
        for effect in block['Scale']:
            U("<h", effect["X"])
            U("<h", effect["Y"])
            U("<h", effect["Z"])
        S1(block.get('PrefabPath', ""))





        Blen = len(block_data)
        final_block = struct.pack("<I", Blen) + block_data
        binary_data.extend(final_block)
        Bflast = Blen
 

    Blast = Bflast + 4
    binary_data[8:12] = struct.pack("<I", Blast)
    md5_hash = hashlib.md5(binary_data[140:]).hexdigest().encode('utf-8')
    binary_data[96:96 + len(md5_hash)] = md5_hash
    binary_data[140 - 12:140] = b'\x00\x00\x00\x00\x8c\x00\x00\x00\x00\x00\x00\x00'

    with open(binary_file, "wb") as bf:
        bf.write(binary_data)


def pack_string(value):
    encoded = value.encode('utf-8') + b'\x00'
    length = len(encoded)
    return struct.pack("<I", length) + encoded

def LitebulletJson(filepath, mode):
    directory = os.path.dirname(filepath)
    if mode == 1:
        with open(filepath, "rb") as f:
            json_data = B2Js(f.read())
        with open(filepath, "w", encoding="utf-8") as json_file:
            json_file.write(json_data)
    elif mode == 2:
        with open(filepath, "r", encoding="utf-8") as json_file:
            json_data = json_file.read()
        JstoB(json_data, filepath)