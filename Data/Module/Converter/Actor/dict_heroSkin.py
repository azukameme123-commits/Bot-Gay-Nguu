import struct, json, os, hashlib


def _parse_block(bdata, feature_slots):
    boff = 0

    def rv(fmt, size):
        nonlocal boff
        if boff + size > len(bdata):
            raise struct.error(
                f"read past block end (boff={boff}, size={size}, block_size={len(bdata)})"
            )
        value = struct.unpack_from(fmt, bdata, boff)[0]
        boff += size
        return value

    def S():  return rv("<I", 4)
    def S2(): return rv("<H", 2)
    def I():  return rv("<i", 4)
    def B1(): return rv("<B", 1)

    def Str():
        nonlocal boff
        length = S()
        raw = bdata[boff:boff + length]
        boff += length
        return raw.decode("utf-8", errors="replace").strip("\x00")

    block = {}
    block['ID']            = S()
    block['HeroID']        = S()
    block['HeroName']      = Str()
    block['SkinID']        = S()
    block['SkinName']      = Str()
    block['SkinPicID']     = Str()
    block['BaseCfgID']     = S()
    block['CombatAbility'] = S()

    attrs = []
    for _ in range(15):
        attr_type  = S2()
        b_val_type = B1()
        i_value    = I()
        if attr_type != 0 or b_val_type != 0 or i_value != 0:
            attrs.append({"Type": attr_type, "bValType": b_val_type, "iValue": i_value})
    block['Attr'] = attrs if attrs else None

    block['GetGoldGain']           = S()
    block['GetGoldUpperLimitGain'] = S()
    block['PresentHeadImg']        = S()
    block['HeroSkinShareUrl']      = Str()
    block['SettleShareUrl']        = Str()
    block['WinRateShareUrl']       = Str()
    block['SkinShowUrl']           = Str()
    TotalFeature = I()

    if feature_slots == 10:
        features = []
        for _ in range(10):
            icon_path = Str()
            desc      = Str()
            if icon_path or desc:
                features.append({"IconPath": icon_path, "Desc": desc})
        block['Feature'] = features if features else None
    else:
        features = []
        for _ in range(20):
            icon = Str()
            name = Str()
            if icon or name:
                features.append({"Icon": icon, "Name": name})
        block['SkinFeature'] = features if features else None

    block['SkinBgAndTable']           = Str()
    block['VideoWeb']                 = Str()
    block['VideoCover']               = Str()
    block['LoadingProjectBox']        = Str()
    block['CoinMultiple']             = S()
    block['CoinMultipleLimit']        = S()
    block['HeroSelectBuySkinBgColor'] = Str()
    block['HeroLabel']                = Str()
    block['HeroLabelColor']           = Str()
    block['HeroLabelDesc']            = Str()
    block['bHideUI']                  = B1()
    block['bDisableRot']              = B1()
    block['bDisableBloom']            = B1()
    block['bDisableDirLight']         = B1()
    block['bScaleCamera']             = B1()
    block['IsRecommendAIUsed']        = S()
    block['bEnableComponentLight']    = B1()
    block['PresentSkinMotion']        = I()
    block['bIsDLC']                   = B1()
    block['bIsInAB']                  = B1()
    block['DLCWeight']                = S()
    block['Ratity']                   = S()
    block['Level']                    = S()
    block['Series']                   = S()
    block['SkinPicCDNPath']           = Str()
    block['SkinHeadCDNPath']          = Str()
    block['TalePageCDNPath']          = Str()
    block['bSkinDynamicPath']         = B1()
    block['bIsHeroSkinShareTextOnRight'] = B1()
    block['HeroVoiceActor']           = Str()
    block['bUseDefaultBackground']    = B1()
    block['SkinThemeID']              = I()
    block['SkinThemeName']            = Str()
    block['HomePageSkinBgAndTable']   = Str()
    block['ImprintAge']               = Str()
    block['ReturnExtarJson']          = Str()
    block['PlayFromEndSec']           = I()
    block['CamZoomInType']            = I()
    block['DeskAllPicOffSet']         = I()
    block['HighLightPicOffSet']       = I()
    block['LiteSoundPlayPos']         = I()
    return block, boff


def _detect_feature_slots(blocks_data):
    if len(blocks_data) < 144:
        return 10
    block_size = struct.unpack_from("<I", blocks_data, 140)[0]
    if block_size == 0 or 144 + block_size > len(blocks_data):
        return 10
    bdata = blocks_data[144:144 + block_size]
    for slots in (10, 20):
        try:
            _, boff = _parse_block(bdata, slots)
            if boff == len(bdata):
                return slots
        except Exception:
            pass
    return 10


def B2Js(blocks_data, feature_slots=None):
    if feature_slots is None:
        feature_slots = _detect_feature_slots(blocks_data)

    offset = 140
    blocks = []

    while offset < len(blocks_data):
        if offset + 4 > len(blocks_data):
            break
        block_size  = struct.unpack_from("<I", blocks_data, offset)[0]
        block_start = offset + 4
        block_end   = block_start + block_size
        if block_size == 0 or block_end > len(blocks_data):
            break

        bdata = blocks_data[block_start:block_end]
        try:
            block, _ = _parse_block(bdata, feature_slots)
            blocks.append(block)
        except (ValueError, struct.error) as e:
            print(f"Error reading block (global offset {offset}, block_size {block_size}): {e}")

        offset = block_end

    return json.dumps(blocks, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    pass
