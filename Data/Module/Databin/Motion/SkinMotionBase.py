import json

def Mod_Motion(file_path, ID_SKIN):
    ID_SKIN = int(ID_SKIN)
    HERO_ID = int(str(ID_SKIN)[:3])

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    best_motion = None
    best_quality = -1

    for obj in data:
        if obj.get("HeroID") != HERO_ID:
            continue

        quality = obj.get("Quality", 0)

        for sg in obj.get("SkinGroup", []):
            if sg[0] == ID_SKIN:
                if quality > best_quality:
                    best_quality = quality
                    best_motion = sg[1]

    if best_motion is None:
        return
        
    for obj in data:
        if obj.get("HeroID") == HERO_ID:
            for sg in obj.get("SkinGroup", []):
                sg[1] = best_motion
                
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)