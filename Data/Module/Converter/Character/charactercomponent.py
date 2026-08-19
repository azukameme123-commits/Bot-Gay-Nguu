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

    def B1():
        nonlocal offset
        value = struct.unpack_from("<B", blocks_data, offset)[0]
        offset += 1
        return value
    def B2():
        nonlocal offset
        value = struct.unpack_from("<B", blocks_data, offset)[0] == 1
        offset += 1
        return value

    def Str():
        nonlocal offset
        length = struct.unpack_from("<I", blocks_data, offset)[0]
        offset += 4
        value = blocks_data[offset : offset + length].decode("utf-8").strip("\x00")
        offset += length
        return value

    while offset < len(blocks_data):
        block = {}
        try:
            blockinfo = S()
            block['ID'] = S()
            
            block['bComponentCfgType'] = B1()
            
            block['Default'] = S() == 1
            block['CharacterComponentType'] = {0: "None", 1: "HairColor", 2: "Head", 3: "Face", 4: "Back", 5: "Decoration", 6: "Weapon", 7: "Suit"}.get(S(), "Unknown")

            block['HeroID'] = S()
            block['DegenerationID'] = S()
            block['EffectLevel'] = S()
            block['IsDone'] = S() == 1
            
            block['bAllowShowWithErrors'] = B2()
            
            block['Name'] = Str()
            block['Desc'] = Str()
            block['ResBackGround'] = Str()
            block['ResTable'] = Str()
            
            block['ContainComponent'] = [value for value in struct.unpack_from("<6I", blocks_data, offset) if value != 0]
            offset += 24

            
            block['SkinFeature'] = []
            for i in range(1, 6):
                icon = Str()
                name = Str()
                if icon or name:
                    block['SkinFeature'].append({"Icon": icon, "Name": name})
                    
            blockiTotalFeature = int(S())
            blockSkinGroupCnt = S()
            block['SkinGroup'] = []
            for _ in range(blockSkinGroupCnt):
                group = []
                for _ in range(6):
                    value = S()
                    if value != 0:
                        group.append(value)
                if group:
                    block['SkinGroup'].append(group)
                str_value = Str()

            block['iQuality'] = int(S())
            blocks.append(block)
        except ValueError as e:
            print(f"Error reading block at offset {offset}: {e}")
            break

    return json.dumps(blocks, indent=4)



import hashlib


def JstoB(json_data, binary_file):
    blocks = json.loads(json_data)
    if not blocks:
        return
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

        U("<I", block.get('ID', 0))
        
        block_data.append(block.get('bComponentCfgType', 0))
        block_data.extend(struct.pack("<I", 1 if block.get('Default', False) else 0))

        block_data.extend(struct.pack("<I", {"None": 0, "HairColor": 1, "Head": 2, "Face": 3, "Back": 4, "Decoration": 5, "Weapon": 6, "Suit": 7}.get(block.get('CharacterComponentType', "None"), 0)))


        U("<I", block.get('HeroID', 0))
        U("<I", block.get('DegenerationID', 0))
        U("<I", block.get('EffectLevel', 0))
        block_data.extend(struct.pack("<I", 1 if block.get('IsDone', False) else 0))
        block_data.append(1 if block.get('bAllowShowWithErrors', False) else 0)
        
        S1(block.get('Name', ""))
        S1(block.get('Desc', ""))
        S1(block.get('ResBackGround', ""))
        S1(block.get('ResTable', ""))
        
        contain = block.get("ContainComponent", [])
        contain = contain[:6]
        for i in range(6):
            block_data.extend(struct.pack("<I", contain[i] if i < len(contain) else 0))

        features = block.get("SkinFeature", [])
        for i in range(5):
            if i < len(features):
                S1(features[i].get("Icon", ""))
                S1(features[i].get("Name", ""))
            else:
                S1("")
                S1("")
                
        block_data.extend(b'\x00' * 4) 
        
        SkinGroup = block.get('SkinGroup', [])
        SkinGroupCnt = len(SkinGroup)
        U("<I", SkinGroupCnt)
        for group in SkinGroup:
            group.extend([0] * (6 - len(group)))
            for value in group[:6]:
                block_data.extend(struct.pack("<I", value))
            block_data.extend(b'\x01\x00\x00\x00\x00')



        U("<I", block.get('iQuality', 0))

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


def CharacterJson(filepath, mode):
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