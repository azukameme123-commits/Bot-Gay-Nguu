"""import os
import re

def HDSkill(ID_SKIN, ID_HD, THU_MUC_SKILL):
    Change_Actor = []

    if isinstance(ID_SKIN, bytes):
        ID_SKIN = ID_SKIN.decode()

    for file in os.listdir(THU_MUC_SKILL):
        file_path = os.path.join(THU_MUC_SKILL, file)

        if not os.path.isfile(file_path):
            continue

        with open(file_path, 'rb') as f:
            content = f.read()

        if b'"Jg\x00' in content:
            continue

        tracks_ca = re.findall(
            rb'<Track[^>]*ChangeActorMeshDuration[^>]*?>.*?</Track>',
            content,
            flags=re.DOTALL
        )

        for track in tracks_ca:
            for path in re.findall(
                rb'<String[^>]*name="prefabName"[^>]*value="([^"]+)"',
                track
            ):
                name = path.split(b"/")[-1].decode(
                    "utf-8",
                    errors="ignore"
                )

                if name not in Change_Actor:
                    Change_Actor.append(name)

        parts = re.split(
            rb'(<Track[^>]*?>.*?</Track>)',
            content,
            flags=re.DOTALL
        )

        modified = False
        result = b''

        for part in parts:
            if part.startswith(b'<Track') and b'</Track>' in part:

                if not (
                    b'hero_skill_effects' in part or
                    b'Hero_Skill_Effects' in part or
                    b'component_effects' in part or
                    b'Component_Effects' in part
                ):
                    result += part
                    continue

                if (
                    b'AutoY' in part or
                    b'tongyong_effects' in part or
                    b'enabled="false"' in part or
                    b'_E"' in part or
                    b'_e"' in part
                ):
                    result += part
                    continue

                def process_resource(match):
                    nonlocal modified

                    prefix = match.group(1)
                    value = match.group(2)
                    suffix = match.group(3)

                    if value.strip() == b"":
                        return match.group(0)

                    new_value = value

                    basename = value.split(b"/")[-1].decode(
                        "utf-8"
                    )

                    if basename in Change_Actor:
                        if not new_value.endswith(b".prefab"):
                            new_value += b".prefab"

                    elif ID_SKIN in ID_HD:

                        if ID_SKIN == "15013" and file == "APsuper.xml":
                            if not new_value.endswith(b".prefab"):
                                new_value += b".prefab"

                        else:
                            if not new_value.endswith(b"_HD"):
                                new_value += b"_HD"

                    else:
                        if not new_value.endswith(b".prefab"):
                            new_value += b".prefab"

                    if new_value != value:
                        modified = True

                    return prefix + new_value + suffix

                part_new = re.sub(
                    rb'((?:resourceName|prefabName|prefab)\d*"[^>]*value=")([^"]*)(")',
                    process_resource,
                    part
                )

                result += part_new

            else:
                result += part

        if modified:
            with open(file_path, 'wb') as f:
                f.write(result)

    return Change_Actor"""
    
import os
import re

RE_TRACK_CHANGE_ACTOR = re.compile(
    rb'<Track[^>]*ChangeActorMesh[^>]*?>.*?</Track>',
    re.DOTALL
)

RE_PREFAB_NAME = re.compile(
    rb'<String[^>]*name="prefabName"[^>]*value="([^"]+)"'
)

RE_TRACK_BLOCK = re.compile(
    rb'<Track[^>]*?>.*?</Track>',
    re.DOTALL
)

RE_RESOURCE = re.compile(
    rb'(<String[^>]*value=")([^"]*prefab_skill_effects[^"]*)(")'
)

SKIP_SIGNATURE = b'"Jg\x00'

INCLUDE_MARKERS = (
    b'prefab_skill_effects',
    b'Prefab_Skill_Effects'
)

EXCLUDE_MARKERS = (
    b'AutoY',
    b'tongyong_effects',
    b'enabled="false"',
    b'_E"',
    b'_e"',
    b'13216_MaKeBoLuoB'
)


def _to_str(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return str(value)


def _skin_in_hd(id_skin, id_hd):
    if isinstance(id_hd, (list, tuple, set)):
        return id_skin in {_to_str(x) for x in id_hd}
    return id_skin in _to_str(id_hd)


def HDSkill(ID_SKIN, ID_HD, THU_MUC_SKILL):
    id_skin = _to_str(ID_SKIN)
    has_hd = _skin_in_hd(id_skin, ID_HD)

    Change_Actor = []
    change_actor_set_bytes = set()
    file_cache = []

    for entry in os.scandir(THU_MUC_SKILL):
        if not entry.is_file():
            continue

        with open(entry.path, "rb") as f:
            content = f.read()

        file_cache.append((entry.name, entry.path, content))

        if SKIP_SIGNATURE in content:
            continue

        for track in RE_TRACK_CHANGE_ACTOR.findall(content):
            for path in RE_PREFAB_NAME.findall(track):
                name_bytes = path.rsplit(b"/", 1)[-1]
                if name_bytes not in change_actor_set_bytes:
                    change_actor_set_bytes.add(name_bytes)
                    Change_Actor.append(
                        name_bytes.decode("utf-8", errors="ignore")
                    )

    for file_name, file_path, content in file_cache:
        if SKIP_SIGNATURE in content:
            continue

        result_parts = []
        last_end = 0
        modified = False

        for match in RE_TRACK_BLOCK.finditer(content):
            start, end = match.span()
            track = match.group(0)

            result_parts.append(content[last_end:start])
            last_end = end

            if not any(marker in track for marker in INCLUDE_MARKERS):
                result_parts.append(track)
                continue

            if any(marker in track for marker in EXCLUDE_MARKERS):
                result_parts.append(track)
                continue

            def process_resource(m):
                nonlocal modified

                prefix = m.group(1)
                value = m.group(2)
                suffix = m.group(3)

                if not value.strip():
                    return m.group(0)

                new_value = value
                basename_bytes = value.rsplit(b"/", 1)[-1]

                if basename_bytes in change_actor_set_bytes:
                    if not new_value.endswith(b".prefab"):
                        new_value += b".prefab"
                elif has_hd:
                    if id_skin == "15013" and file_name == "APsuper.xml":
                        if not new_value.endswith(b".prefab"):
                            new_value += b".prefab"
                    else:
                        if not new_value.endswith(b"_HD"):
                            new_value += b"_HD"
                else:
                    if not new_value.endswith(b".prefab"):
                        new_value += b".prefab"

                if new_value != value:
                    modified = True

                return prefix + new_value + suffix

            new_track = RE_RESOURCE.sub(process_resource, track)
            result_parts.append(new_track)

        result_parts.append(content[last_end:])

        if modified:
            with open(file_path, "wb") as f:
                f.write(b"".join(result_parts))

    return Change_Actor
