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



    def I():
        nonlocal offset
        value = struct.unpack_from("<i", blocks_data, offset)[0]
        offset += 4
        return value
    def I2():
        nonlocal offset
        value = struct.unpack_from("<h", blocks_data, offset)[0]
        offset += 2
        return value
    def I8():
        nonlocal offset
        value = struct.unpack_from("<q", blocks_data, offset)[0]
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
            block['ID'] = S()
            block['HeadDesc'] = Str()
            block['HeadAccess'] = Str()
            block['HeadIcon'] = Str()
            block['bHeadType'] = B1()
            block['ShowStartTime'] = Str()
            block['ShowEndTime'] = Str()
            block['ShowStartGen'] = S()
            block['ShowEndGen'] = S()
            block['CouponsBuy'] = S()
            block['PVPCoinBuy'] = S()
            block['GuildCoinBuy'] = S()
            block['DiamondBuy'] = S()
            block['bIsBuyMixPay'] = B2()
            block['bSortWeight'] = B1()
            block['ReturnDiamond'] = S()
            block['bAutoUnlock'] = B2()
            block['HeadFXPath'] = Str()
            block['CDNIcon'] = Str()
            block['Prefix'] = Str()
            block['PrefixOnTime'] = S8()
            block['PrefixOffTime'] = S8()
            block['bIsInAB'] = B2()
            block['bIsShowInMgr'] = B2()


            
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
        
        
        U("<I", block.get('ID', 0))
        S1(block.get('HeadDesc', ""))
        S1(block.get('HeadAccess', ""))
        S1(block.get('HeadIcon', ""))
        block_data.append(block.get('bHeadType', 0))
        S1(block.get('ShowStartTime', ""))
        S1(block.get('ShowEndTime', ""))
        U("<I", block.get('ShowStartGen', 0))
        U("<I", block.get('ShowEndGen', 0))
        U("<I", block.get('CouponsBuy', 0))
        U("<I", block.get('PVPCoinBuy', 0))
        U("<I", block.get('GuildCoinBuy', 0))
        U("<I", block.get('DiamondBuy', 0))
        block_data.append(1 if block.get('bIsBuyMixPay', False) else 0)
        block_data.append(block.get('bSortWeight', 0))
        U("<I", block.get('ReturnDiamond', 0))
        block_data.append(1 if block.get('bAutoUnlock', False) else 0)
        S1(block.get('HeadFXPath', ""))
        S1(block.get('CDNIcon', ""))
        S1(block.get('Prefix', ""))
        U("<Q", block.get('PrefixOnTime', 0))
        U("<Q", block.get('PrefixOffTime', 0))
        block_data.append(1 if block.get('bIsInAB', False) else 0)
        block_data.append(1 if block.get('bIsShowInMgr', False) else 0)



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




def HeadImageJson(filepath, mode):
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
        