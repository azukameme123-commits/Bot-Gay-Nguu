# 13-6-2026 13:23:49
import struct,json,os,hashlib
from itertools import dropwhile

def zro(lst):
    return list(reversed(list(dropwhile(lambda x: x == 0, reversed(lst)))))

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
        try:
            block_start = offset
            blockinfo = S()
            block_end = block_start + 4 + blockinfo

            block = {
                'CfgID': I(),
                'SkillFuncType': I(),
                'SkillFuncFreq': I(),
                'MutexCfgID2': I(),
                'MutexCfgID3': I(),
                'bMapSkillCombineUseRuleID': B1(),
                'TriggerRate': I(),
                'CroupID': I(),
                'FirstLifeStealAttenuation': I(),
                'FollowUpLifeStealAttenuation': I(),
                'bHurtFadeType': B1(),
                'NextDeltaFadeRate': I(),
                'NextLowFadeRate': I(),
                'ClearRule': S(),
                'OverlayFadeRate': S(),
                'OverlayRule': S(),
                'OverlayMax': S(),
                'OverlayMaxGrowType': S(),
                'EffectType': S(),
                'EffectSubType': S(),
                'ShowType': S(),
                'FloatTextID': S(),
                'SkillCombineName': Str(),
                'SkillCombineDescTitle': Str(),
                'SkillCombineDesc': Str(),
                'Prefab': Str(),
                'Duration': I(),
                'DurationGrow': I(),
            }

            block = {k: v for k, v in block.items() if v not in (0, "")}

            bSkillFuncInfoCnt = struct.unpack_from("<B", blocks_data, offset)[0]
            offset += 1

            if bSkillFuncInfoCnt > 0:
                block['SkillFuncInfo'] = []
                for _ in range(bSkillFuncInfoCnt):
                    func = {
                        'SkillFuncType': S(),
                        'SkillFuncFreq': S(),
                        'SkillFuncParam': zro([I() for _ in range(13)]),
                        'SkillFuncGroup': zro([I() for _ in range(13)])
                    }
                    block['SkillFuncInfo'].append(func)

            block2 = {
                'SrcType': I(),
                'IconPath': Str(),
                'bIsShowBuff': B2(),
                'bShowBuffPriority': B1(),
                'OverlayBuffID': I(),
                'bGrowthType': B1(),
                'bIsInheritByKiller': B2(),
                'CanSkillCrit': I(),
                'DamageLimit': I(),
                'MonsterDamageLimit': I(),
                'LongRangeReduction': I(),
                'EffectiveTargetType': I(),
                'bIsAssistEffect': B1(),
                'bAgeImmeExcute': B2(),
                'bAgeImmeStop': B2(),
                'bNotGetHate': B2(),
                'ExtraEffectSlotType': I(),
                'ReplaceHudNameType': S(),
                'bIsHideBuffTimerBar': B2(),
                'bStatSlotType': B1(),
                'bDifferentSource': B1(),
                'bNotShowHitEffectLOD3': B2(),
                'bNotShowDmgFloatLOD3': B2(),
                'bTakeEffectCountMax': B1(),
                'bIsRecordTakeEffectCountWhenAddBuff': B2(),
                'ChangeDurationProperty': S2(),
                'ChangeDurationPropertyRate': I(),
                'DurationMax': I(),
                'bNoAffectByTenacity': B2(),
                'TargetMarkerSlotType': I(),
                'bIsUniqueBuff': B2(),
                'bIsHeroBuff': B2(),
                'bNotShowDmgFloat': B1(),
                'BindSkillID': I(),
                'RemoveRuleID': I(),
                'ControlEffectType': I(),
                'bBuffBorderType': B1(),
                'bBuffRelocateByCopyedActor': B2(),
                'CoverCombineCfgID1': I(),
                'CoverCombineCfgID2': I(),
                'CoverCombineCfgID3': I(),
                'bBUsePreCrit': B2(),
                'UnknownI4': I(),
                'UnknownH2': S2(),
                'UnknownB1': B1(),
            }
            block2 = {k: v for k, v in block2.items() if v not in (0, "")}
            block.update(block2)

            offset = block_end
            blocks.append(block)

        except ValueError as e:
            print(f"Error reading block at offset {offset}: {e}")
            break

    return json.dumps(blocks, ensure_ascii=False, indent=4)


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

    Bflast = 0
    for block in blocks:
        block_data = bytearray()

        def U(fmt, value):
            nonlocal block_data
            block_data.extend(struct.pack(fmt, value))
        def S1(value):
            nonlocal block_data
            block_data.extend(pack_string(value))

        U("<i", block.get('CfgID', 0))
        U("<i", block.get('SkillFuncType', 0))
        U("<i", block.get('SkillFuncFreq', 0))
        U("<i", block.get('MutexCfgID2', 0))
        U("<i", block.get('MutexCfgID3', 0))
        block_data.append(block.get('bMapSkillCombineUseRuleID', 0))
        U("<i", block.get('TriggerRate', 0))
        U("<i", block.get('CroupID', 0))
        U("<i", block.get('FirstLifeStealAttenuation', 0))
        U("<i", block.get('FollowUpLifeStealAttenuation', 0))
        block_data.append(block.get('bHurtFadeType', 0))
        U("<i", block.get('NextDeltaFadeRate', 0))
        U("<i", block.get('NextLowFadeRate', 0))
        U("<I", block.get('ClearRule', 0))
        U("<I", block.get('OverlayFadeRate', 0))
        U("<I", block.get('OverlayRule', 0))
        U("<I", block.get('OverlayMax', 0))
        U("<I", block.get('OverlayMaxGrowType', 0))
        U("<I", block.get('EffectType', 0))
        U("<I", block.get('EffectSubType', 0))
        U("<I", block.get('ShowType', 0))
        U("<I", block.get('FloatTextID', 0))
        S1(block.get('SkillCombineName', ""))
        S1(block.get('SkillCombineDescTitle', ""))
        S1(block.get('SkillCombineDesc', ""))
        S1(block.get('Prefab', ""))
        U("<i", block.get('Duration', 0))
        U("<i", block.get('DurationGrow', 0))

        func_count = len(block.get('SkillFuncInfo', []))
        block_data.append(func_count)

        for skill_func in block.get('SkillFuncInfo', []):
            U("<I", skill_func['SkillFuncType'])
            U("<I", skill_func['SkillFuncFreq'])

            skill_func_param = skill_func.get('SkillFuncParam', [])
            skill_func_param.extend([0] * (13 - len(skill_func_param)))
            for param in skill_func_param[:13]:
                block_data.extend(struct.pack("<i", param))

            skill_func_group = skill_func.get('SkillFuncGroup', [])
            skill_func_group.extend([0] * (13 - len(skill_func_group)))
            for group in skill_func_group[:13]:
                block_data.extend(struct.pack("<i", group))

        U("<i", block.get('SrcType', 0))
        S1(block.get('IconPath', ""))
        block_data.append(1 if block.get('bIsShowBuff', False) else 0)
        block_data.append(block.get('bShowBuffPriority', 0))
        U("<i", block.get('OverlayBuffID', 0))
        block_data.append(block.get('bGrowthType', 0))
        block_data.append(1 if block.get('bIsInheritByKiller', False) else 0)
        U("<i", block.get('CanSkillCrit', 0))
        U("<i", block.get('DamageLimit', 0))
        U("<i", block.get('MonsterDamageLimit', 0))
        U("<i", block.get('LongRangeReduction', 0))
        U("<i", block.get('EffectiveTargetType', 0))
        block_data.append(block.get('bIsAssistEffect', 0))
        block_data.append(1 if block.get('bAgeImmeExcute', False) else 0)
        block_data.append(1 if block.get('bAgeImmeStop', False) else 0)
        block_data.append(1 if block.get('bNotGetHate', False) else 0)
        U("<i", block.get('ExtraEffectSlotType', 0))
        U("<I", block.get('ReplaceHudNameType', 0))
        block_data.append(1 if block.get('bIsHideBuffTimerBar', False) else 0)
        block_data.append(block.get('bStatSlotType', 0))
        block_data.append(block.get('bDifferentSource', 0))
        block_data.append(1 if block.get('bNotShowHitEffectLOD3', False) else 0)
        block_data.append(1 if block.get('bNotShowDmgFloatLOD3', False) else 0)
        block_data.append(block.get('bTakeEffectCountMax', 0))
        block_data.append(1 if block.get('bIsRecordTakeEffectCountWhenAddBuff', False) else 0)
        U("<h", block.get('ChangeDurationProperty', 0))
        U("<i", block.get('ChangeDurationPropertyRate', 0))
        U("<i", block.get('DurationMax', 0))
        block_data.append(1 if block.get('bNoAffectByTenacity', False) else 0)
        U("<i", block.get('TargetMarkerSlotType', 0))
        block_data.append(1 if block.get('bIsUniqueBuff', False) else 0)
        block_data.append(1 if block.get('bIsHeroBuff', False) else 0)
        block_data.append(block.get('bNotShowDmgFloat', 0))
        U("<i", block.get('BindSkillID', 0))
        U("<i", block.get('RemoveRuleID', 0))
        U("<i", block.get('ControlEffectType', 0))
        block_data.append(block.get('bBuffBorderType', 0))
        block_data.append(1 if block.get('bBuffRelocateByCopyedActor', False) else 0)
        U("<i", block.get('CoverCombineCfgID1', 0))
        U("<i", block.get('CoverCombineCfgID2', 0))
        U("<i", block.get('CoverCombineCfgID3', 0))
        block_data.append(1 if block.get('bBUsePreCrit', False) else 0)
        U("<i", block.get('UnknownI4', 0))
        U("<H", block.get('UnknownH2', 0))
        block_data.append(block.get('UnknownB1', 0))

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


def SkillCombineJson(filepath, mode):
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