import json
import copy

def Mod_HeadImage(file_path, ID):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    code = None
    for i in data:
        if i.get("ID") == ID:
            code = i
            break

    if not code:
        return data

    for i in data:
        code1 = copy.deepcopy(code)
        code1["ID"] = i["ID"]
        i.update(code1)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data