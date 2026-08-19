import os
import re
import json

def Mod_Skill_Databin(ID_EFF, ID_HD, liteBulletCfg1, skillmark1):
    ID_SKIN = str(ID_EFF)
    prefix = ID_SKIN[:3] + "_"

    with open(liteBulletCfg1, "r", encoding="utf-8") as f:
        data = json.load(f)

    if ID_SKIN in ["11215"]:
        data.append({
        "ConfigID": 11215235,
        "bMoveType": 0,
        "Name": "112s1b1",
        "MoveSpeed": 15000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 50,
                "Z": 0
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 0,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1150,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/112_gongshuban/gongshuban_attack01_spell01"
    })

    if ID_SKIN in ["11119", "11120"]:
        data.extend([{
        "ConfigID": 11100,
        "bMoveType": 0,
        "Name": "111a1b1",
        "MoveSpeed": 35000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 800,
                "Z": 0
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 0,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1000,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/111_sunshangxiang/sunshangxiang_fly_01b"
    },
    {
        "ConfigID": 111002,
        "bMoveType": 0,
        "Name": "111a1b2",
        "MoveSpeed": 35000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 800,
                "Z": -30000
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 1,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 30000
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1000,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/111_sunshangxiang/sunshangxiang_fly_01b"
    },
    {
        "ConfigID": 11101,
        "bMoveType": 0,
        "Name": "111a2b1",
        "MoveSpeed": 35000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 0,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1000,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/111_sunshangxiang/sunshangxiang_fly_01b"
    },
    {
        "ConfigID": 111012,
        "bMoveType": 0,
        "Name": "111a2b2",
        "MoveSpeed": 35000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 750,
                "Z": -30000
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 1,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 30000
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1000,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/111_sunshangxiang/sunshangxiang_fly_01b"
    },
    {
        "ConfigID": 11102,
        "bMoveType": 0,
        "Name": "111a4b1",
        "MoveSpeed": 35000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 750,
                "Z": 0
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 0,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1000,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/111_sunshangxiang/sunshangxiang_attack01_C"
    },
    {
        "ConfigID": 111022,
        "bMoveType": 0,
        "Name": "111a4b2",
        "MoveSpeed": 35000,
        "Acceleration": 0,
        "bIsModifyTranslation": 1,
        "ModifyTranslation": [
            {
                "X": 0,
                "Y": 750,
                "Z": -30000
            }
        ],
        "bIsModifyDirection": 1,
        "bModifyDirType": 0,
        "bIsMoveRotate": 1,
        "bHitPointType": 0,
        "bIsIgnoreHeight": 1,
        "bIsLockY": 1,
        "bIsIgnoreCharCollisionSize": 0,
        "bIsDelayLeave": 0,
        "BindPosOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 30000
            }
        ],
        "BindRotOffset": [
            {
                "X": 0,
                "Y": 0,
                "Z": 0
            }
        ],
        "Scale": [
            {
                "X": 1000,
                "Y": 1000,
                "Z": 1000
            }
        ],
        "PrefabPath": "prefab_skill_effects/hero_skill_effects/111_sunshangxiang/sunshangxiang_attack01_C"
    }])
    
    with open(liteBulletCfg1, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    try:
        with open(liteBulletCfg1, "r", encoding="utf-8") as f:
            data = json.load(f)

        modified = 0

        for item in data:
            prefab = item.get("PrefabPath")
            if not prefab:
                continue

            if prefix not in prefab:
                continue

            parts = prefab.split("/")

            if len(parts) < 2:
                continue

            if ID_SKIN in ID_HD:
                new_prefab = (
                    f"{'/'.join(parts[:-1])}/{ID_SKIN}/{parts[-1]}_HD"
                ).lower()
            else:
                new_prefab = (
                    f"{'/'.join(parts[:-1])}/{ID_SKIN}/{parts[-1]}.prefab"
                ).lower()

            if new_prefab != prefab:
                item["PrefabPath"] = new_prefab
                modified += 1

        if modified:
            with open(liteBulletCfg1, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"Lỗi: {e}")

    try:
        with open(skillmark1, "r", encoding="utf-8") as f:
            data = json.load(f)

        modified = 0

        for item in data:
            cfg_id = str(item.get("CfgID", ""))

            if not cfg_id.startswith(ID_SKIN[:3]):
                continue

            effects = item.get("LayerEffectName")

            if not isinstance(effects, list):
                continue

            for i, effect in enumerate(effects):
                if not effect or prefix not in effect:
                    continue

                folder, name = effect.rsplit("/", 1)

                if ID_SKIN in ID_HD:
                    new_effect = (
                        f"{folder}/{ID_SKIN}/{name}_HD"
                    ).lower()
                else:
                    new_effect = (
                        f"{folder}/{ID_SKIN}/{name}.prefab"
                    ).lower()

                if new_effect != effect:
                    effects[i] = new_effect
                    modified += 1

        if modified:
            with open(skillmark1, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        print(f"Lỗi: {e}")
      
def Add_SkillCombineId(ID_SKIN, skillcombine):
    with open(skillcombine, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if ID_SKIN in ["13213"]:
        data.extend([{
        "CfgID": 132235,
        "bMapSkillCombineUseRuleID": 100,
        "OverlayRule": 1,
        "OverlayMax": 1,
        "SkillCombineDesc": "94BB57718F6CA746_##",
        "Prefab": "Prefab_Characters/Prefab_Hero/141_DiaoChan/skill/Change",
        "Duration": -1,
        "bAgeImmeExcute": True,
        "ExtraEffectSlotType": -1,
        "TargetMarkerSlotType": -1,
        "UnknownI4": 10000
    },
    {
        "CfgID": 132123,
        "bMapSkillCombineUseRuleID": 100,
        "OverlayRule": 1,
        "OverlayMax": 1,
        "SkillCombineDesc": "94BB57718F6CA746_##",
        "Prefab": "Prefab_Characters/Prefab_Hero/141_DiaoChan/skill/Change",
        "Duration": -1,
        "bAgeImmeExcute": True,
        "ExtraEffectSlotType": -1,
        "TargetMarkerSlotType": -1,
        "UnknownI4": 10000
    },
    {
        "CfgID": 132456,
        "bMapSkillCombineUseRuleID": 100,
        "OverlayRule": 1,
        "OverlayMax": 1,
        "SkillCombineDesc": "94BB57718F6CA746_##",
        "Prefab": "Prefab_Characters/Prefab_Hero/141_DiaoChan/skill/Change",
        "Duration": -1,
        "bAgeImmeExcute": True,
        "ExtraEffectSlotType": -1,
        "TargetMarkerSlotType": -1,
        "UnknownI4": 10000
    },
    {
        "CfgID": 132789,
        "bMapSkillCombineUseRuleID": 100,
        "OverlayRule": 1,
        "OverlayMax": 1,
        "SkillCombineDesc": "94BB57718F6CA746_##",
        "Prefab": "Prefab_Characters/Prefab_Hero/141_DiaoChan/skill/Change",
        "Duration": -1,
        "bAgeImmeExcute": True,
        "ExtraEffectSlotType": -1,
        "TargetMarkerSlotType": -1,
        "UnknownI4": 10000
    },
    {
        "CfgID": 132890,
        "bMapSkillCombineUseRuleID": 100,
        "OverlayRule": 1,
        "OverlayMax": 1,
        "SkillCombineDesc": "94BB57718F6CA746_##",
        "Prefab": "Prefab_Characters/Prefab_Hero/141_DiaoChan/skill/Change",
        "Duration": -1,
        "bAgeImmeExcute": True,
        "ExtraEffectSlotType": -1,
        "TargetMarkerSlotType": -1,
        "UnknownI4": 10000
    }])
    
    with open(skillcombine, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        