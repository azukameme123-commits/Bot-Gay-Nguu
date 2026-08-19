import os
import json

import re

def is_text(s):
    return bool(re.search(r"[A-Za-z]", s))

def timskin(A, B, text):
    Tuong = TrPhuc = ""

    for line in text:
        if A in line:
            value = line[22:].strip()
            if is_text(value):
                Tuong = value

        if B in line:
            value = line[22:].strip()
            if (
                is_text(value)
                and "[ex][DNT]" not in value
                and "[ex]" not in value
            ):
                TrPhuc = value

        if Tuong and TrPhuc:
            break

    return f"{Tuong} {TrPhuc}".strip()

def Icon_Bac(ID, file_icon, file_bac, Kb):
    ID = str(ID)

    with open(file_icon, 'r', encoding="utf-8") as f:
        data = json.load(f)

    hero_prefix = ID[:3]

    code = None
    SkinID_MD = None
    Allhero = []

    for x in data:
        sid = str(x["ID"])
        if sid == ID:
            code = x
        if sid.startswith(hero_prefix):
            Allhero.append(x)
        if sid.startswith(hero_prefix + "00"):
            SkinID_MD = x["SkinID"]

    if not code:
        return

    Vien = code.get("PresentHeadImg")

    ID_EVO = {
        "16707": ("301677_2", "Share_16707_2.jpg", "16707_2.jpg", "BG_wukongjuexing2/BG_wukongjuexing2_Platform", "301677_2.jpg", "301677_2head.jpg"),
        "11620": ("3011620_1", "Share_11620_2.jpg", "11620_2.jpg", "BG_DaoFengJiNiang_11621/BG_yinyingzhishou_01_platform", "3011620_2.jpg", "3011620_2head.jpg"),
        "13311": ("3013311_1", "Share_13311_2.jpg", "13311_2.jpg", "BG_direnjie_13312_T3/BG_yinyingzhishou_01_platform", "3013311_1.jpg", "3013311_1head.jpg"),
    }

    if ID in ID_EVO:
        a, b, c, d, e, f2 = ID_EVO[ID]
        code.update({
            "SkinPicID": a,
            "HeroSkinShareUrl": b,
            "SettleShareUrl": b,
            "WinRateShareUrl": b,
            "SkinShowUrl": c,
            "SkinBgAndTable": d,
            "SkinPicCDNPath": e,
            "SkinHeadCDNPath": f2,
            "bSkinDynamicPath": 1
        })

    if ID == "13210":
        code["SkinPicID"] = "3013210"
    if ID == "10611":
        code["SkinPicID"] = "3010611"

    code["bIsInAB"] = 1
    
    if ID == "10812":
        TEN_SKIN = "Gildur Jiji"
    elif ID == "10917":
        TEN_SKIN = "Veera Momo"
    elif ID == "59903":
        TEN_SKIN = "Billow Okarun"
    else:
        TEN_SKIN = timskin(code["HeroName"], code["SkinName"], Kb)
    print(f"\n{TEN_SKIN}")

    if SkinID_MD is not None:
        code["SkinID"], SkinID_MD = 0, code["SkinID"]

    for i, phu in enumerate(data):
        if not str(phu["ID"]).startswith(hero_prefix):
            continue

        new = code.copy()
        new["ID"] = phu["ID"]
        new["HeroID"] = phu["HeroID"]
        new["SkinID"] = phu["SkinID"]
        new["bHideUI"] = 1

        if str(phu["ID"]).startswith(hero_prefix + "00"):
            new["SkinPicID"] = code["SkinPicID"][:5] + "0"
            new["SkinID"] = SkinID_MD
            if ID == "15412":
                new["SkinPicCDNPath"] = "3015412.jpg"
            if ID == "13118":
                new["SkinPicCDNPath"] = "301310.jpg"

        data[i] = new

    with open(file_icon, 'w', encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    with open(file_bac, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    codeskin = None
    for i in data:
        if str(i.get("ID")) == ID:
            codeskin = i
            break
    
    hero_prefix = ID[:3]
    hero_id = int(hero_prefix)
    
    if codeskin:
        if ID in ("13311", "16707", "15004", "11620"):
            codeskin["LimitLabelPicUrl"] = "Awake_Label_6.png"
            
        #Tạm Thời
        if ID in ("14120", "15905", "13316"):
    	    codeskin["LimitLabelPicUrl"] = f"{ID}.png"
        
        for i in data:
            if i.get("HeroID") == hero_id:
                new = codeskin.copy()
                new["ID"] = i["ID"]
                new["HeroID"] = i["HeroID"]
                new["SkinID"] = i["SkinID"]
                i.update(new)
    
    else:
        for i in data:
            if i.get("HeroID") == hero_id:
                i["LimitLabelPicUrl"] = f"{ID}.png"
    
    with open(file_bac, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return TEN_SKIN, Vien