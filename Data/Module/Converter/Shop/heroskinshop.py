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
        value = blocks_data[offset : offset + length].decode("utf-8", errors="replace").strip("\x00")
        offset += length
        return value

    while offset < len(blocks_data):
        block = {}
        try:
            blockinfo = S()
            block['ID'] = S()
            block['HeroID'] = S()
            block['HeroName'] = Str()
            block['SkinID'] = S()
            block['SkinName'] = Str()
            block['SkinDesc'] = Str()
            block['bIsLimitSkin'] = B2()
            block['LimitQualityPic'] = Str()
            block['LimitLabelPic'] = Str()
            block['LimitLabelPicUrl'] = Str()
            block['bSkinQuality'] = B1()
            block['bGetPathType'] = B1()
            block['GetPath'] = Str()
            
            block['bIsBuyCoupons'] = B2()
            block['BuyCoupons'] = S()
            
            block['bIsBuySkinCoin'] = B2()
            block['BuySkinCoin'] = S()
            
            block['bIsBuyDiamond'] = B2()
            block['BuyDiamond'] = S()
            
            block['bIsBuyMixPay'] = B2()
            block['bIsBuyItem'] = B2()
            block['BuyItemCnt'] = S()
            
            block['bIsPresent'] = B2()
            block['SortId'] = S()
            
            block['bPromotionCnt'] = B1()
            block['PromotionID'] = []
            for i in range(1, 6):
                idp = S()
                if idp:
                    block['PromotionID'].append(idp)

            block['ChgItemCnt'] = S()

            block['OnTimeStr'] = Str()
            block['OffTimeStr'] = Str()

            block['OnTimeGen'] = S()
            block['OffTimeGen'] = S()
            block['ReleaseId'] = S()
            
            block['bShowInShop'] = B2()
            block['bShowInMgr'] = B2()
            block['bRankLimitType'] = B1()
            block['bExchangeCoinType'] = B1()
            block['bRankLimitGrade'] = B1()
            
            block['ExchangeCoinCnt'] = S()
            
            offset += 34

            
            block['ConnectionGift'] = S()
            block['SkinLevel'] = S()
            
            block['bIsDefaultT6'] = B2()
            block['VideoAddress'] = Str()
            block['bIsWorldConceptVideo'] = B2()
            
            block['ShareSkinGroupID'] = S()
            block['VipShareSkinGroupID'] = S()
            blocks.append(block)
        except ValueError as e:
            print(f"Error reading block at offset {offset}: {e}")
            break

    return json.dumps(blocks, indent=4)


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

        U("<I", block.get('ID', 0))
        U("<I", block.get('HeroID', 0))
        S1(block.get('HeroName', ""))
        U("<I", block.get('SkinID', 0))
        S1(block.get('SkinName', ""))
        S1(block.get('SkinDesc', ""))
        block_data.append(1 if block.get('bIsLimitSkin', False) else 0)
        S1(block.get('LimitQualityPic', ""))
        S1(block.get('LimitLabelPic', ""))
        S1(block.get('LimitLabelPicUrl', ""))
        block_data.append(block.get('bSkinQuality', 0))
        block_data.append(block.get('bGetPathType', 0))
        S1(block.get('GetPath', ""))
        
        block_data.append(1 if block.get('bIsBuyCoupons', False) else 0)
        U("<I", block.get('BuyCoupons', 0))
        
        block_data.append(1 if block.get('bIsBuySkinCoin', False) else 0)
        U("<I", block.get('BuySkinCoin', 0))
        
        block_data.append(1 if block.get('bIsBuyDiamond', False) else 0)
        U("<I", block.get('BuyDiamond', 0))
        
        block_data.append(1 if block.get('bIsBuyMixPay', False) else 0)
        block_data.append(1 if block.get('bIsBuyItem', False) else 0)
        U("<I", block.get('BuyItemCnt', 0))
        

        
        block_data.append(1 if block.get('bIsPresent', False) else 0)
        U("<I", block.get('SortId', 0))
        block_data.append(block.get('bPromotionCnt', 0))
        promotion_ids = block.get("PromotionID", [])
        promotion_ids.extend([0] * (5 - len(promotion_ids)))
        for idp in promotion_ids[:5]:
            U("<I", idp)

        block["PromotionID"] = promotion_ids

        U("<I", block.get('ChgItemCnt', 0))
        S1(block.get('OnTimeStr', ""))
        S1(block.get('OffTimeStr', ""))
        
        U("<I", block.get('OnTimeGen', 0))
        U("<I", block.get('OffTimeGen', 0))
        U("<I", block.get('ReleaseId', 0))
        
        block_data.append(1 if block.get('bShowInShop', False) else 0)
        block_data.append(1 if block.get('bShowInMgr', False) else 0)
        block_data.append(block.get('bRankLimitType', 0))
        block_data.append(block.get('bExchangeCoinType', 0))
        block_data.append(block.get('bRankLimitGrade', 0))
        
        U("<I", block.get('ExchangeCoinCnt', 0))

        block_data.extend(b'\x00\x01' + b'\x00' * 32)
        
        U("<I", block.get('ConnectionGift', 0))
        U("<I", block.get('SkinLevel', 0))
        block_data.append(1 if block.get('bIsDefaultT6', False) else 0)
        S1(block.get('VideoAddress', ""))
        block_data.append(1 if block.get('bIsWorldConceptVideo', False) else 0)
        U("<I", block.get('ShareSkinGroupID', 0))
        U("<I", block.get('VipShareSkinGroupID', 0))

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


def HeroSkinShopJson(filepath, mode):
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
        