import os
import re
import xml.etree.ElementTree as ET

def Xml(path):
    if os.path.isfile(path):
        files = [path]
    else:
        files = [os.path.join(path, f) for f in os.listdir(path)]

    for file_path in files:

        if not os.path.isfile(file_path):
            continue

        try:
            try:
                tree = ET.parse(file_path)
                tree.write(file_path, encoding="utf-8")
            except Exception:
                continue

            with open(file_path, "rb") as f:
                data = f.read()

            data = re.sub(rb">\s+<", b"><", data)
            
            with open(file_path, "wb") as f:
                f.write(data)

        except:
            pass