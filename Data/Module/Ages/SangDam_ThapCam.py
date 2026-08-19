import os
import re
import xml.etree.ElementTree as ET
from copy import deepcopy

def ModEffects(AllSkinid0, heroname, trackName):
    return_trackName = b''
    for skinid0 in AllSkinid0:
        prefab = b'"prefab_skill_effects/hero_skill_effects/' + str.encode(f'{heroname}/')
        trackName1 = re.sub(str.encode(f'(?i)"prefab_skill_effects/hero_skill_effects/{heroname}/'), prefab, trackName)
        return_trackName += trackName1
    return trackName + return_trackName

def ProcessTrackFiles(path, heroname, all_skinid0):
    AllSkinid0_list = all_skinid0.split(' ')
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if not os.path.isfile(file_path):
            continue
        with open(file_path, "rb") as r0:
            context = r0.read()
            AllTracks = re.findall(rb'\n    <Track trackName="(.*?)</Track>', context, re.DOTALL)
            if AllTracks:
                for trackName in AllTracks:
                    full_track = b'\n    <Track trackName="' + trackName + b'</Track>'
                    if re.search(rb'enabled="false"', full_track) is None:
                        if ((b'<String name="resourceName' in full_track or b'<String name="prefabName' in full_track) and re.search(rb'(?i)prefab_s', full_track) and re.search(rb'(?i)kill_effects', full_track) and not re.search(rb'(?i)ui_fx', full_track) and not re.search(rb'(?i)ChangeActorMesh', full_track) and not re.search(rb'(?i)<String name="resourceName" value=""', full_track) and not re.search(rb'(?i)AutoY"', full_track)):
                            modified = ModEffects(AllSkinid0_list, heroname, full_track)
                            context = context.replace(full_track, modified)
        with open(file_path, "wb") as w0:
            w0.write(context)
            
def ModEffects2(AllSkinid0, heroname, trackName):
    return_trackName = b''
    for skinid0 in AllSkinid0:
        prefab = b'"prefab_skill_effects/hero_skill_effects/' + str.encode(f'{heroname}/{skinid0}/')
        trackName1 = re.sub(str.encode(f'(?i)"prefab_skill_effects/hero_skill_effects/{heroname}/'), prefab, trackName)
        return_trackName += trackName1
    return trackName + return_trackName

def ProcessTrackFiles2(path, heroname, all_skinid0):
    AllSkinid0_list = all_skinid0.split(' ')
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if not os.path.isfile(file_path):
            continue
        with open(file_path, "rb") as r0:
            context = r0.read()
            AllTracks = re.findall(rb'\n    <Track trackName="(.*?)</Track>', context, re.DOTALL)
            if AllTracks:
                for trackName in AllTracks:
                    full_track = b'\n    <Track trackName="' + trackName + b'</Track>'
                    if re.search(rb'enabled="false"', full_track) is None:
                        if ((b'<String name="resourceName' in full_track or b'<String name="prefabName' in full_track) and re.search(rb'(?i)prefab_s', full_track) and re.search(rb'(?i)kill_effects', full_track) and not re.search(rb'(?i)ui_fx', full_track) and not re.search(rb'(?i)ChangeActorMesh', full_track) and not re.search(rb'(?i)<String name="resourceName" value=""', full_track) and not re.search(rb'(?i)AutoY"', full_track)):
                            modified = ModEffects2(AllSkinid0_list, heroname, full_track)
                            context = context.replace(full_track, modified)
        with open(file_path, "wb") as w0:
            w0.write(context)          

def FixStopTrack(path):
    for name in os.listdir(path):
        if not name.lower().endswith(".xml"):
            continue

        file_path = os.path.join(path, name)
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, "rb") as f:
                f.read().decode("utf-8")
        except:
            continue

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except:
            continue

        modified = False

        for parent in root.iter():
            tracks = list(parent.findall("Track"))
            if not tracks:
                continue
                
            trigger_total = {}
            for t in tracks:
                has_prefab = False
                for s in t.findall(".//String"):
                    if s.get("name") == "resourceName":
                        val = s.get("value", "").lower()
                        if val.startswith("prefab_skill_effects"):
                            has_prefab = True
                            break

                if has_prefab:
                    g = t.get("guid")
                    if g:
                        trigger_total[g] = trigger_total.get(g, 0) + 1

            dup_map = {
                g: [g] + [f"{i}-{g}" for i in range(2, c + 1)]
                for g, c in trigger_total.items()
                if c > 1
            }

            if not dup_map:
                continue

            trigger_seen = {}
            new_tracks = []

            for t in tracks:
                etype = t.get("eventType")

                if etype in ("StopTrack", "StopTracks"):
                    new_tracks.append(t)

                    for obj in t.findall(".//TrackObject"):
                        base_guid = obj.get("guid")
                        if base_guid in dup_map:
                            for new_guid in dup_map[base_guid][1:]:
                                clone = deepcopy(t)
                                for clone_obj in clone.findall(".//TrackObject"):
                                    if clone_obj.get("guid") == base_guid:
                                        clone_obj.set("guid", new_guid)
                                new_tracks.append(clone)
                                modified = True
                    continue

                has_prefab = False
                for s in t.findall(".//String"):
                    if s.get("name") == "resourceName":
                        val = s.get("value", "").lower()
                        if val.startswith("prefab_skill_effects"):
                            has_prefab = True
                            break

                if has_prefab:
                    g = t.get("guid")
                    trigger_seen[g] = trigger_seen.get(g, 0) + 1
                    if g in dup_map and trigger_seen[g] > 1:
                        t.set("guid", f"{trigger_seen[g]}-{g}")
                        modified = True
                    new_tracks.append(t)
                    continue

                new_tracks.append(t)

            for t in tracks:
                parent.remove(t)
            for t in new_tracks:
                parent.append(t)

        if modified:
            tree.write(file_path, encoding="utf-8", xml_declaration=True)