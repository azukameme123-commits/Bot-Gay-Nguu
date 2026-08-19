import struct
import json
import os

def B2Js(blocks_data):
    offset = 140
    blocks = []
    
    def S():
        nonlocal offset
        value = struct.unpack_from("<I", blocks_data, offset)[0]
        offset += 4
        return value

    def S2():
        nonlocal offset
        value = struct.unpack_from("<H", blocks_data, offset)[0]
        offset += 2
        return value

    def S8():
        nonlocal offset
        value = struct.unpack_from("<Q", blocks_data, offset)[0]
        offset += 8
        return value
        
    def B1():
        nonlocal offset
        value = struct.unpack_from("<B", blocks_data, offset)[0]
        offset += 1
        return value
    def B2():
        return B1() == 1


    def Str():
        nonlocal offset
        length = struct.unpack_from("<I", blocks_data, offset)[0]
        offset += 4
        raw_bytes = blocks_data[offset:offset + length]
        offset += length
        try:
            value = raw_bytes.decode("utf-8").strip("\x00")
        except UnicodeDecodeError:
            value = raw_bytes.decode("utf-8", errors="replace").strip("\x00")
        return value

    while offset < len(blocks_data):
        block = {}
        try:
            blockinfo = S()
            block['CfgID'] = int(S())
            block['DependCfgID'] = int(S())
            
            block['MarkName'] = Str()
            block['MarkDesc'] = Str()
            block['ActionName'] = Str()
            
            block['MarkOverlapRule'] = int(S())
            
            block['bLayerEffect'] = B1()
            
            block['MaxLayer'] = int(S())
            block['OnlyTriggerLayer'] = int(S())
            block['CostLayer'] = int(S())
            block['TriggerLayer'] = int(S())
            block['ImmuneTime'] = int(S())
            block['LastMaxTime'] = int(S())
            block['CDTime'] = int(S())
            block['AddMarkImmuneTime'] = int(S())

            block['bAutoTrigger'] = B2()
            block['EffectMask'] = S()
            block['LayerEffectName'] = []
            for i in range(1, 11):
                efx = Str()
                if efx:
                    block['LayerEffectName'].append(efx)

            block['bAgeImmeExcute'] = B2()
            block['bUseHUDInd'] = B2()
            block['bHUDIndDir'] = B2()
            block['bHUDIndProSlot'] = B1()

            block['HUDIndColor'] = S()
            block['HUDIndProColor'] = S()
            block['IndPriority'] = int(S())
            
            block['bAutoTriggerOnDead'] = B2()

            block['RotateFollowParent'] = int(S())

            block['bSpecialBuffEffect'] = B2()
            block['bInvisibleSelf'] = B2()
            block['bInvisibleEnemy'] = B2()
            block['bInvisibleTeamNotSelf'] = B2()
            block['bDeadPreserve'] = B2()
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
    header.extend(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00UTF-8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
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

        U("<I", block.get('CfgID', 0))
        U("<I", block.get('DependCfgID', 0))
        
        S1(block.get('MarkName', ""))
        S1(block.get('MarkDesc', ""))
        S1(block.get('ActionName', ""))
        
        U("<I", block.get('MarkOverlapRule', 0))

        block_data.append(1 if block.get('bLayerEffect', False) else 0)

        U("<I", block.get('MaxLayer', 0))
        U("<I", block.get('OnlyTriggerLayer', 0))
        U("<I", block.get('CostLayer', 0))
        U("<I", block.get('TriggerLayer', 0))
        U("<I", block.get('ImmuneTime', 0))
        U("<I", block.get('LastMaxTime', 0))
        U("<I", block.get('CDTime', 0))
        U("<I", block.get('AddMarkImmuneTime', 0))
        
        block_data.append(1 if block.get('bAutoTrigger', False) else 0)
        
        U("<I", block.get('EffectMask', 0))
        
        layerefx = block.get("LayerEffectName", [])
        for i in range(10):
            if i < len(layerefx):
                S1(layerefx[i])
            else:
                S1("")
        block_data.append(1 if block.get('bAgeImmeExcute', False) else 0)
        block_data.append(1 if block.get('bUseHUDInd', False) else 0)
        block_data.append(1 if block.get('bHUDIndDir', False) else 0)
        block_data.append(block.get('bHUDIndProSlot', 0))
        # block_data.extend(b'\x00') 
        U("<I", block.get('HUDIndColor', 0))
        U("<I", block.get('HUDIndProColor', 0))
        U("<I", block.get('IndPriority', 0))
        
        block_data.append(1 if block.get('bAutoTriggerOnDead', False) else 0)

        U("<I", block.get('RotateFollowParent', 0))
        
        block_data.append(1 if block.get('bSpecialBuffEffect', False) else 0)
        block_data.append(1 if block.get('bInvisibleSelf', False) else 0)
        block_data.append(1 if block.get('bInvisibleEnemy', False) else 0)
        block_data.append(1 if block.get('bInvisibleTeamNotSelf', False) else 0)
        block_data.append(1 if block.get('bDeadPreserve', False) else 0)

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

def SkillMarkJson(filepath, mode):
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