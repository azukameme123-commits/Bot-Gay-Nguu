import os
import json

def Sound_Databin(ID_SKIN, folder_path):
    hero_prefix = ID_SKIN[:3]
    base_skin = hero_prefix + "00"
    mapped_prefix = "235"

    special_map = {
        "11620": {
            ("11620", "1162001", "1162002", "1162003", "1162004"): "23520",
            ("1162005", "1162006"): "11600",
        },
        "13311": {
            ("1331101",): "23511",
            ("1331102", "1331103", "1331104"): "13300",
        },
        "15004": {
            ("1503301", "1503302", "1503303", "1503304", "1503305"): "23511",
        },
        "16707": {
            ("1670701", "1670702"): "23507",
            ("1670703", "1670704", "1670705"): "16700",
        },
    }

    evo_map = {}
    if ID_SKIN in special_map:
        for k, v in special_map[ID_SKIN].items():
            for sid in k:
                evo_map[sid] = v

    for name in os.listdir(folder_path):
        if not name.endswith(".bytes"):
            continue

        path = os.path.join(folder_path, name)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            continue

        changed = False
        new_data = []

        for e in data:
            sid = str(e.get("HeroSkinID", ""))
            
            if not sid.startswith(hero_prefix) and sid not in evo_map:
                new_data.append(e)
                continue

            if sid in evo_map:
                e["HeroSkinID"] = int(evo_map[sid])
                changed = True
            elif sid == base_skin:
                e["HeroSkinID"] = int(mapped_prefix + base_skin[3:])
                changed = True
            elif sid == ID_SKIN:
                e["HeroSkinID"] = int(base_skin)
                changed = True
            elif sid.startswith(hero_prefix):
                e["HeroSkinID"] = int(mapped_prefix + sid[3:])
                changed = True
            
            new_data.append(e)

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
