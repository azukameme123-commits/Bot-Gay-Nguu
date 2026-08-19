'''import os
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

def SoundDatabinJs(Sound_Files, mode):
    def pstr(value):
        encd = value.encode('utf-8') + b'\x00'
        dd = len(encd)
        return struct.pack("<I", dd) + encd

    def B2Js(bsdata):
        offset = 140
        bs = []
        def rv(fmt, size):
            nonlocal offset
            value = struct.unpack_from(fmt, bsdata, offset)[0]
            offset += size
            return value
        def rvb():
            return rv("<B", 1) == 1
        def S(): return rv("<I", 4)
        def I(): return rv("<i", 4)
        def B1(): return rv("<B", 1)
        def Str():
            nonlocal offset
            dd = S()
            本 = bsdata[offset:offset + dd]
            offset += dd
            return 本.decode("utf-8", errors="replace").strip("\x00")

        while offset < len(bsdata):
            try:
                一 = {}
                blockinfo = S()
                一['CfgID'] = S()
                一['EventName'] = Str()
                一['HeroSkinID'] = S()
                一['MonsterID'] = S()
                一['OrganID'] = S()
                一['bType'] = B1()
                一['bFilter'] = B1()
                一['Param1'] = I()
                一['Param2'] = I()
                一['Param3'] = Str()
                一['Param4'] = Str()
                bs.append(一)
            except Exception as e:
                print(f"Error reading block at offset {offset}: {e}")
                break
        return json.dumps(bs, ensure_ascii=False, indent=4)

    def JstoB(jsdata, bifile):
        bs = json.loads(jsdata)
        bidata = bytearray()
        头 = (
            b'MSES\x07\x00\x00\x00' + 
            struct.pack("<II", 0, len(bs)) + 
            b'\x61' * 32 + 
            b'\x00' * 16 + b'UTF-8' + b'\x00' * 23
        ).ljust(140, b'\x00')
        bidata.extend(头)

        for 一 in bs:
            bdata = bytearray()
            def U(fmt, value):
                bdata.extend(struct.pack(fmt, value))
            def S1(value):
                bdata.extend(pstr(value))

            U("<I", 一.get('CfgID', 0))
            S1(一.get('EventName', ""))
            U("<I", 一.get('HeroSkinID', 0))
            U("<I", 一.get('MonsterID', 0))
            U("<I", 一.get('OrganID', 0))
            bdata.append(一.get('bType', 0))
            bdata.append(一.get('bFilter', 0))
            U("<i", 一.get('Param1', 0))
            U("<i", 一.get('Param2', 0))
            S1(一.get('Param3', ""))
            S1(一.get('Param4', ""))

            Blen = len(bdata)
            fblock = struct.pack("<I", Blen) + bdata
            bidata.extend(fblock)
            Bflast = Blen

        bidata[8:12] = struct.pack("<I", Bflast + 4)
        bidata[96:128] = hashlib.md5(bidata[140:]).hexdigest().encode()
        bidata[128:140] = b'\x00\x00\x00\x00\x8c\x00\x00\x00\x00\x00\x00\x00'

        with open(bifile, "wb") as bf:
            bf.write(bidata)

    Vfile = ["BattleBank", "ChatSound", "CoupleSound", "HeroSound", "LobbyBank", "LobbySound"]

    if mode == 1:
        for filename in os.listdir(Sound_Files):
            if any(filename.startswith(name) for name in Vfile) and filename.endswith(".bytes"):
                with open(f"{Sound_Files}/{filename}", "rb") as f:
                    data = B2Js(f.read())
                with open(f"{Sound_Files}/{filename}", "w", encoding="utf-8") as jsfile:
                    jsfile.write(data)
    
    elif mode == 2:
        for filename in os.listdir(Sound_Files):
            if any(filename.startswith(name) for name in Vfile) and filename.endswith(".bytes"):
                with open(f"{Sound_Files}/{filename}", "r", encoding="utf-8") as jsfile:
                    data = jsfile.read()
                with open(f"{Sound_Files}/{filename}", "wb") as bf:
                    JstoB(data, f"{Sound_Files}/{filename}")'''
                    
                    
                    
import struct, json, os, hashlib

def SoundDatabinJs(Sound_Files, mode):

    def pstr(value):
        encd = value.encode('utf-8') + b'\x00'
        return struct.pack("<I", len(encd)) + encd

    def B2Js(bsdata):
        offset = 140
        bs = []

        def rv(fmt, size):
            nonlocal offset
            value = struct.unpack_from(fmt, bsdata, offset)[0]
            offset += size
            return value

        def S(): return rv("<I", 4)
        def I(): return rv("<i", 4)
        def B1(): return rv("<B", 1)

        def Str():
            nonlocal offset
            dd = S()
            raw = bsdata[offset:offset + dd]
            offset += dd
            return raw.decode("utf-8", errors="replace").strip("\x00")

        while offset < len(bsdata):
            try:
                blockinfo = S()
                block_end = offset + blockinfo

                一 = {}
                一['CfgID'] = S()
                一['EventName'] = Str()
                一['HeroSkinID'] = S()
                一['MonsterID'] = S()
                一['OrganID'] = S()
                一['bType'] = B1()
                一['bFilter'] = B1()
                一['Param1'] = I()
                一['Param2'] = I()
                一['Param3'] = Str()
                一['Param4'] = Str()

                if offset < block_end:
                    一['Param5'] = B1()

                bs.append(一)

            except Exception as e:
                print(f"Error at offset {offset}: {e}")
                break

        return json.dumps(bs, ensure_ascii=False, indent=4)

    def JstoB(jsdata, out_file):
        bs = json.loads(jsdata)
        has_param5 = any('Param5' in x for x in bs)

        bidata = bytearray()

        header = (
            b'MSES\x07\x00\x00\x00' +
            struct.pack("<II", 0, len(bs)) +
            b'\x61' * 32 +
            b'\x00' * 16 + b'UTF-8' + b'\x00' * 23
        ).ljust(140, b'\x00')

        bidata.extend(header)

        Bflast = 0

        for 一 in bs:
            bdata = bytearray()

            def U(fmt, val):
                bdata.extend(struct.pack(fmt, val))

            def S1(val):
                bdata.extend(pstr(val))

            U("<I", 一.get('CfgID', 0))
            S1(一.get('EventName', ""))
            U("<I", 一.get('HeroSkinID', 0))
            U("<I", 一.get('MonsterID', 0))
            U("<I", 一.get('OrganID', 0))
            bdata.append(一.get('bType', 0))
            bdata.append(一.get('bFilter', 0))
            U("<i", 一.get('Param1', 0))
            U("<i", 一.get('Param2', 0))
            S1(一.get('Param3', ""))
            S1(一.get('Param4', ""))

            if has_param5:
                bdata.append(一.get('Param5', 0))

            Blen = len(bdata)
            bidata.extend(struct.pack("<I", Blen) + bdata)
            Bflast = Blen

        bidata[8:12] = struct.pack("<I", Bflast + 4)
        bidata[96:128] = hashlib.md5(bidata[140:]).hexdigest().encode()
        bidata[128:140] = b'\x00\x00\x00\x00\x8c\x00\x00\x00\x00\x00\x00\x00'

        with open(out_file, "wb") as f:
            f.write(bidata)

    Vfile = [
        "ACHeroBank", "ACHeroSound", "BattleBank", "ChatSound",
        "CoupleSound", "HeroSound", "LobbyBank", "LobbySound",
        "MonsterAndOrganSound", "SceneSound"
    ]

    if mode == 1:
        for filename in os.listdir(Sound_Files):
            if any(filename.startswith(x) for x in Vfile) and filename.endswith(".bytes"):

                path = os.path.join(Sound_Files, filename)

                with open(path, "rb") as f:
                    data = B2Js(f.read())

                with open(path, "w", encoding="utf-8") as f:
                    f.write(data)

    elif mode == 2:
        for filename in os.listdir(Sound_Files):
            if any(filename.startswith(x) for x in Vfile):

                path = os.path.join(Sound_Files, filename)

                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()

                JstoB(data, path)