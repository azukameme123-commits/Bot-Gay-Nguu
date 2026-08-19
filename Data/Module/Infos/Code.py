import os
import re

def EfxInfosPhu(ID_SKIN, files):
    ID_SKIN = ID_SKIN.encode()
    with open(files, 'rb') as f:
        code = f.read()
        list_code = code.split(b'\r\n')

    for i in list_code:
        if b'prefab_skill_effects' in i.lower():
            i1 = i.split(b'/')
            if len(i1) == 5:
                i2 = i.replace(i1[2], i1[2] + b'/' + ID_SKIN)
                code = code.replace(i, i2)
            if len(i1) == 6:
                i2 = i.replace(i1[3], ID_SKIN)
                code = code.replace(i, i2)

    code = (
        code.replace(b'_LOD1', b'_LOD1.prefab')
            .replace(b'_LOD2', b'_LOD1.prefab')
            .replace(b'_LOD3', b'_LOD1.prefab')
    )

    with open(files, 'wb') as f:
        f.write(code)
        
def EfxAnimInfos(file_path, ID_SKIN, ID_HD, NAME_HERO, ALL_CODE_GOC):
    lines = ALL_CODE_GOC.split('\n')
    new_lines = []

    for line in lines:
        if "hero_skill_effects" in line.lower():

            if f"hero_skill_effects/{NAME_HERO}/{ID_SKIN}/" not in line:
                pattern = rf"(hero_skill_effects/{re.escape(NAME_HERO)}/)(?!{re.escape(ID_SKIN)}/)"
                line = re.sub(
                    pattern,
                    lambda m: m.group(1) + ID_SKIN + "/",
                    line,
                    flags=re.IGNORECASE
                )

            line = line.replace("Assets/Prefabs/", "")
            line = line.replace("Hero_Skill_Effects/Hero_Skill_Effects/", "Hero_Skill_Effects/")
            line = line.replace(f"/{ID_SKIN}/{ID_SKIN}/", f"/{ID_SKIN}/")
            if 'value="' in line and '.prefab"' not in line:
                if ID_SKIN in ID_HD:
                    line = re.sub(
                        r'(value="[^"]+?)(?=")',
                        r'\1_HD',
                        line
                    )
                    
                else:
                    line = re.sub(
                        r'(value="[^"]+?)(?=")',
                        r'\1.prefab',
                        line
                    )

        new_lines.append(line)

    return '\n'.join(new_lines)
    
def ModInfos(ID_INFO, ID_EFF, ID_HD, NAME_HERO, file_path, phukienbutter, phukienveres):
    with open(file_path, 'r',  encoding="utf-8") as file:
        ALL_CODE_GOC = file.read()
        STAR_END = re.compile(r'\n    <Element var="Com" type="Assets.Scripts.GameLogic.SkinElement">.*?\n    </Element>', re.DOTALL)
        DOAN_CODE = STAR_END.findall(ALL_CODE_GOC)
        if ID_INFO == "1505":
            A = [x for x in DOAN_CODE if re.search(rf'/15033_.*?LOD', x, re.IGNORECASE) and re.search(rf'/15033_.*?_Show1', x, re.IGNORECASE)]
        else:
            A = [x for x in DOAN_CODE if f'/{ID_INFO}_' in x]
        if len(A) != 0:
            code_skin_mod = A[0]
            if ID_INFO == '13312':
                code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/133_DiRenJie/13312_DiRenJie_AW1_', 'Prefab_Characters/Prefab_Hero/133_DiRenJie/awaken/13312_DiRenJie_04_').replace('Prefab_Characters/Prefab_Hero/133_DiRenJie/1331_DiRenJie_Cam', 'Prefab_Characters/Prefab_Hero/133_DiRenJie/awaken/13312_DiRenJie_aw5_Cam')
            if ID_INFO == '1505':
                code_skin_mod = code_skin_mod.replace('15033_HanXin_AW1', '15033_HanXin_AW5')
            if ID_INFO == '1678':
                code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/167_WuKong/1678_SunWuKong_AW1_Cam"/>', 'Prefab_Characters/Prefab_Hero/167_WuKong/Awaken/1678_SunWuKong_03_Cam"/>\n  <ArtSkinLobbyShowMovie var="String" type="System.String" value="Prefab_Characters/Prefab_Hero/167_WuKong/Awaken/1678_SunWuKong_03_Movie"/>').replace('Prefab_Characters/Prefab_Hero/167_WuKong/1678_SunWuKong_AW1_', 'Prefab_Characters/Prefab_Hero/167_WuKong/Awaken/1678_SunWuKong_03_').replace('prefab_skill_effects/hero_skill_effects/167_WuKong/', 'prefab_skill_effects/component_effects/16707/16707_5/')
            if ID_INFO == '11621':
                if phukienbutter == "1":
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_AW1_Cam"/>', 'Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_AW5_Cam"/>\n  <ArtSkinLobbyShowMovie var="String" type="System.String" value="Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_Movie"/>').replace('Prefab_Characters/Prefab_Hero/116_JingKe/11621_JingKe_AW1_', 'Prefab_Characters/Prefab_Hero/116_JingKe/Component/11621_JingKe_RT_2_')
                if phukienbutter == "2":
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_AW1_Cam"/>', 'Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_AW5_Cam"/>\n  <ArtSkinLobbyShowMovie var="String" type="System.String" value="Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_Movie"/>').replace('Prefab_Characters/Prefab_Hero/116_JingKe/11621_JingKe_AW1_', 'Prefab_Characters/Prefab_Hero/116_JingKe/Component/11621_JingKe_RT_3_')
                else:
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_AW1_Cam"/>', 'Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_AW5_Cam"/>\n  <ArtSkinLobbyShowMovie var="String" type="System.String" value="Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_Movie"/>').replace('Prefab_Characters/Prefab_Hero/116_JingKe/11621_JingKe_AW1_', 'Prefab_Characters/Prefab_Hero/116_JingKe/Awaken/11621_JingKe_04_')
            if ID_INFO == '5208':
                if phukienveres == "1":
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/520_Veres/5208_Veres_LOD', 'Prefab_Characters/Prefab_Hero/520_Veres/Component/5208_Veres_RT_2_LOD').replace('Prefab_Characters/Prefab_Hero/520_Veres/5208_Veres_Show', 'Prefab_Characters/Prefab_Hero/520_Veres/Component/5208_Veres_RT_2_Show')
                if phukienveres == "2":
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/520_Veres/5208_Veres_LOD', 'Prefab_Characters/Prefab_Hero/520_Veres/Component/5208_Veres_RT_3_LOD').replace('Prefab_Characters/Prefab_Hero/520_Veres/5208_Veres_Show', 'Prefab_Characters/Prefab_Hero/520_Veres/Component/5208_Veres_RT_3_Show')      
            if ID_INFO == '1575':
                phukienraz = '2' #input('\033[1;97m[\033[1;91m?\033[1;97m] Mod Component Infos:\n\033[1;97m [1] \033[1;92mYes\n\033[1;97m [2] \033[1;92mNo\n\033[1;97m[•] INPUT: ')                  
                if phukienraz == "1":
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/157_BuZhiHuoWu/1575_BuZhiHuoWu_LOD', 'Prefab_Characters/Prefab_Hero/157_BuZhiHuoWu/Component/1575_BuZhiHuoWu_RT_2_LOD').replace('Prefab_Characters/Prefab_Hero/157_BuZhiHuoWu/1575_BuZhiHuoWu_Show', 'Prefab_Characters/Prefab_Hero/157_BuZhiHuoWu/Component/1575_BuZhiHuoWu_RT_2_Show')                
            if ID_INFO == '10710':
                phukienzephys = '2' #input('\033[1;97m[\033[1;91m?\033[1;97m] Mod Component Infos:\n\033[1;97m [1] \033[1;92mYes\n\033[1;97m [2] \033[1;92mNo\n\033[1;97m[•] INPUT: ')                                             
                if phukienzephys == "1":
                    code_skin_mod = code_skin_mod.replace('Prefab_Characters/Prefab_Hero/107_ZhaoYun/10710_Zhaoyun_LOD', 'Prefab_Characters/Prefab_Hero/107_Zhaoyun/Component/10710_Zhaoyun_RT_2_LOD').replace('Prefab_Characters/Prefab_Hero/107_ZhaoYun/10710_ZhaoYun_Show', 'Prefab_Characters/Prefab_Hero/107_Zhaoyun/Component/10710_Zhaoyun_RT_2_Show')                
            code_skin_mod = code_skin_mod.replace('_LOD1', '_LOD1.prefab').replace('_LOD2', '_LOD1.prefab').replace('_LOD3', '_LOD1.prefab').replace('Show1"/>', 'Show1.prefab"/>').replace('Show2"/>', 'Show1.prefab"/>').replace('Show3"/>', 'Show1.prefab"/>').replace('_lod1', '_LOD1.prefab').replace('_lod2', '_LOD1.prefab').replace('_lod3', '_LOD1.prefab').replace('show1"/>', 'show1.prefab"/>').replace('show2"/>', 'show1.prefab"/>').replace('show3"/>', 'show1.prefab"/>')
            if ID_INFO == "5208":
                if phukienveres in ["1"]:
                	code_skin_mod = code_skin_mod.replace('_LOD1', '_LOD2')
                	
            B = [x for x in DOAN_CODE if f'/{ID_INFO[:3]}' in x]
            for codeskinphu in B:
                if '<SavedSkinId var="String"' in codeskinphu:
                    for saveskin in codeskinphu.split('\n'):
                        if '<SavedSkinId var="String"' in saveskin:
                            code_skin_mod_save = code_skin_mod.replace('GameLogic.SkinElement">', 'GameLogic.SkinElement">\n' + saveskin) 
                            ALL_CODE_GOC = ALL_CODE_GOC.replace(codeskinphu, code_skin_mod_save)                            
                else:
                    ALL_CODE_GOC = ALL_CODE_GOC.replace(codeskinphu, code_skin_mod)
                    
            STAR_END_MD = re.compile(r'\n  <ArtPrefabLOD var="Array" type="System\.String\[\]">.*?\n  <SkinPrefab var="Array" type="Assets\.Scripts\.GameLogic\.SkinElement\[\]">', re.DOTALL)
            DOAN_CODE_MD = STAR_END_MD.findall(ALL_CODE_GOC)
            if len(DOAN_CODE_MD) != 0:
                Skin_md = DOAN_CODE_MD[0].replace('\n  <SkinPrefab var="Array" type="Assets.Scripts.GameLogic.SkinElement[]">','')
                code_skin_mod_md = code_skin_mod.replace('\n    <Element var="Com" type="Assets.Scripts.GameLogic.SkinElement">','').replace('\n    </Element>', '').replace('ArtSkinPrefabLOD', 'ArtPrefabLOD').replace('ArtSkinPrefabLODEx', 'ArtPrefabLODEx').replace('ArtSkinLobbyShowLOD', 'ArtLobbyShowLOD').replace('ArtSkinLobbyIdleShowLOD', 'ArtLobbyIdleShowLOD').replace('      <', '  <').replace('        <', '    <').replace('          <', '      <')
                ALL_CODE_GOC = ALL_CODE_GOC.replace(Skin_md, code_skin_mod_md)
            if 'hero_skill_effects' in code_skin_mod.lower() and ID_INFO not in ['13312', '1678']:
                ALL_CODE_GOC = EfxAnimInfos(file_path, ID_EFF, ID_HD, NAME_HERO, ALL_CODE_GOC)
    with open(file_path, 'w', encoding="utf-8") as file: 
        file.write(ALL_CODE_GOC)
        
def FixCodeInfos(file_path, ID_SKIN, ID_INFO):        
    with open(file_path, 'rb') as f:
        data = f.read()

    if ID_SKIN in ["19015", "19016"]:
        data = data.replace(b'\n  <useMecanim var="String" type="System.Boolean" value="True"/>',b'')
    if ID_SKIN in ["54805", "17408"]:
        data = data.replace(b'\n  <useNewMecanim var="String" type="System.Boolean" value="True"/>',b'')
    if ID_SKIN == "54402":
        data = data.replace(b'</ArtLobbyIdleShowLOD>',b'</ArtLobbyIdleShowLOD>\r\n  <CrossFadeTime var="String" type="System.Single" value="0"/>\r\n  <TransConfigs var="Array" type="Assets.Scripts.GameLogic.TransformConfig[]">\r\n    <Element var="Com" type="Assets.Scripts.GameLogic.TransformConfig"/>\r\n    <Element var="Com" type="Assets.Scripts.GameLogic.TransformConfig">\r\n      <Scale var="String" type="System.Single" value="1.2"/>\r\n    </Element>\r\n  </TransConfigs>')
    if ID_SKIN == "19908":
        data = data.replace(b'Assets/Art_Resources/Characters/Hero/199_Li/Ani/1999/',b'prefab_skill_effects/hero_skill_effects/199_Li/19908/')
        
    data = re.sub(rb'<ActorName var="String" type="System.String" value=".*?"/>', b'<ActorName var="String" type="System.String" value="MOD BY: KM MOD AOV \x54\x68\xE1\xBA\xB1\x6E\x67\x20\x4E\xC3\xA0\x6F\x20\xC4\x82\x6E\x20\x43\xE1\xBA\xAF\x70\x20\x4C\xC3\xA0\x6D\x20\x43\x68\xC3\xB3"/>', data)
    data = data.replace(b'<SkinPrefab', b'<MSAA var="Enum" type="Assets.Scripts.GameLogic.EAntiAliasing" value="4"/>\r\n  <SkinPrefab').replace(b'    </Element>\r\n    <Element var="Com"', b'      <MSAA var="Enum" type="Assets.Scripts.GameLogic.EAntiAliasing" value="4"/>\r\n    </Element>\r\n    <Element var="Com"').replace(b'<MSAA var="Enum" type="Assets.Scripts.GameLogic.EAntiAliasing" value="0"/>', b'<MSAA var="Enum" type="Assets.Scripts.GameLogic.EAntiAliasing" value="4"/>').replace(b'<MSAA var="Enum" type="Assets.Scripts.GameLogic.EAntiAliasing" value="2"/>', b'<MSAA var="Enum" type="Assets.Scripts.GameLogic.EAntiAliasing" value="4"/>')
    
    if ID_INFO in ['5373', '5458', '5485', '1843', '1845', '1846', '1847', '1848', '1849', '5343', '5346', '5482', '5483', '5484', '5372', '11611', '11612', '5393', '5394', '5395', '5353', '5355', '5359', '5363', '5366', '5367', '5369', '53610']:
        data = data.replace(b'<bUnityLight var="String" type="System.Boolean" value="True"/>', b'<bUnityLight var="String" type="System.Boolean" value="False"/>')

    if ID_SKIN == "52102":
        modinfoslinh = input(" Mod Ngoại Hình Lính (y/n): ")
        if modinfoslinh.lower() == "y":
            data = data.replace(b'Prefab_Characters/Prefab_Hero/521_Florentino/5213_Florentino_LOD1', b'Prefab_Characters/Prefab_Soldier/New_MeleeSoldier/New_MeleeSoldier_LOD1').replace(b'<Scale var="String" type="System.Single" value="1.06"/>', b'<Scale var="String" type="System.Single" value="1.3"/>')
               
    with open(file_path, 'wb') as f:
        f.write(data)
