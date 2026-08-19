import os
import sys
import getopt
import re
import json
import shutil
import random
import string
import struct
import hashlib
import tempfile
from io import BytesIO
from colorama import init, Fore, Back, Style
import zipfile
import pyzstd
import copy
import xml.etree.ElementTree as ET
import xml.dom.minidom
from xml.dom import minidom


def pack_string(value):
    encoded = value.encode('utf-8') + b'\x00'
    return struct.pack("<I", len(encoded)) + encoded


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


def _write_block(block, feature_slots):
    bd = bytearray()

    def U(fmt, v): bd.extend(struct.pack(fmt, v))
    def S1(v):     bd.extend(pack_string(v))

    U("<I", block.get('ID', 0))
    U("<I", block.get('HeroID', 0))
    S1(block.get('HeroName', ""))
    U("<I", block.get('SkinID', 0))
    S1(block.get('SkinName', ""))
    S1(block.get('SkinPicID', ""))
    U("<I", block.get('BaseCfgID', 0))
    U("<I", block.get('CombatAbility', 0))

    attrs = block.get('Attr') or []
    for i in range(15):
        if i < len(attrs):
            a = attrs[i]
            U("<H", a.get('Type', 0))
            bd.append(a.get('bValType', 0))
            U("<i", a.get('iValue', 0))
        else:
            U("<H", 0)
            bd.append(0)
            U("<i", 0)

    U("<I", block.get('GetGoldGain', 0))
    U("<I", block.get('GetGoldUpperLimitGain', 0))
    U("<I", block.get('PresentHeadImg', 0))
    S1(block.get('HeroSkinShareUrl', ""))
    S1(block.get('SettleShareUrl', ""))
    S1(block.get('WinRateShareUrl', ""))
    S1(block.get('SkinShowUrl', ""))

    if feature_slots == 10:
        raw = block.get('Feature') or []
        features = [f for f in raw if f.get('IconPath')]
        U("<i", len(features))
        for i in range(10):
            if i < len(features):
                S1(features[i].get('IconPath', ""))
                S1(features[i].get('Desc', ""))
            else:
                S1("")
                S1("")
    else:
        raw = block.get('SkinFeature') or []
        features = [f for f in raw if f.get('Icon')]
        U("<i", len(features))
        for i in range(20):
            if i < len(features):
                S1(features[i].get('Icon', ""))
                S1(features[i].get('Name', ""))
            else:
                S1("")
                S1("")

    S1(block.get('SkinBgAndTable', ""))
    S1(block.get('VideoWeb', ""))
    S1(block.get('VideoCover', ""))
    S1(block.get('LoadingProjectBox', ""))
    U("<I", block.get('CoinMultiple', 0))
    U("<I", block.get('CoinMultipleLimit', 0))
    S1(block.get('HeroSelectBuySkinBgColor', ""))
    S1(block.get('HeroLabel', ""))
    S1(block.get('HeroLabelColor', ""))
    S1(block.get('HeroLabelDesc', ""))
    bd.append(block.get('bHideUI', 0))
    bd.append(block.get('bDisableRot', 0))
    bd.append(block.get('bDisableBloom', 0))
    bd.append(block.get('bDisableDirLight', 0))
    bd.append(block.get('bScaleCamera', 0))
    U("<I", block.get('IsRecommendAIUsed', 0))
    bd.append(block.get('bEnableComponentLight', 0))
    U("<i", block.get('PresentSkinMotion', 0))
    bd.append(block.get('bIsDLC', 0))
    bd.append(block.get('bIsInAB', 0))
    U("<I", block.get('DLCWeight', 0))
    U("<I", block.get('Ratity', 0))
    U("<I", block.get('Level', 0))
    U("<I", block.get('Series', 0))
    S1(block.get('SkinPicCDNPath', ""))
    S1(block.get('SkinHeadCDNPath', ""))
    S1(block.get('TalePageCDNPath', ""))
    bd.append(block.get('bSkinDynamicPath', 0))
    bd.append(block.get('bIsHeroSkinShareTextOnRight', 0))
    S1(block.get('HeroVoiceActor', ""))
    bd.append(block.get('bUseDefaultBackground', 0))
    U("<i", block.get('SkinThemeID', 0))
    S1(block.get('SkinThemeName', ""))
    S1(block.get('HomePageSkinBgAndTable', ""))
    S1(block.get('ImprintAge', ""))
    S1(block.get('ReturnExtarJson', ""))
    U("<i", block.get('PlayFromEndSec', 0))
    U("<i", block.get('CamZoomInType', 0))
    U("<i", block.get('DeskAllPicOffSet', 0))
    U("<i", block.get('HighLightPicOffSet', 0))
    U("<i", block.get('LiteSoundPlayPos', 0))
    return bd


def _detect_slots_from_json(blocks):
    if not blocks:
        return 10
    first = blocks[0]
    if 'SkinFeature' in first:
        return 20
    if 'Feature' in first:
        return 10
    for key in ('SkinFeature',):
        if key in first:
            return 20
    return 10


def JstoB(json_data, binary_file, feature_slots=None):
    blocks = json.loads(json_data)
    if feature_slots is None:
        feature_slots = _detect_slots_from_json(blocks)

    binary_data = bytearray()
    header = bytearray()
    header.extend(b'MSES\x07\x00\x00\x00')
    header.extend(struct.pack("<I", 0))
    header.extend(struct.pack("<I", len(blocks)))
    header.extend(b'\x61' * 32)
    header.extend(b'\x00' * 16 + b'UTF-8' + b'\x00' * 23)
    header.extend(b'\x00' * (140 - len(header)))
    binary_data.extend(header)

    Bflast = 0
    for block in blocks:
        block_data = _write_block(block, feature_slots)
        Bflast = len(block_data)
        binary_data.extend(struct.pack("<I", Bflast) + block_data)

    Blast = Bflast + 4
    binary_data[8:12] = struct.pack("<I", Blast)
    md5_hash = hashlib.md5(binary_data[140:]).hexdigest().encode('utf-8')
    binary_data[96:96 + len(md5_hash)] = md5_hash
    binary_data[140 - 12:140] = b'\x00\x00\x00\x00\x8c\x00\x00\x00\x00\x00\x00\x00'

    with open(binary_file, "wb") as bf:
        bf.write(binary_data)


def HeroSkinJson(filepath, mode, feature_slots=None):
    """
    mode 1: .bytes → JSON
    mode 2: JSON → .bytes
    feature_slots: 10 (old format) hoặc 20 (new format), None = tự detect
    """
    if mode == 1:
        with open(filepath, "rb") as f:
            json_data = B2Js(f.read(), feature_slots=feature_slots)
        with open(filepath, "w", encoding="utf-8") as jf:
            jf.write(json_data)
    elif mode == 2:
        with open(filepath, "r", encoding="utf-8") as jf:
            json_data = jf.read()
        JstoB(json_data, filepath, feature_slots=feature_slots)