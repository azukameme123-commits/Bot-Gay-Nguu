import os
import re
import copy
import xml.etree.ElementTree as ET
from copy import deepcopy

def AssetRefs(file, ID_SKIN, ID_HD, NAME_HERO, phukienbutter=None, phukienveres=None, Change_Actor=None):
    NAME_HERO_B = NAME_HERO.lower().encode()
    ID_SKIN_C = str(ID_SKIN)
    ID_SKIN_B = ID_SKIN_C.encode()

    if Change_Actor is None:
        Change_Actor = []
        
    with open(file, 'rb') as f:
        All = f.read()

    ListAll = All.split(b'\r\n')

    All = All.replace(b'Project/Assets/Prefabs/', b'') \
             .replace(b'Project\\Assets\\Prefabs\\', b'')

    effectf_code = b'prefab_skill_effects/hero_skill_effects/'
    CODE_EFF = [x for x in ListAll if effectf_code in x.lower()]

    for text in CODE_EFF:
        pattern = (re.escape(effectf_code + NAME_HERO_B + b'/') + b'(?:\\d+/)?')

        if ID_SKIN_C not in ['13311', '16707', '11620']:
            text1 = re.sub(pattern, effectf_code + NAME_HERO_B + b'/' + ID_SKIN_B + b'/', text, flags=re.IGNORECASE)
        else:
            ID_EOV = ID_SKIN_B + b'_5/'

            text1 = re.sub(pattern, b'prefab_skill_effects/component_effects/' + ID_SKIN_B + b'/' + ID_EOV, text, flags=re.IGNORECASE)
    
        effect_name = text1.split(b'/')[-2].split(b'"')[0].decode('utf-8')
    
        if effect_name in Change_Actor:
            text1 = text1.replace(b'"/>', b'.prefab"/>')
        elif ID_SKIN_C in ID_HD:
            text1 = text1.replace(b'"/>', b'_HD"/>')
        else:
            text1 = text1.replace(b'"/>', b'.prefab"/>')
    
        text1 = (text1.replace(b'_E.prefab', b'_E').replace(b'_e.prefab', b'_e').replace(b'.prefab.prefab', b'.prefab').replace(b'_E_HD', b'_E').replace(b'_e_HD', b'_e').replace(b'_HD_HD', b'_HD'))
    
        All = All.replace(text, text1)

    if ID_SKIN_C == '52007' and phukienveres:
        suf = b'5200401/' if phukienveres == "1" else b'5200402/'
        All = All.replace(b'prefab_skill_effects/hero_skill_effects/520_veres/52007/', b'prefab_skill_effects/component_effects/52007/' + suf).replace(b'prefab_skill_effects/hero_skill_effects/520_Veres/52007/', b'prefab_skill_effects/component_effects/52007/' + suf)

    if ID_SKIN_C == '15004':
        All = All.replace(b'prefab_skill_effects/hero_skill_effects/150_hanxin/15004/',b'prefab_skill_effects/component_effects/15033/15037/')
    
    if ID_SKIN_C == '11620':
        if phukienbutter == "1":
            suf = b'1162001/'
        elif phukienbutter == "2":
            suf = b'1162002/'
        else:
            suf = b'11620_5/'
 
        All = All.replace(b'11620/11620_3/', b'11620/11620_5/')
        All = (All.replace(b'hero_skill_effects/116_JingKe/11620/', b'Component_Effects/11620/' + suf).replace(b'hero_skill_effects/116_jingke/11620/', b'Component_Effects/11620/' + suf).replace(b'11620/11620_5/', b'11620/' + suf))
    
    if ID_SKIN_C == '15704':
        for k in ["Atk1","Atk3","Atk4","Spell1_1","Spell1_2","Spell1_1_2","Spell2","Spell3"]:
            All = All.replace(f'value="{k}"'.encode(), f'value="15704/{k}"'.encode())

    if ID_SKIN_C == '50105':
        for k in ["Atk1","Atk2","Atk3","Atk4","Atk5","Atk6","Spell1", "Spell2", "Spell3"]:
            All = All.replace(f'value="{k}"'.encode(), f'value="50105/{k}"'.encode())
        
    if ID_SKIN_C == '12806':
        for k in ["Atk1","Atk2","Atk3","Atk4","Atk5","Spell1_1","Spell1_2","Spell1_3","Spell2","Spell3"]:
            All = All.replace(f'value="{k}"'.encode(), f'value="12806/{k}"'.encode())

    if ID_SKIN_C == '51504':
        for k in ["Atk1","Atk2","Atk3","Atk4","Spell1-1","Spell1-2","Spell1-3","Spell2","Spell2-1","Spell2-2","Spell2-3","Spell3"]:
            All = All.replace(f'value="{k}"'.encode(), f'value="51504/{k}"'.encode())

    if ID_SKIN_C == '11107':
        for k in ["Atk1","Atk2","Atk3","Spell1","Spell2","Spell2_1","Spell3","Spell3_1","Spell_SSX"]:
            All = All.replace(f'value="{k}"'.encode(), f'value="11107/{k}"'.encode())

    if ID_SKIN_C == '13314':
        All = All.replace(b'prefab_characters/prefab_hero/133_DiRenJie/DiRenJie_spell03_cutin01', b'prefab_skill_effects/hero_skill_effects/133_DiRenJie/13314/DiRenJie_spell03_cutin01')

    with open(file, 'wb') as f:
        f.write(All)

    if not file or not os.path.exists(file):
        return

    tree = ET.parse(file)
    root = tree.getroot()
    base_subset = root.find(".//baseSubset")
    skin_subset = root.find(".//skinSubset")
    if skin_subset is not None and base_subset is not None:
        for skin_elem in skin_subset.findall(".//Element"):
            skin_id_elem = skin_elem.find("./v1[@type='System.UInt32']")
            if skin_id_elem is not None and skin_id_elem.get("value") == ID_SKIN:
                skin_data = skin_elem.find("./v2")
                if skin_data is not None:
                    for child in skin_data:
                        tag_name = child.tag
                        base_target = base_subset.find(f".//{tag_name}")
                        if base_target is not None:
                            for sub_elem in child:
                                base_target.append(deepcopy(sub_elem))
                                
    if ID_SKIN_C in ["13213", "19016", "12313", "16707"]:
        skillCombines = base_subset.find("skillCombines")
        if skillCombines is None:
            skillCombines = ET.SubElement(base_subset, "skillCombines")
            
        if ID_SKIN_C in ["13213"]:
            data = [
                "132235",
                "132123",
                "132456",
                "132789",
                "132890"
            ]

        elif ID_SKIN_C in ["12313"]:
            data = [
                "130912",
                "130913",
                "130914"
            ]            
            
        elif ID_SKIN_C in ["19016"]:
            data = [
                "130912",
                "130913"
            ]
            
        elif ID_SKIN_C in ["16707"]:
            data = [
                "167235",
                "167736",
                "167767",
            ]        
        existing = {
            el.find("v1").get("value")
            for el in skillCombines.findall("Element")
            if el.find("v1") is not None
        }
        
        for value in data:
            if value in existing:
                continue
        
            element = ET.SubElement(
                skillCombines,
                "Element",
                {
                    "var": "Com",
                    "type": "AssetRefAnalyser.Pair`2[System.UInt32,System.Int32]"
                }
            )
        
            ET.SubElement(
                element,
                "v1",
                {
                    "var": "String",
                    "type": "System.UInt32",
                    "value": value
                }
            )
            if ID_SKIN_C in ["13213"]:
                ET.SubElement(
                    element,
                    "v2",
                    {
                        "var": "String",
                        "type": "System.Int32",
                        "value": "3"
                    }
                )

            elif ID_SKIN_C in ["19016"]:
                ET.SubElement(
                    element,
                    "v2",
                    {
                        "var": "String",
                        "type": "System.Int32",
                        "value": "1"
                    }
                )
                
            elif ID_SKIN_C in ["16707"]:
                ET.SubElement(
                    element,
                    "v2",
                    {
                        "var": "String",
                        "type": "System.Int32",
                        "value": "3"
                    }
                )
                
            elif ID_SKIN_C in ["12313"]:
                ET.SubElement(
                    element,
                    "v2",
                    {
                        "var": "String",
                        "type": "System.Int32",
                        "value": "3"
                    }
                )
    tree.write(file, encoding="utf-8", xml_declaration=True)