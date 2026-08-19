from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict

FIX_BLOB_FILES: Dict[str, str] = {
    "CODES2B1": "13011/CODES2B1.xml",
    "CODES2B1MOD": "13011/CODES2B1MOD.xml",
    
    "CODES1LAUMOD": "14111/CODES1LAUMOD.xml",
    "CODES1B1LAUMOD": "14111/CODES1B1LAUMOD.xml",
    "CODES1B2LAUMOD": "14111/CODES1B2LAUMOD.xml",
    
    "ACTIONU1": "15015/ACTIONU1.xml",
    "U1MOD": "15015/U1MOD.xml",
    
    "ACTION": "13210/ACTION.xml",
    "A1MOD": "13210/A1MOD.xml",
    "A2MOD": "13210/A2MOD.xml",
    "A3MOD": "13210/A3MOD.xml",
    "S1MOD": "13210/S1MOD.xml",
    
    "S12MOD": "13210/S12MOD.xml",
    "S1B1MOD": "13210/S1B1MOD.xml",
    
    "S215013": "15013/S2.xml",
    "S2MOD15013": "15013/S2MOD.xml",
    
    "WUKONGBACKMOD": "16707/16707_BackMod.xml",
    "WUKONGU1B0": "16707/U1B0.xml",
    "WUKONGU1B0MOD": "16707/U1B0Mod.xml",
    
    "BACKFIXBILLOW": "59901/BACKFIXBILLOW.xml",
    
    "KAITOS1B1": "13213/S1B1.xml",
    "A1MOD13213": "13213/A1MOD.xml",
    "A2MOD13213": "13213/A2MOD.xml",
    "A3MOD13213": "13213/A3MOD.xml",
    
    "Ulti19016": "19016/U1.xml",
    
    "BACK59903": "59903/BACKFIXBILLOW.xml",
}

FIX_BASE_DIR = Path(__file__).resolve().parents[2] / "Fix"


def _rfile(path: str) -> bytes:
    return (FIX_BASE_DIR / path).read_bytes()


def _load_fix_data() -> Dict[str, bytes]:
    return {name: _rfile(rel_path) for name, rel_path in FIX_BLOB_FILES.items()}


FIX_DATA = _load_fix_data()


def _blob(name: str) -> bytes:
    return FIX_DATA[name]


def _replace_action_ci(content: bytes, replacement: bytes) -> bytes:
    return re.compile(re.escape(_blob("ACTION")), re.IGNORECASE).sub(replacement, content)

def FixCodeSkin(ID_SKIN, THU_MUC_SKILL, NAME_HERO, phukienbutter, phukienveres):
    NAME_HERO = NAME_HERO.lower()
    ID_SKIN = ID_SKIN.encode()
    duongvaotimem = os.listdir(THU_MUC_SKILL)
    '''if ID_SKIN[:3] == b"521":
        kich_thuoc = input(" Nhập Kích Thước Hoa Mặc Định 1.0: ").strip() or "1.0"'''
    for file_skill in duongvaotimem:
        file_path = os.path.join(THU_MUC_SKILL, file_skill)
        if not os.path.isfile(file_path):
            continue

        if ID_SKIN[:3] == b"106":
            if file_skill == "U1E1.xml":               
                with open(file_path, 'rb') as f:
                    rpl = f.read()
                tracks = rpl.split(b"</Track>")
                modified_tracks = []
                for track in tracks:
                    if (b'trackName="10620\xe8\xa1\xa8\xe7\x8e\xb0' in track):
                        track = (track.replace(b'ba87253d-ce28-41ab-8390-c856bb239982', b'52ea47c3-1b89-4701-9481-4b7eb7fb63f8'))                                         
                        modified_tracks.append(track + b"</Track>")             
                    else:                                                              
                        modified_tracks.append(track + b"</Track>")                         
                rpl = b"".join(modified_tracks)    
                if rpl.endswith(b"</Track>"):
                    rpl = rpl[:-8]                            
                with open(file_path, 'wb') as f:
                    f.write(rpl)  

        if ID_SKIN == b"52007":           
            if phukienveres == "1":
                with open(file_path, 'rb') as f:
                    rpl = f.read().replace(b'prefab_skill_effects/hero_skill_effects/520_veres/52007/', b'prefab_skill_effects/component_effects/52007/5200401/').replace(b'prefab_skill_effects/hero_skill_effects/520_Veres/52007/', b'prefab_skill_effects/component_effects/52007/5200401/')
                with open(file_path, 'wb') as f:
                    f.write(rpl)          
                    
            elif phukienveres == "2":
                with open(file_path, 'rb') as f:
                    rpl = f.read().replace(b'prefab_skill_effects/hero_skill_effects/520_veres/52007/',b'prefab_skill_effects/component_effects/52007/5200402/').replace(b'prefab_skill_effects/hero_skill_effects/520_Veres/52007/', b'prefab_skill_effects/component_effects/52007/5200402/')
                with open(file_path, 'wb') as f:
                    f.write(rpl)

            if file_skill == "A3.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<String name="clipName" value="Atk3"', b'<String name="clipName" value="Atk1"')
                with open(file_path,'wb') as f: f.write(sec)
                                    
        if ID_SKIN == b"15412":
            if file_skill == "P12E2.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'prefab_skill_effects/hero_skill_effects/154_huamulan/15412/15413_HuaMuLan_Red', b'prefab_skill_effects/hero_skill_effects/154_HuaMuLan/15413_HuaMuLan_Red')
                with open(file_path,'wb') as f: f.write(sec)
        
        if ID_SKIN in [b"51504", b"11107", b"15704", b"12806", b"50105"]:
            if file_skill != "Death.xml":                     
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<String name="clipName" value="Atk', b'<String name="clipName" value="' + ID_SKIN + b'/Atk').replace(b'<String name="clipName" value="Spell', b'<String name="clipName" value="' + ID_SKIN + b'/Spell')
                with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN in [b"51504"]:
            if file_skill != "Death.xml":                     
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<String name="changedAnimName" value="Spell', b'<String name="changedAnimName" value="' + ID_SKIN + b'/Spell')
                with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN in [b"10506"]:
            if file_skill == "P4E1.xml":                     
                with open(file_path, 'rb') as f:
                    rpl = f.read()
                tracks = rpl.split(b"</Track>")
                modified_tracks = []
                for track in tracks:
                    if (b'Bip001 L ' in track):                                            
                        track = (track.replace(b'enabled="true"', b'enabled="false"'))
                        modified_tracks.append(track + b"</Track>")      
                    else:                                                              
                        modified_tracks.append(track + b"</Track>")                                
                rpl = b"".join(modified_tracks)    
                if rpl.endswith(b"</Track>"):
                    rpl = rpl[:-8]                            
                with open(file_path, 'wb') as f:
                    f.write(rpl)    

        if ID_SKIN[:3] == b"524":
            if file_skill == "A1E9.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'prefab_skill_effects/hero_skill_effects/524_Capheny/'+ID_SKIN+b'/Atk1_FireRange',b'prefab_skill_effects/hero_skill_effects/524_Capheny/Atk1_FireRange')
                with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN[:3] == b"537":
            if file_skill == "S12.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'prefab_skill_effects/hero_skill_effects/537_Trip/Trip_attack_spell01_1prefab_skill_effects/hero_skill_effects/537_Trip/Trip_attack_spell01_1prefab_skill_effects/hero_skill_effects/537_Trip/Trip_attack_spell01_1_S',b'prefab_skill_effects/hero_skill_effects/537_Trip/' + ID_SKIN + b'Trip_attack_spell01_1_S')
                with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN == b"53702":
            if file_skill in ["S13B1.xml", "S14B1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(b'prefab_skill_effects/hero_skill_effects/537_trip/53702/Trip_attack_spell01_Indicator',b'prefab_skill_effects/hero_skill_effects/537_Trip/Trip_attack_spell01_Indicator')
                with open(file_path,'wb') as f: f.write(sec)
                               
        if ID_SKIN[:3] == b"544":
            if file_skill =="U1E0.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'Bone_Whisk03',b'Bone_Weapon01')
                with open(file_path,'wb') as f: f.write(sec)                      

            if file_skill == "A4B1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'544_painter/'+ ID_SKIN +b'/Painter_Atk4_blue',b'544_painter/Painter_Atk4_blue').replace(b'544_painter/'+ID_SKIN+b'/Painter_Atk4_red',b'544_painter/Painter_Atk4_red')
                with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN == b"15004":
            with open(file_path, 'rb') as f: sec = f.read().replace(b'prefab_skill_effects/hero_skill_effects/150_hanxin/15004/',b'prefab_skill_effects/component_effects/15033/15037/')
            with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN == b"10620":    
            if file_skill in ["S2B1.xml"]:                     
                with open(file_path, 'rb') as f: rpl = f.read().replace(b'xiaoqiao_skill02_bullet" refParamName="" useRefParam="false" />', b'xiaoqiao_skill02_bullet" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/xiaoqiao_skill02_02_bullet" refParamName="" useRefParam="false" />').replace(b'xiaoqiao_skill02_bullet_E" refParamName="" useRefParam="false" />', b'xiaoqiao_skill02_bullet_E" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/xiaoqiao_skill02_02_bullet_E" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(rpl)                                        
               
            if file_skill in ["U1E1.xml"]:                     
                with open(file_path, 'rb') as f: rpl = f.read().replace(b'\r\n        <int name="skinId" value="10611" refParamName="" useRefParam="false" />\r\n        <bool name="bEqual" value="false" refParamName="" useRefParam="false" />', b'').replace(b'<int name="skinId" value="10611" refParamName="" useRefParam="false" />', b'<int name="skinId" value="10620" refParamName="" useRefParam="false" />\r\n        <bool name="bEqual" value="false" refParamName="" useRefParam="false" />').replace(b'        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/xiaoqiao_skill03_hurt" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/T2_xiaoqiao_skill03_hurt_01" refParamName="" useRefParam="false" />\r\n        <String name="resourceName3" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/T2_xiaoqiao_skill03_hurt_02" refParamName="" useRefParam="false" />', b'        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/xiaoqiao_skill03_hurt" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/xiaoqiao_skill03_02_hurt" refParamName="" useRefParam="false" />\r\n        <String name="resourceName3" value="prefab_skill_effects/hero_skill_effects/106_xiaoqiao/10620/xiaoqiao_skill03_03_hurt" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(rpl)                                        
               
        if ID_SKIN == b"16707":
            with open(file_path, 'rb') as f: sec = f.read().replace(b"prefab_skizll_effects/hero_skill_effects/167_wukong/", b"prefab_skill_effects/component_effects/16707/16707_5/")
            with open(file_path,'wb') as f: f.write(sec)                       
                
            if file_skill == "U1B0.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("WUKONGU1B0"), _blob("WUKONGU1B0MOD"))
                with open(file_path,'wb') as f: f.write(sec)                       
                
            if file_skill == "16707_Back.xml":
                with open(file_path, 'wb') as f:
                    f.write(_blob("WUKONGBACKMOD"))

        if ID_SKIN == b"11620":
            with open(file_path, 'rb') as f: sec = f.read().replace(b'11620/11620_3/', b'11620/11620_5/')
            with open(file_path,'wb') as f: f.write(sec)                                            
                    
            if phukienbutter == "1":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'11620/11620_5/' ,b'11620/1162001/')
                with open(file_path,'wb') as f: f.write(sec)
            elif phukienbutter == "2":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'11620/11620_5/' ,b'11620/1162002/')
                with open(file_path,'wb') as f: f.write(sec)                  
                    
        if ID_SKIN == b"13609":
            if file_skill == "U1B1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<String name="resourceName" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03" refParamName="" useRefParam="false" />', b'<String name="resourceName" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03_1" refParamName="" useRefParam="false" />\r\n        <String name="resourceName3" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03_2" refParamName="" useRefParam="false" />').replace(b'<String name="resourceName" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03_e" refParamName="" useRefParam="false" />', b'<String name="resourceName" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03_e" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03_1_e" refParamName="" useRefParam="false" />\r\n        <String name="resourceName3" value="prefab_skill_effects/hero_skill_effects/136_wuzetian/13609/wuzetian_attack_spell03_2_e" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(sec)
                
            if file_skill == "S1B1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<Vector3 name="scaling" x="1.300" y="1.000" z="1.000" refParamName="" useRefParam="false" />', b'<Vector3 name="scaling" x="1.000" y="1.000" z="1.000" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(sec)

        if ID_SKIN == b"13613":
            if file_skill == "S1B1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<Vector3 name="scaling" x="1.300" y="1.000" z="1.000" refParamName="" useRefParam="false" />', b'<Vector3 name="scaling" x="1.000" y="1.000" z="1.000" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(sec)                        

        if ID_SKIN == b"13111":
            with open(file_path, 'rb') as f: sec = f.read().replace(b'Bip001 Prop1', b'Bone_Weapon01').replace(b'Bone_Blade', b'Bone_Weapon01')
            with open(file_path,'wb') as f: f.write(sec)          
                                    
        if ID_SKIN == b"13011":      
            if file_skill == "S2B1.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = content.replace(b'<TemplateObject name="targetId" id="2" objectName="bullet" isTemp="true" refParamName="" useRefParam="false" />\r\n        <String name="resourceName"',b'<TemplateObject name="targetId" id="0" objectName="self" isTemp="true" refParamName="" useRefParam="false" />\r\n        <String name="resourceName"')
                with open(file_path, 'wb') as f:
                    f.write(content)        
 
            if file_skill == "S21.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = content.replace(b'<Track trackName="TriggerParticleTick1" eventType="TriggerParticleTick" guid="a07302eb-cb3b-4146-9996-d018f92247aa" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">', b'<Track trackName="TriggerParticleTick1" eventType="TriggerParticleTick" guid="a07302eb-cb3b-4146-9996-d018f92247aa" enabled="false" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">').replace(b"GongBenWuZang_attack01_spell01_2", b"GongBenWuZang_attack01_spell01_1")
                with open(file_path, 'wb') as f:
                    f.write(content)           
                    
            if file_skill == "S22.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = content.replace(b'<Track trackName="TriggerParticleTick1" eventType="TriggerParticleTick" guid="a07302eb-cb3b-4146-9996-d018f92247aa" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">', b'<Track trackName="TriggerParticleTick1" eventType="TriggerParticleTick" guid="a07302eb-cb3b-4146-9996-d018f92247aa" enabled="false" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">').replace(b'GongBenWuZang_attack01_spell01_3', b'GongBenWuZang_attack01_spell01_2')
                with open(file_path, 'wb') as f:
                    f.write(content)

        if ID_SKIN == b"14111":       
            if file_skill in ["A1B2.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), b'    <Track trackName="" eventType="CheckSkillCombineConditionTick" guid="KM-14111" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">\r\n      <Event eventName="CheckSkillCombineConditionTick" time="0.000" isDuration="false">\r\n        <int name="skillCombineId" value="141920"/>\r\n        <Enum name="checkOPType" value="5"/>\r\n        <int name="skillCombineLevel" value="1"/>\r\n      </Event>\r\n    </Track>\r\n    <Track trackName="" eventType="TriggerParticle" guid="971ee44c-f85b-465b-8e63-245d921efc03" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">\r\n      <Condition id="26" guid="KM-14111" status="false"/>\r\n      <Event eventName="TriggerParticle" time="0.000" length="0.500" isDuration="true" guid="954698cf-e628-4f3c-868c-b7785364ff3e">\r\n        <TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true"/>\r\n        <TemplateObject name="objectSpaceId" objectName="bullet" id="2" isTemp="true"/>\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/141_Diaochan/14111/diaochan_fly_01"/>\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000"/>\r\n      </Event>\r\n    </Track>\r\n    <Track trackName="" eventType="TriggerParticle" guid="6b711fb7-811b-4457-9a40-68851df3b739" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">\r\n      <Condition id="26" guid="KM-14111" status="true"/>\r\n      <Event eventName="TriggerParticle" time="0.000" length="0.500" isDuration="true" guid="1d80d988-27ba-452c-a277-35f6319af16e">\r\n        <TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true"/>\r\n        <TemplateObject name="objectSpaceId" objectName="bullet" id="2" isTemp="true"/>\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/141_Diaochan/14111/diaochan_fly_01_s"/>\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000"/>\r\n      </Event>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

            if file_skill in ["S1B1.xml", "S1B2.xml"]:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = re.sub(b'"resourceName" value="(.*?)"', b'"resourceName" value="KM-MOD-AOV"', content)
                with open(file_path, 'wb') as f:
                    f.write(content)                         
 
            if file_skill in ["S1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), _blob("CODES1LAUMOD"))
                with open(file_path,'wb') as f: f.write(sec)                     
                
            if file_skill in ["S1B1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), _blob("CODES1B1LAUMOD"))
                with open(file_path,'wb') as f: f.write(sec)                     

            if file_skill in ["S1B2.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), _blob("CODES1B2LAUMOD"))
                with open(file_path,'wb') as f: f.write(sec)                     
                                               
        if ID_SKIN == b"13210":              
            if file_skill == "A1.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    new_content = _replace_action_ci(content, _blob("A1MOD"))
                with open(file_path, 'wb') as f:
                    f.write(new_content)
                    
            if file_skill == "A2.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    new_content = _replace_action_ci(content, _blob("A2MOD"))
                with open(file_path, 'wb') as f:
                    f.write(new_content)   
    
            if file_skill == "A3.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    new_content = _replace_action_ci(content, _blob("A3MOD"))
                with open(file_path, 'wb') as f:
                    f.write(new_content)        

            if file_skill in ['S1B0.xml', 'S11B0.xml', 'S12B0.xml']:                    
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = re.sub(b'"resourceName" value="(.*?)"', b'"resourceName" value="KM-MOD-AOV"', content)
                    new_content = _replace_action_ci(content, _blob("S1MOD"))
                    new_content = _replace_action_ci(new_content, _blob("S12MOD"))
                with open(file_path, 'wb') as f:
                    f.write(new_content)        
                    
            if file_skill == "S1B1.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    new_content = _replace_action_ci(content, _blob("S1B1MOD"))
                with open(file_path, 'wb') as f:
                    f.write(new_content)

        if ID_SKIN == b"13112":
            if file_skill == "P1E5.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = re.sub(b'"resourceName" value="(.*?)"', b'"resourceName" value="KM-MOD-AOV"', content)
                    new_content = content.replace(_blob("ACTIONU1"), b'     <Track trackName="" eventType="TriggerParticle" guid="KM-MOD-Z" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false">\r\n      <Event eventName="TriggerParticle" time="0.000" length="5.000" isDuration="true">\r\n        <TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true" />\r\n        <TemplateObject name="objectSpaceId" objectName="bullet" id="2" isTemp="true" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/131_libai/13112/LiBai_buff_07" />\r\n        <String name="bindPointName" value="Bip001 Prop1" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" />\r\n      </Event>\r\n    </Track>\r\n  </Action>')
                with open(file_path, 'wb') as f:
                    f.write(new_content)
                    
            if file_skill == "S1E5.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = re.sub(b'"resourceName" value="(.*?)"', b'"resourceName" value="KM-MOD-AOV"', content)
                    new_content = content.replace(_blob("ACTIONU1"), b'     <Track trackName="" eventType="TriggerParticle" guid="KM-MOD-AOV" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false">\r\n      <Event eventName="TriggerParticle" time="0.000" length="10.000" isDuration="true">\r\n        <TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true" />\r\n        <TemplateObject name="objectSpaceId" objectName="bullet" id="2" isTemp="true" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/131_libai/13112/libai_buff_02" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/131_libai/13112/LiBai_buff_02_a" />\r\n        <String name="resourceName3" value="prefab_skill_effects/hero_skill_effects/131_libai/13112/LiBai_buff_02_b" />\r\n        <Vector3 name="scaling" x="1" y="1.25" z="1" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" />\r\n      </Event>\r\n    </Track>\r\n  </Action>')
                with open(file_path, 'wb') as f:
                    f.write(new_content)

        if ID_SKIN == b"13118":          
            if file_skill in ["U1B1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), b'    <Track trackName="" eventType="TriggerParticle" guid="KM-MOD-AOV" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Condition id="17" guid="8d804687-bf09-4268-b04b-ced794ebaa7f" status="true"/>\r\n      <Event eventName="TriggerParticle" time="0.000" length="2.000" isDuration="true">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false" refParamName="" useRefParam="false"/>\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false"/>\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/131_LiBai/13118/libai_attack01_spell03c" refParamName="" useRefParam="false"/>\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false"/>\r\n      </Event>\r\n      <SkinOrAvatarList id="13118"/>\r\n    </Track>\r\n    <Track trackName="" eventType="TriggerParticle" guid="KM-MOD-AOV" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Condition id="17" guid="8d804687-bf09-4268-b04b-ced794ebaa7f" status="false"/>\r\n      <Event eventName="TriggerParticle" time="0.000" length="2.000" isDuration="true">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false" refParamName="" useRefParam="false"/>\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false"/>\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/131_LiBai/13118/libai_attack06_spell03c" refParamName="" useRefParam="false"/>\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false"/>\r\n      </Event>\r\n      <SkinOrAvatarList id="13118"/>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN == b"50108":          
            if file_skill in ["S2B1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), b'    <Track trackName="" eventType="TriggerParticle" guid="KM-MOD-AOV" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false">\r\n      <Event eventName="TriggerParticle" time="0.000" length="1.500" isDuration="true" guid="1f7acfcf-6f54-4477-953b-66309ed835d8">\r\n        <TemplateObject name="targetId" objectName="bullet1" id="3" isTemp="true"/>\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_TelAnnas/50108/TelAnnas_spell2" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/501_TelAnnas/50108/TelAnnas_spell2_2" />\r\n        <String name="resourceName3" value="prefab_skill_effects/hero_skill_effects/501_TelAnnas/50108/TelAnnas_spell2_2" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" />\r\n      </Event>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
                
        if ID_SKIN == b"59702":          
            if file_skill in ["U1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), b'    <Track trackName="" eventType="TriggerParticleTick" guid="KM-MOD-AOV" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticleTick" time="0.000" isDuration="false">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false"/>\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false"/>        \r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/597_kuangtie/59702/kuangtie_attack_spell03"/>\r\n        <float name="lifeTime" value="4.000"/>\r\n        <Vector3 name="scaling" x="1.150" y="1.150" z="1.150"/>\r\n        <bool name="applyActionSpeedToParticle" value="false"/>\r\n      </Event>\r\n     <SkinOrAvatarList id="59702"/>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

            if file_skill in ["U11B1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), b'    <Track trackName="" eventType="TriggerParticleTick" guid="KM-MOD-AOV" enabled="true" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticleTick" time="0.066" isDuration="false">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false"/>\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false"/>\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/597_KuangTie/59702/kuangtie_attack02_spell03"/>\r\n        <float name="lifeTime" value="4.000"/>\r\n        <Vector3 name="scaling" x="1.150" y="1.150" z="1.150"/>\r\n        <bool name="bUseRealScaling" value="true"/>\r\n        <bool name="applyActionSpeedToParticle" value="false"/>\r\n      </Event>\r\n      <SkinOrAvatarList id="59702"/>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
                                                        
        if ID_SKIN == b"15015":
            if file_skill == "U1.xml":
                with open(file_path, 'rb') as f:
                    content = f.read()
                    content = re.sub(b'"resourceName" value="(.*?)"', b'"resourceName" value="KM-MOD-AOV"', content)
                    new_content = content.replace(_blob("ACTIONU1"),_blob("U1MOD"))
                with open(file_path, 'wb') as f:
                    f.write(new_content)                                      

        if ID_SKIN == b"15013":          
            if file_skill in ["S2.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(b'      <Condition id="17" guid="b73050c0-0afc-4e3b-98e2-6ffe12d3d489" status="true" />\r\n      <Condition id="18" guid="84b2cbba-51cc-4673-adab-a3624a854953" status="true" />', b'      <Condition id="18" guid="84b2cbba-51cc-4673-adab-a3624a854953" status="true" />').replace(b'      <Condition id="17" guid="b73050c0-0afc-4e3b-98e2-6ffe12d3d489" status="true" />\r\n      <Event eventName="CheckActorPositionDuration"', b'      <Event eventName="CheckActorPositionDuration"').replace(b'      <Condition id="17" guid="b73050c0-0afc-4e3b-98e2-6ffe12d3d489" status="true" />\r\n      <Event eventName="HitTriggerTick"', b'      <Event eventName="HitTriggerTick"').replace(b'      <Condition id="40" guid="173653f1-8aaf-47ee-84a3-92cf343f6711" status="false" />\r\n      <Condition id="17" guid="b73050c0-0afc-4e3b-98e2-6ffe12d3d489" status="true" />\r\n      <Event eventName="SetAnimationParamsTick"', b'      <Condition id="40" guid="173653f1-8aaf-47ee-84a3-92cf343f6711" status="false" />\r\n      <Event eventName="SetAnimationParamsTick"').replace(b'      <Condition id="16" guid="0ba75381-3d32-4aa6-9e9f-7fc5a2488448" status="true" />\r\n      <Event eventName="PlayAnimDuration"', b'      <Event eventName="PlayAnimDuration"').replace(_blob("S215013"), _blob("S2MOD15013"))
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN == b"19015":          
            if file_skill in ["S1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(b'aea0a916-e3f8-4524-b464-307e531ce3ae" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="9">', b'aea0a916-e3f8-4524-b464-307e531ce3ae" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">')
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN == b"19016":
            if file_skill in ["S1B1.xml", "S1B2.xml", "S1B3.xml"]:   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticle0" eventType="TriggerParticle" guid="dd0e80af-00f9-4a45-a03f-d5e2ed3e4f71" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticle" time="0.000" length="2.000" isDuration="true" guid="bd7db382-7e96-441d-b3c0-ec748689a52c">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="bullet" id="2" isTemp="true" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="Prefab_Skill_Effects/Hero_Skill_Effects/190_Zhugeliang/19016/Zhugeliang_attack01_spell02_2" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="19016" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
                    
            if file_skill in ["U1.xml"]:   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'    <Track trackName="SimpleSpawnBuffTick0" eventType="SimpleSpawnBuffTick" guid="b4dc6410-e552-4cbd-9058-6a340c69d51b" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Condition id="2" guid="0f419793-de79-4f4e-ab29-93d9226ff671" status="true" />', _blob("Ulti19016"))
                with open(file_path,'wb') as f: f.write(sec)                     
                                       
        if ID_SKIN == b"14120":
            if file_skill in ["S2.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(_blob("ACTIONU1"), b'    <Track trackName="" eventType="SpawnBulletTick" guid="KM-MOD-AOV" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="SpawnBulletTick" time="0.000" isDuration="false">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false"/>\r\n        <String name="ActionName" value="Prefab_Characters/Prefab_Hero/141_DiaoChan/skill/S214112.xml" refParamName="" useRefParam="false"/>\r\n        <bool name="bAgeImmeStop" value="true" refParamName="" useRefParam="false"/>\r\n      </Event>\r\n      <SkinOrAvatarList id="14120"/>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

            if file_skill in ["S214112.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="bullet" id="2" isTemp="true" refParamName="" useRefParam="false" />', b'<TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />').replace(b'<bool name="applyActionSpeedToParticle" value="false" refParamName="" useRefParam="false" />\r\n        <int name="iDelayDisappearTime" value="1000" refParamName="" useRefParam="false" />\r\n        <bool name="bPartyDelayDisppear" value="true" refParamName="" useRefParam="false" />', b'<bool name="applyActionSpeedToParticle" value="false" refParamName="" useRefParam="false" />\r\n        <int name="iDelayDisappearTime" value="1000" refParamName="" useRefParam="false" />\r\n        <bool name="bPartyDelayDisppear" value="true" refParamName="" useRefParam="false" />\r\n        <bool name="enableMaxFollowTime" value="true" refParamName="" useRefParam="false" />\r\n        <float name="maxFollowTime" value="0.400" refParamName="" useRefParam="false" />\r\n        <bool name="bOnlyFollowPos" value="true" refParamName="" useRefParam="false" />\r\n        <bool name="b1stTickParentRot" value="true" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(sec)                     
                     
                                                              
        if ID_SKIN == b"59901":
            if file_skill == "A5.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<TemplateObject name="objectSpaceId" objectName="bullet3" id="5" isTemp="true" refParamName="" useRefParam="false" />', b'<TemplateObject name="parentId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />')
                with open(file_path,'wb') as f: f.write(sec)                     
 
            if file_skill == "S1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="SpawnBulletTick0" eventType="SpawnBulletTick" guid="82100141-8ca0-46c5-b959-23564e8f5a65" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="false" SkinAvatarFilterType="11">\r\n      <Event eventName="SpawnBulletTick" time="0.000" isDuration="false" guid="a9e02aa3-648e-4c24-8147-a6076fac66fe">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="ActionName" value="Prefab_Characters/Prefab_Hero/599_LvMeng/skill/Back" refParamName="" useRefParam="false" />\r\n        <int name="bulletTypeId" value="5991" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="59901" />\r\n      <SkinOrAvatarList id="59903" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
                             
            if file_skill == "Back.xml":                            
                with open (file_path, 'wb') as f:
                    f.write(_blob("BACKFIXBILLOW"))                            

        if ID_SKIN == b"59903":
            if file_skill == "S1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="SpawnBulletTick0" eventType="SpawnBulletTick" guid="e2fba3ec-bd0c-484d-abbd-db7903763f40" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="SpawnBulletTick" time="0.000" isDuration="false" guid="db66f448-10a4-440f-9ff2-74c799c4aec4">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="ActionName" value="Prefab_Characters/Prefab_Hero/599_LvMeng/skill/Back" refParamName="" useRefParam="false" />\r\n        <int name="bulletTypeId" value="5991" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="59901" />\r\n      <SkinOrAvatarList id="59903" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
 
            if file_skill == "Back.xml":                            
                with open (file_path, 'wb') as f:
                    f.write(_blob("BACK59903"))
                
        if ID_SKIN == b"52414":
            if file_skill == "S3B1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>',b'    <Track trackName="\xe6\x9e\xaa\xe5\x8f\xa3\xe7\x89\xb9\xe6\x95\x88" eventType="TriggerParticle" guid="7e9d5fca-8e56-45b0-9fb2-d2ba97cfa6d3" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticle" time="0.000" length="4.000" isDuration="true" guid="2840ce3c-5daa-47dd-ae0f-a7e9e1af4843">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/524_capheny/52414/spell3_bullet2" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n        <String name="syncAnimationName" value="" refParamName="" useRefParam="false" />\r\n        <String name="customTagName" value="" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="23514" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                                     

        if ID_SKIN == b"59802":
            if file_skill == "S2E6.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'<SkinOrAvatarList id="59802" />\r\n    </Track>',b'<SkinOrAvatarList id="59802" />\r\n    </Track>\r\n    <Track trackName="HitTriggerTick0" eventType="HitTriggerTick" guid="c30de0bb-1736-4aa9-a893-61284a36840f" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="HitTriggerTick" time="0.000" isDuration="false" guid="8ef533bc-5f75-41d4-9a7d-1cdddee37d42">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="hitTargetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <int name="SelfSkillCombineID_1" value="598999" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="59802" />\r\n    </Track>')
                with open(file_path,'wb') as f: f.write(sec)                     
            
        if ID_SKIN[:3] == b"171":   
            with open(file_path, 'rb') as f: rpl = f.read().replace(b'prefab_skill_effects/hero_skill_effects/171_zhangfei/1719_zhangfei', b'prefab_skill_effects/hero_skill_effects/171_zhangfei/' + ID_SKIN + b'/1719_zhangfei')
            with open(file_path,'wb') as f: f.write(rpl)                                                                       
                    
        if ID_SKIN == b"50119":        
            if file_skill == "A1B1.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticle6" eventType="TriggerParticle" guid="KM-MOD-AOV-ATK0102" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticle" time="0.000" length="3.000" isDuration="true" guid="add4f4d7-918e-4ba5-a4a9-8770e8eb58f6">\r\n        <TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_attack_01" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_attack_02" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n        <String name="syncAnimationName" value="" refParamName="" useRefParam="false" />\r\n        <String name="customTagName" value="" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n    <Track trackName="StopTrack5" eventType="StopTrack" guid="4fef95d4-2853-43f1-a4df-dfe675f3dd71" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Condition id="6" guid="09805859-49f5-4ed0-8a41-b9b2b75ce864" status="true" />\r\n      <Event eventName="StopTrack" time="0.000" isDuration="false" guid="8b053152-b11f-4352-b470-bb34f03d40e6">\r\n        <TrackObject name="trackId" id="0" guid="KM-MOD-AOV-ATK0102" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
 
            if file_skill == "A1E1.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="8a031d7e-f96d-435b-a1d0-555f6feb9017" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticleTick" time="0.000" isDuration="false" guid="dfce1419-2cc5-4726-9d28-7b51da34a0fc">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="target" id="1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/TelAnnas_attack_01_hurt01" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_attack_01_hurt_02" refParamName="" useRefParam="false" />\r\n        <float name="lifeTime" value="0.600" refParamName="" useRefParam="false" />\r\n        <bool name="bIsBindPosYRelateBeHitHeight" value="true" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="1" y="1" z="1" refParamName="" useRefParam="false" />\r\n        <bool name="bUseRealScaling" value="true" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="lookTargetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
 
            if file_skill == "A3B1.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticle6" eventType="TriggerParticle" guid="KM-MOD-AOV_ATK0102" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticle" time="0.000" length="3.000" isDuration="true" guid="c386bcf4-688e-4d95-8be8-c86f7c6d8ed9">\r\n        <TemplateObject name="targetId" objectName="bullet" id="2" isTemp="true" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_spell1_attack01" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_spell1_attack02" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n        <String name="syncAnimationName" value="" refParamName="" useRefParam="false" />\r\n        <String name="customTagName" value="" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n    <Track trackName="StopTrack5" eventType="StopTrack" guid="5c51ccc7-483b-4111-9267-6ada8b893c7b" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n      <Condition id="0" guid="09805859-49f5-4ed0-8a41-b9b2b75ce864" status="true" />\r\n      <Event eventName="StopTrack" time="0.000" isDuration="false" guid="ad90944c-4b25-436b-bfaf-5c40c2a0a7c4">\r\n        <TrackObject name="trackId" id="16" guid="KM-MOD-AOV_ATK0102" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
 
            if file_skill == "S1E3.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="1e46c82d-4af3-437b-875f-76bc5dbd2075" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticleTick" time="0.000" isDuration="false" guid="15864868-5229-4598-bc5a-f50fdf6979cb">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="target" id="1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_spell1_hurt01" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_spell1_hurt02" refParamName="" useRefParam="false" />\r\n        <float name="lifeTime" value="0.600" refParamName="" useRefParam="false" />\r\n        <bool name="bIsBindPosYRelateBeHitHeight" value="true" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="1" y="1" z="1" refParamName="" useRefParam="false" />\r\n        <bool name="bUseRealScaling" value="true" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="lookTargetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
 
            if file_skill in ["A1.xml", "A2.xml", "A3.xml", "A3_S.xml", "A4.xml", "A5.xml", "A6.xml"]:   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="f25d6410-e58f-4c09-991a-52d0a4aea13c" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticleTick" time="0.000" isDuration="false" guid="c5616c78-1973-42b5-910e-9c6cf4830d36">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_attack_weapon" refParamName="" useRefParam="false" />\r\n        <String name="resourceName2" value="prefab_skill_effects/hero_skill_effects/501_telannas/50119/telannas_attack_weapon_02" refParamName="" useRefParam="false" />\r\n        <String name="bindPointName" value="Bip001 Prop1" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n        <bool name="applyActionSpeedToAnimation" value="true" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50119" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN == b"50120":
            if file_skill in ["A1E1.xml"]:   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="4865d04e-8eff-42ae-8209-702369ac306a" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="TriggerParticleTick" time="0.000" isDuration="false" guid="1d6be983-69c9-42bb-b647-cb92cfe9815f">\r\n        <TemplateObject name="targetId" objectName="None" id="-1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" objectName="target" id="1" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/501_telannas/50120/telannas_hurt_spell03" refParamName="" useRefParam="false" />\r\n        <float name="lifeTime" value="0.600" refParamName="" useRefParam="false" />\r\n        <bool name="bIsBindPosYRelateBeHitHeight" value="true" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="1" y="1" z="1" refParamName="" useRefParam="false" />\r\n        <bool name="bUseRealScaling" value="true" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="lookTargetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="50120" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     
                     
        if ID_SKIN in [b"11119", b"11120"]:                   
            if file_skill in ["A1B1.xml"]:                                
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b'<Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="\xe9\x83\x91\xe5\x87\xaf\xe6\x98\x8e" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n<Event eventName="SpawnLiteObjDuration" time="0.000" length="0.500" isDuration="true" guid="6d868a6f-8ee5-477f-b215-8168ab03ce28">\r\n<String name="OutputLiteBulletName" value="111a1b1" refParamName="" useRefParam="false" />\r\n<uint name="ConfigID" value="11100" refParamName="" useRefParam="false" />\r\n<TemplateObject name="ReferenceID" id="0" objectName="\xe6\x94\xbb\xe5\x87\xbb\xe8\x80\x85" isTemp="false" refParamName="" useRefParam="false" />\r\n<TemplateObject name="TargetID" id="1" objectName="target" isTemp="false" refParamName="" useRefParam="false" />\r\n</Event>\r\n<SkinOrAvatarList id="11119" />\r\n<SkinOrAvatarList id="11120" />\r\n</Track>\r\n</Action>')
                with open(file_path,'wb') as f: f.write(sec)                               

            if file_skill in ["A1b2.xml"]:                                
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b'<Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="\xe9\x83\x91\xe5\x87\xaf\xe6\x98\x8e" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n<Event eventName="SpawnLiteObjDuration" time="0.000" length="0.200" isDuration="true" guid="6d868a6f-8ee5-477f-b215-8168ab03ce28">\r\n<String name="OutputLiteBulletName" value="111a1b2" refParamName="" useRefParam="false" />\r\n<uint name="ConfigID" value="111002" refParamName="" useRefParam="false" />\r\n<TemplateObject name="ReferenceID" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n<TemplateObject name="TargetID" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n</Event>\r\n<SkinOrAvatarList id="11119" />\r\n<SkinOrAvatarList id="11120" />\r\n</Track>\r\n</Action>')
                with open(file_path,'wb') as f: f.write(sec)                               
                
            if file_skill in ["A2B1.xml"]:                                
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b'<Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="\xe9\x83\x91\xe5\x87\xaf\xe6\x98\x8e" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n<Event eventName="SpawnLiteObjDuration" time="0.000" length="0.500" isDuration="true" guid="6d868a6f-8ee5-477f-b215-8168ab03ce28">\r\n<String name="OutputLiteBulletName" value="111a2b1" refParamName="" useRefParam="false" />\r\n<uint name="ConfigID" value="11101" refParamName="" useRefParam="false" />\r\n<TemplateObject name="ReferenceID" id="0" objectName="\xe6\x94\xbb\xe5\x87\xbb\xe8\x80\x85" isTemp="false" refParamName="" useRefParam="false" />\r\n<TemplateObject name="TargetID" id="1" objectName="target" isTemp="false" refParamName="" useRefParam="false" />\r\n</Event>\r\n<SkinOrAvatarList id="11119" />\r\n<SkinOrAvatarList id="11120" />\r\n</Track>\r\n</Action>')
                with open(file_path,'wb') as f: f.write(sec) 

            if file_skill in ["A2b2.xml"]:                                
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b'<Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="\xe9\x83\x91\xe5\x87\xaf\xe6\x98\x8e" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n<Event eventName="SpawnLiteObjDuration" time="0.000" length="0.200" isDuration="true" guid="6d868a6f-8ee5-477f-b215-8168ab03ce28">\r\n<String name="OutputLiteBulletName" value="111a2b2" refParamName="" useRefParam="false" />\r\n<uint name="ConfigID" value="111012" refParamName="" useRefParam="false" />\r\n<TemplateObject name="ReferenceID" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n<TemplateObject name="TargetID" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n</Event>\r\n<SkinOrAvatarList id="11119" />\r\n<SkinOrAvatarList id="11120" />\r\n</Track>\r\n</Action>')
                with open(file_path,'wb') as f: f.write(sec) 
                              
            if file_skill in ["A4B1.xml"]:                                
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b'<Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="\xe9\x83\x91\xe5\x87\xaf\xe6\x98\x8e" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n<Event eventName="SpawnLiteObjDuration" time="0.000" length="0.500" isDuration="true" guid="6d868a6f-8ee5-477f-b215-8168ab03ce28">\r\n<String name="OutputLiteBulletName" value="111a4b1" refParamName="" useRefParam="false" />\r\n<uint name="ConfigID" value="11102" refParamName="" useRefParam="false" />\r\n<TemplateObject name="ReferenceID" id="0" objectName="\xe6\x94\xbb\xe5\x87\xbb\xe8\x80\x85" isTemp="false" refParamName="" useRefParam="false" />\r\n<TemplateObject name="TargetID" id="1" objectName="target" isTemp="false" refParamName="" useRefParam="false" />\r\n</Event>\r\n<SkinOrAvatarList id="11119" />\r\n<SkinOrAvatarList id="11120" />\r\n</Track>\r\n</Action>')
                with open(file_path,'wb') as f: f.write(sec)          

            if file_skill in ["A4b2.xml"]:                                
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b'<Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="\xe9\x83\x91\xe5\x87\xaf\xe6\x98\x8e" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="11">\r\n<Event eventName="SpawnLiteObjDuration" time="0.000" length="0.200" isDuration="true" guid="6d868a6f-8ee5-477f-b215-8168ab03ce28">\r\n<String name="OutputLiteBulletName" value="111a4b2" refParamName="" useRefParam="false" />\r\n<uint name="ConfigID" value="111022" refParamName="" useRefParam="false" />\r\n<TemplateObject name="ReferenceID" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n<TemplateObject name="TargetID" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n</Event>\r\n<SkinOrAvatarList id="11119" />\r\n<SkinOrAvatarList id="11120" />\r\n</Track>\r\n</Action>')
                with open(file_path,'wb') as f: f.write(sec)          
                
        if ID_SKIN == b"13314":
            with open(file_path, 'rb') as f: sec = f.read().replace(b'prefab_characters/prefab_hero/133_DiRenJie/DiRenJie_spell03_cutin01', b'prefab_skill_effects/hero_skill_effects/133_DiRenJie/13314/DiRenJie_spell03_cutin01')
            with open(file_path,'wb') as f: f.write(sec)              
                                        
            if file_skill == "Death.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b' <Track trackName="SetObjectDirectionTick0" eventType="SetObjectDirectionTick" guid="887eb67f-101d-4820-a6f3-89fb91f299d6" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false">\r\n      <Event eventName="SetObjectDirectionTick" time="0.000" isDuration="false" guid="0dee70b1-71dd-4ef2-ada6-633b94a67537">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <int name="rotationY" value="15" refParamName="" useRefParam="false" />\r\n      </Event>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                                   
                                                                                                 
                                      
        if ID_SKIN == b"51015":
            if file_skill == "Death.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'</Action>', b' <Track trackName="SetObjectDirectionTick1" eventType="SetObjectDirectionTick" guid="351eb169-b371-42e3-bfb3-40e1617aa2e3" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true" SkinAvatarFilterType="9">\r\n      <Event eventName="SetObjectDirectionTick" time="0.000" isDuration="false" guid="7f276ac3-57b2-4692-9549-1d0acb347f8d">\r\n        <TemplateObject name="targetId" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <int name="rotationY" value="180" refParamName="" useRefParam="false" />\r\n      </Event>\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN == b"13213":     
            if file_skill in ["S1B0.xml"]:
                with open(file_path, 'rb') as f:
                    rpl = f.read()
                tracks = rpl.split(b"</Track>")
                modified_tracks = []
                for track in tracks:
                    if b'<SkinOrAvatarList id="13213" />' in track:
                        if (b'PlayAnimDuration' in track):
                            track = (track.replace(b'SkinAvatarFilterType="9">', b'SkinAvatarFilterType="8">').replace(b'SkinAvatarFilterType="11">', b'SkinAvatarFilterType="9">').replace(b'SkinAvatarFilterType="8">', b'SkinAvatarFilterType="11">').replace(b'<SkinOrAvatarList id="' + ID_SKIN + b'" />',b'<SkinOrAvatarList id="235' + ID_SKIN[-2:] + b'" />'))
                            modified_tracks.append(track + b"</Track>")
                        else:
                            modified_tracks.append(track + b"</Track>")      
                    else:                                                              
                        modified_tracks.append(track + b"</Track>")                                
                rpl = b"".join(modified_tracks)    
                if rpl.endswith(b"</Track>"):
                    rpl = rpl[:-8]                            
                with open(file_path, 'wb') as f:
                    f.write(rpl)       
                    
            if file_skill == "S1B1.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', _blob("KAITOS1B1"))
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN in [b"13210", b"13215"]:     
            with open(file_path, 'rb') as f: sec = f.read().replace(b"""<bool name="useNegateValue" value="true" refParamName="" useRefParam="false" />\r\n        <Array name="skinIdArray" refParamName="" useRefParam="false" type="int">\r\n          <int value="13210" />\r\n          <int value="13215" />""", b"""<bool name="useNegateValue" value="false" refParamName="" useRefParam="false" />\r\n        <Array name="skinIdArray" refParamName="" useRefParam="false" type="int">\r\n          <int value="99999" />""").replace(b"""<bool name="useNegateValue" value="true" refParamName="" useRefParam="false" />\r\n        <Array name="skinIdArray" refParamName="" useRefParam="false" type="int">\r\n          <int value="13215" />\r\n          <int value="13210" />""", b"""<bool name="useNegateValue" value="false" refParamName="" useRefParam="false" />\r\n        <Array name="skinIdArray" refParamName="" useRefParam="false" type="int">\r\n          <int value="99999" />""")
            with open(file_path,'wb') as f: f.write(sec)                     
                
        if ID_SKIN == b"11215":                        
            if file_skill == "S1B1.xml":   
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>', b'    <Track trackName="SpawnLiteObjDuration0" eventType="SpawnLiteObjDuration" guid="c890e4ed-8300-4e21-8d66-757283ec3cc0" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" SkinAvatarFilterType="11">\r\n      <Event eventName="SpawnLiteObjDuration" time="0.000" length="0.571" isDuration="true" guid="36200992-6a48-47a7-95c6-c2e352151ff4">\r\n        <String name="OutputLiteBulletName" value="112s1b1" refParamName="" useRefParam="false" />\r\n        <uint name="ConfigID" value="11215235" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="ReferenceID" objectName="self" id="0" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="TargetID" objectName="bullet" id="2" isTemp="false" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      <SkinOrAvatarList id="11215" />\r\n    </Track>\r\n  </Action>')
                with open(file_path,'wb') as f: f.write(sec)                     

        if ID_SKIN == b"14002":
            if file_skill in ["S1B1.xml", "S2B1.xml"]:
                with open(file_path, 'rb') as f: sec = f.read().replace(b'hero_skill_effects/140_guanyu/14002/',b'hero_skill_effects/140_guanyu/')
                with open(file_path,'wb') as f: f.write(sec)
            
        with open(file_path, 'rb') as f:
            rpl = f.read()
        tracks = rpl.split(b"</Track>")
        modified_tracks = []
        for track in tracks:
            if (b'SkinAvatarFilterType="9"' in track and b'<SkinOrAvatarList id="235' in track and b'prefab_skill_effects' in track):
                track = track.replace(b'/' + ID_SKIN + b'/', b'/')
            modified_tracks.append(track)
        rpl = b"</Track>".join(modified_tracks)
        with open(file_path, 'wb') as f:
            f.write(rpl)
            
        if file_skill in ["Death.xml"]:               
            with open(file_path, 'rb') as f:
                rpl = f.read()
            tracks = rpl.split(b"</Track>")
            modified_tracks = []
            for track in tracks:
                if (b'<SkinOrAvatarList id="' + ID_SKIN[:3] in track and b'<SkinOrAvatarList id="' + ID_SKIN not in track):
                    if (b'PlayAnimationTick' in track):
                        track = (track.replace(b'<SkinOrAvatarList id="' + ID_SKIN[:3], b'<SkinOrAvatarList id="235'))
                        modified_tracks.append(track + b"</Track>")
                    else:                                                                                      
                        modified_tracks.append(track + b"</Track>")
                else:                                                              
                    modified_tracks.append(track + b"</Track>")                         
            rpl = b"".join(modified_tracks)    
            if rpl.endswith(b"</Track>"):
                rpl = rpl[:-8]                            
            with open(file_path, 'wb') as f:
                f.write(rpl)

        '''if ID_SKIN == b"15009":
            if file_skill == "S1.xml":
                with open(file_path, 'rb') as f: sec = f.read().replace(b'  </Action>\r\n</Project>', b'    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="0dd50bba-7a9f-42e5-9e07-36682560346a" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">\r\n      <Event eventName="TriggerParticleTick" time="0.133" isDuration="false" guid="739356cc-bba5-4e21-be19-1864beab3928">\r\n        <TemplateObject name="targetId" id="-1" objectName="None" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/150_hanxin/15009/hanxin_attack01_spell06" refParamName="" useRefParam="false" />\r\n        <float name="lifeTime" value="2.000" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      </Track>\r\n    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="0dd50bba-7a9f-42e5-9e07-36682560346a" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">\r\n      <Event eventName="TriggerParticleTick" time="0.133" isDuration="false" guid="739356cc-bba5-4e21-be19-1864beab3928">\r\n        <TemplateObject name="targetId" id="-1" objectName="None" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/518_Quillen/51809/jingke_attack_04" refParamName="" useRefParam="false" />\r\n        <Vector3 name="scaling" x="1.000" y="1.000" z="1.000" refParamName="" useRefParam="false" />\r\n        <Vector3 name="bindPosOffset" x="-1.000" y="2.800" z="1.300" refParamName="" useRefParam="false"/>\r\n        <EulerAngle name="bindRotOffset" x="-100.000" y="0.000" z="-100.000" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n        <bool name="bUseRealScaling" value="true" refParamName="" useRefParam="false" />\r\n        <bool name="applyActionSpeedToAnimation" value="true" refParamName="" useRefParam="false" />\r\n      </Event>\r\n      </Track>\r\n    <Track trackName="TriggerParticleTick0" eventType="TriggerParticleTick" guid="0dd50bba-7a9f-42e5-9e07-36682560346a" enabled="true" useRefParam="false" refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" execOnActionCompleted="false" stopAfterLastEvent="true">\r\n      <Event eventName="TriggerParticleTick" time="0.133" isDuration="false" guid="739356cc-bba5-4e21-be19-1864beab3928">\r\n        <TemplateObject name="targetId" id="-1" objectName="None" isTemp="false" refParamName="" useRefParam="false" />\r\n        <TemplateObject name="objectSpaceId" id="0" objectName="self" isTemp="false" refParamName="" useRefParam="false" />\r\n        <String name="resourceName" value="prefab_skill_effects/hero_skill_effects/518_Quillen/51809/jingke_attack_04" refParamName="" useRefParam="false" />\r\n        <Vector3 name="scaling" x="1.000" y="1.000" z="1.000" refParamName="" useRefParam="false" />\r\n        <Vector3 name="bindPosOffset" x="-1.000" y="2.800" z="1.300" refParamName="" useRefParam="false"/>\r\n        <EulerAngle name="bindRotOffset" x="-280.000" y="0.000" z="-100.000" refParamName="" useRefParam="false" />\r\n        <Vector3i name="scalingInt" x="10000" y="10000" z="10000" refParamName="" useRefParam="false" />\r\n        <bool name="bUseRealScaling" value="true" refParamName="" useRefParam="false" />\r\n        <bool name="applyActionSpeedToAnimation" value="true" refParamName="" useRefParam="false" />\r\n      </Event>\r\n    </Track>\r\n  </Action>\r\n</Project>')
                with open(file_path,'wb') as f: f.write(sec)'''
                
        '''if ID_SKIN[:3] == b"521":
            if file_skill in ["S1B2.xml", "S1B3.xml", "S1B4.xml"]:
                with open(file_path, "rb") as f:
                    sec = f.read()
                add_data = (f'\r\n        <Vector3 name="scaling" x="{kich_thuoc}" y="{kich_thuoc}" z="{kich_thuoc}" refParamName="" useRefParam="false" />\r\n        <bool name="bUseRealScaling" value="true" refParamName="" useRefParam="false" />').encode()
                for effect in [b"Florentino_spell01_bullet03",b"Florentino_spell01_bullet03_e"]:
                    old = effect + b'" refParamName="" useRefParam="false" />'
                    new = old + add_data
                    sec = sec.replace(old, new)
                with open(file_path, "wb") as f:
                    f.write(sec)'''
