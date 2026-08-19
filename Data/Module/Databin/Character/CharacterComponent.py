import json
import os

def Mod_ResCharacterComponent(file_path, ID_SKIN):
    hero_id = int(ID_SKIN[:3])
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data = [item for item in data if item.get("HeroID") != hero_id]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)