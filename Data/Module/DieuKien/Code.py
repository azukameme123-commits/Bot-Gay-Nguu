import os
import re
import json

def IDSOUND_AGES(i, ktr_Sound):
    with open (ktr_Sound, 'rb') as s:
        kts = s.read()
    if i.encode() in kts:
        ID_SKIN = i.encode()
        if ID_SKIN.decode()[3] == '0':
            IDSOUND1 = ID_SKIN.decode()[4]
        else:
            IDSOUND1 = ID_SKIN.decode()[-2:]
        IDSOUND = b"_Skin" + IDSOUND1.encode()
        ID_SOUND = IDSOUND.decode()
    else:
        ID_SOUND = ''
    return ID_SOUND

def dinhdang(ID_SKIN):
    ID_1 = ID_SKIN
    DINH_DANG_1 = hex(int(ID_1))[2:]
    if len(DINH_DANG_1) % 2 != 0:
        DINH_DANG_1 = '0' + DINH_DANG_1
    DINH_DANG_1 = DINH_DANG_1[-2:] + DINH_DANG_1[-4:-2]
    DINH_DANG_1 = bytes.fromhex(DINH_DANG_1)
    DINH_DANG_1 = b'\x00\x00' + DINH_DANG_1 + b'\x00\x00'
    a = DINH_DANG_1
    return DINH_DANG_1
    
def dkgtbv(ID_SKIN, Huanhua):
    DINH_DANG_1 = dinhdang(ID_SKIN)
    DK_MOD_GT = 'None'
    DK_MOD_BV = 'None'
    xyz_GIATOC = b'None'
    xyz_BIENVE = b'None'
    code_duoi_giatoc = b'None'
    with open(Huanhua, 'rb') as f:
        ab = f.read()
    ID_1 = ID_SKIN
    a = DINH_DANG_1
    i = ab.find(a) - 2
    vt = ab[i:i+2]
    vtr = int.from_bytes(vt, byteorder='little') + 4
    vt1 = ab[i:i+vtr]
    DKMBVGT = vt1
    DDSKM = DINH_DANG_1
    if b'Sprint' in DKMBVGT or b'run' in DKMBVGT:
        xyz_GIATOC = DKMBVGT.split(b'\x00\x00\x00')
        if ID_SKIN in ["14111"]:
            code_duoi_giatoc = xyz_GIATOC[-5][:-2]
            xyz_GIATOC = xyz_GIATOC[-4][:-2]
        else:
            code_duoi_giatoc = xyz_GIATOC[-6][:-2]
            xyz_GIATOC = xyz_GIATOC[-5][:-2]            
        xyz_GIATOC = xyz_GIATOC.split(b',')

        try:
            x_gt = "{:.3f}".format(float(xyz_GIATOC[0])) if xyz_GIATOC[0].strip() else "0.000"
            y_gt = "{:.3f}".format(float(xyz_GIATOC[1])) if xyz_GIATOC[1].strip() else "0.000"
            z_gt = "{:.3f}".format(float(xyz_GIATOC[2])) if xyz_GIATOC[2].strip() else "0.000"
        except (IndexError, ValueError) as e:
            x_gt = y_gt = z_gt = "0.000"
        xyz_GIATOC = (b'x="' + x_gt.encode() +b'" y="' + y_gt.encode() +b'" z="' + z_gt.encode() + b'"')
        DK_MOD_GT = 'Sprint'

    if DDSKM in DKMBVGT or ID_SKIN == "17408":
        if ID_SKIN in ['13311', '16707', '11620', '17408']:
            xyz_BIENVE = b'x="0.000" y="-0.300" z="0.000"'
        else:
            xyz_BIENVE = DKMBVGT.split(b'\x00\x00\x00')
            xyz_BIENVE = xyz_BIENVE[7]
            xyz_BIENVE = xyz_BIENVE.split(b',')
            x_bv = "{:.3f}".format(float(xyz_BIENVE[0]))
            y_bv = "{:.3f}".format(float(xyz_BIENVE[1]))
            z_bv = "{:.3f}".format(float(xyz_BIENVE[2]))
            xyz_BIENVE = (b'x="'+x_bv.encode()+b'"'+ b' y="'+y_bv.encode()+b'"'+ b' z="'+z_bv.encode()+b'"')
        DK_MOD_BV = 'Recall'
    return DK_MOD_GT, DK_MOD_BV, xyz_GIATOC.decode(), xyz_BIENVE.decode(), code_duoi_giatoc.decode()

def TimDieuKienModAges(ID_SKIN, file_icon):
    with open(file_icon, "r", encoding="utf-8") as f:
        data = json.load(f)

    for x in data:
        if str(x["ID"]) == str(ID_SKIN):
            features = (x.get("SkinFeature") or []) + (x.get("Feature") or [])

            for feat in features:
                icon = feat.get("Icon") or feat.get("IconPath")
                if icon in ["Skin_Icon_Skill", "LOD_Skin_Icon_Skill_G"]:
                    return True

            return False

    return False