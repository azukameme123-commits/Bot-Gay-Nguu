import json
import copy

def ModLabelDong(file, ID_SKIN):
    ID_SKIN = int(ID_SKIN)
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    template = None
    for item in data:
        if item.get("ID") == ID_SKIN:
            template = item
            break

    if template is None:
        return

    prefix = str(ID_SKIN)[:3]
    existing_ids = {item["ID"] for item in data}

    for i in range(46):
        new_id = int(prefix + f"{i:02d}")

        if new_id in existing_ids:
            continue

        new_item = copy.deepcopy(template)
        new_item["ID"] = new_id
        data.append(new_item)

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)