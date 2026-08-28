
import os
import re

SKIP_MARKER       = b'"Jg\x00'

TRACK_RE          = br'(<Track.*?</Track>)'
TRACK_SPLIT       = b'    <Track trackName="'
EVENT_VALUE_RE    = rb'<String name="eventName" value="(.*?)"'
PRE_PATH_RE       = br'(?i)(<String\s+name="[^"]+"\s+value=")(prefab_skill_effects[^"]+)(" refParamName="" useRefParam="false" />)'

PATH_STRIP_BACK   = b'Project\\Assets\\Prefabs\\'
PATH_STRIP_FWD    = b'Project/Assets/Prefabs/'

EMPTY_EFFECT_FROM = b'<bool name="bAllowEmptyEffect" value="true"'
EMPTY_EFFECT_TO   = b'<bool name="bAllowEmptyEffect" value="false"'

EXTRA_SKIN_RE     = br'\r\n\s*<Array name="extraSkinId".*?</Array>'
COMPONENT_LOWER   = b'component_effects/'
Effectf_Code        = b'prefab_skill_effects/hero_skill_effects/'
COMPONENT_DIR_B   = b'prefab_skill_effects/component_effects/'

SOUND_EVO = {
    b'13311': (b'_Skin11_AW2', b'_Skin11_AW3'),
    b'16707': (b'_Skin7_AW3',  b'_Skin7_AW4'),
    b'11620': (b'_Skin20_AW5', b'_Skin20_AW5'),
}

SKIP_CODES = {
    (b'13210', 'S1B0.xml'):  [b'5f05ee52'],
    (b'13210', 'S11B0.xml'): [b'7d02fc49'],
    (b'13210', 'S12B0.xml'): [b'aac205d6'],
    (b'54307', 'S1.xml'):    [b'eccedf60'],
    (b'54307', 'S1B1.xml'):  [b'29c7a696'],
    (b'15611', 'S3.xml'):    [b'c42c43de'],
    (b'50108', 'S2B1.xml'):  [b'20901971'],
    (b'50112', 'P9.xml'):    [b'da35'],
    (b'50112', 'S2B1.xml'):  [b'7ea0'],
    (b'15013', 'S2.xml'):    [b'b73050c0'],
    (b'59702', 'U1.xml'):    [b'2ccfceee'],
    (b'59702', 'U11B1.xml'): [b'076cb1cf'],
    (b'13112', 'S1E5.xml'):  [b'456b8f23'],
    (b'13116', 'S1.xml'):    [b'721f7371'],
    (b'13116', 'S11.xml'):   [b'158a1edd'],
    (b'13116', 'U1B1.xml'):  [b'78c3df73'],
    (b'13118', 'U1B1.xml'):  [b'b8a8a82e'],
    (b'13118', 'U1E7.xml'):  [b'ab9bc01c'],
    (b'13011', 'A1.xml'):    [b'47afc0ce'],
    (b'13011', 'A2.xml'):    [b'47afc0ce'],
    (b'13011', 'A3.xml'):    [b'47afc0ce'],
    (b'13011', 'A4.xml'):    [b'47afc0ce'],
    (b'13011', 'S2.xml'):    [b'd3ea4a4d', b'79427f69'],
    (b'13011', 'S21.xml'):   [b'd3ea4a4d', b'6b3a8d20'],
    (b'13011', 'S22.xml'):   [b'd3ea4a4d', b'8d5e99b6'],
}

FILE_SKIN_SKIP = {
    b'14111': {'A1B2.xml', 'S1.xml'},
    b'12008': {'P1E2.xml', 'P1E8.xml', 'S11.xml'},
    b'14117': {'A1B2.xml'},
    b'17408': {'17408_Back.xml'},
    b'19613': {'P01.xml'},
    b'53806': {'U1.xml', 'Skin2E1.xml'},
    b'11215': {'S1.xml'},
    b'56703': {'A1.xml', 'A2.xml', 'A3.xml'},
    b'56704': {'A1.xml', 'A2.xml', 'A3.xml'},
    b'19015': {'Skin15E2.xml'},
    b'16607': {'16607_Back.xml'},
    b'11113': {'U1.xml'},
    b'12907': {'S1E1.xml', 'S1E2.xml', 'U1E2.xml'},
    b'13011': {'S2B1_13011.xml', 'S2B2_13011.xml', 'S2B3_13011.xml'},
    b'10611': {'A2.xml'},
    b'13210': {'t2b1.xml', 't2b2.xml', 't2b3.xml'},
    b'13609': {'U1.xml', 'U1B2.xml'},
    b'16707': {'U1B0.xml'},
    b'15015': {'U1.xml'},
    b'16307': {'P2.xml'},
    b'59702': {'Skin2E1.xml'},
    b'10620': {'S2B1.xml', 'U1B0.xml', 'U1E1.xml', 'P1.xml'},
}

CHECK_SK_HDR      = b'CheckSkinIdTick'
CHECK_VT_HDR      = b'CheckSkinIdVirtualTick'
DISABLED_HDR      = b'enabled="false"'
BOOL_LINE_PREFIX  = b'\r\n        <bool name="'

RGX_SKIN_STRIP    = rb'(_Skin\d+)+'

AUX_FOR_13015     = b'13014'


def _is_xml(name):       return name.endswith('.xml')
def _voice_or_vo(v):     return b'_Voice_' in v or b'_VO_' in v


def _collapse_skin_dupe(m):
    raw = m.group(0)
    if raw.count(b'_Skin') <= 1:
        return raw
    return raw.split(b'_Skin')[0] + b'_Skin' + raw.split(b'_Skin')[-1]


def _pick_suffix(skin_id, value, default):
    if skin_id in SOUND_EVO:
        s0, s1 = SOUND_EVO[skin_id]
        return s1 if _voice_or_vo(value) else s0
    return default


def _make_path_rewriter(skin_id, hero_b):
    def repl(m):
        raw_path = m.group(2).replace(b'\\', b'/')
        if COMPONENT_LOWER in raw_path.lower():
            return m.group(0)
        leaf = raw_path.split(b'/')[-1]
        if skin_id in SOUND_EVO:
            tail = COMPONENT_DIR_B + skin_id + b'/' + skin_id + b'_5/' + leaf
        else:
            tail = Effectf_Code + hero_b + b'/' + skin_id + b'/' + leaf
        return m.group(1) + tail + m.group(3)
    return repl


def _is_skippable_track(block):
    return (block.startswith(b'<Track')
            and (b'AutoY' in block
                 or b'tongyong_effects' in block
                 or DISABLED_HDR in block))


def _skip_track_due_to_codes(x_id, filename, text):
    anchors = SKIP_CODES.get((x_id, filename))
    if not anchors:
        return False
    return any(code in text for code in anchors)


def ModAges(ID_SKIN, THU_MUC_SKILL, NAME_HERO, ID_Sound):
    skin_id  = ID_SKIN.encode()
    hero_b   = NAME_HERO.lower().encode()
    sound_b  = ID_Sound.encode() if ID_Sound else b''
    rewriter = _make_path_rewriter(skin_id, hero_b)

    for fname in (n for n in os.listdir(THU_MUC_SKILL) if _is_xml(n)):
        path = os.path.join(THU_MUC_SKILL, fname)
        if not os.path.isfile(path):
            continue

        with open(path, 'rb') as f:
            content = f.read()
        if SKIP_MARKER in content:
            continue

        modified, content = _first_pass(content, skin_id, rewriter, sound_b)
        if modified:
            with open(path, 'wb') as f:
                f.write(content)

    _second_pass(skin_id, THU_MUC_SKILL)


def _first_pass(content, skin_id, rewriter, sound_b):
    modified = False

    blocks = re.split(TRACK_RE, content, flags=re.DOTALL)
    for i, block in enumerate(blocks):
        if _is_skippable_track(block):
            continue
        new_block, count = re.subn(PRE_PATH_RE, rewriter, block)
        if count > 0:
            blocks[i] = new_block
            modified = True

    content = b''.join(blocks)
    content = content.replace(PATH_STRIP_BACK, b'').replace(PATH_STRIP_FWD, b'')
    content = content.replace(EMPTY_EFFECT_FROM, EMPTY_EFFECT_TO)

    for value in re.findall(EVENT_VALUE_RE, content):
        old_tag = (b'<String name="eventName" value="' + value
                   + b'" refParamName="" useRefParam="false" />')
        suffix     = _pick_suffix(skin_id, value, sound_b)
        new_value  = value if b'_Skin' in value else value + suffix
        new_value  = re.sub(RGX_SKIN_STRIP, _collapse_skin_dupe, new_value)
        new_tag    = (b'<String name="eventName" value="' + new_value
                      + b'" refParamName="" useRefParam="false" />')
        if old_tag in content and new_value != value:
            content = content.replace(old_tag, new_tag)
            modified = True

    content = re.sub(EXTRA_SKIN_RE, b'', content, flags=re.DOTALL)
    return modified, content


def _second_pass(skin_id, thu_muc):
    list_ids = [skin_id]
    if skin_id == b'13015':
        list_ids.append(AUX_FOR_13015)
    for x_id in list_ids:
        _process_skin(x_id, thu_muc)


def _process_skin(x_id, thu_muc):
    skip_files = FILE_SKIN_SKIP.get(x_id, ())
    for filename in os.listdir(thu_muc):
        file_path = os.path.join(thu_muc, filename)
        if not os.path.isfile(file_path):
            continue
        if filename in skip_files:
            continue
        if x_id.startswith(b'111') and filename == 'A2b2.xml':
            continue

        with open(file_path, 'rb') as f:
            data = f.read()
        if SKIP_MARKER in data:
            continue

        sections  = data.split(TRACK_SPLIT)
        IDS       = b'\r\n        <int name="skinId" value="' + x_id + b'" refParamName="" useRefParam="false" />'
        code_chk  = [s for s in sections
                     if IDS.lower() in s.lower()
                     and DISABLED_HDR not in s.lower()]
        if code_chk:
            data = _patch_tracks(x_id, filename, code_chk, data)

        with open(file_path, 'wb') as f:
            f.write(data)


def _patch_tracks(x_id, filename, code_check, data):
    snips = _make_snippets(x_id)
    for text in code_check:
        if _skip_track_due_to_codes(x_id, filename, text):
            continue
        ltext = text.lower()
        if CHECK_SK_HDR.lower() in ltext:
            data = _apply_check_sk(data, text, snips)
            continue
        if CHECK_VT_HDR.lower() in ltext:
            data = _apply_check_vt(data, text, snips)
    return data


def _make_snippets(x_id):
    return (
        b'\r\n        <int name="skinId" value="235' + x_id[-2:] + b'" refParamName="" useRefParam="false" />',
        b'\r\n        <int name="skinId" value="' + x_id + b'" refParamName="" useRefParam="false" />',
        b'\r\n        <bool name="bEqual" value="false" refParamName="" useRefParam="false" />',
        b'\r\n        <bool name="bEqual" value="true" refParamName="" useRefParam="false" />',
        b'\r\n        <bool name="useNegateValue" value="true" refParamName="" useRefParam="false" />',
        b'\r\n        <bool name="useNegateValue" value="false" refParamName="" useRefParam="false" />',
    )


def _apply_check_sk(data, text, S):
    SKM, IDS, EQF, EQT, UNV, UNF = S
    if BOOL_LINE_PREFIX not in text:
        text1 = text.replace(IDS, IDS + EQF).replace(IDS, SKM)
    elif EQF in text:
        text1 = text.replace(EQF, b'').replace(IDS, SKM)
    elif EQT in text:
        text1 = text.replace(EQT, EQF).replace(IDS, SKM)
    else:
        text1 = text.replace(IDS, IDS + EQF).replace(IDS, SKM)
    return data.replace(text, text1)


def _apply_check_vt(data, text, S):
    SKM, IDS, EQF, EQT, UNV, UNF = S
    if UNV in text:
        text1 = text.replace(UNV, b'').replace(IDS, SKM)
    elif UNF in text:
        text1 = text.replace(UNF, UNV).replace(IDS, SKM)
    else:
        text1 = text.replace(IDS, IDS + UNV).replace(IDS, SKM)
    return data.replace(text, text1)


def ModSoundAges(ID_SKIN, THU_MUC_SKILL, ID_Sound):
    skin_id = ID_SKIN.encode()
    sound_b = ID_Sound.encode()

    for fname in (n for n in os.listdir(THU_MUC_SKILL) if _is_xml(n)):
        path = os.path.join(THU_MUC_SKILL, fname)
        if not os.path.isfile(path):
            continue
        with open(path, 'rb') as f:
            content = f.read()
        if SKIP_MARKER in content:
            continue

        modified, content = _sound_pass(content, skin_id, sound_b)
        if modified:
            with open(path, 'wb') as f:
                f.write(content)


def _sound_pass(content, skin_id, sound_b):
    modified = False
    for value in re.findall(EVENT_VALUE_RE, content):
        old_tag = (b'<String name="eventName" value="' + value
                   + b'" refParamName="" useRefParam="false" />')
        suffix  = _pick_suffix(skin_id, value, sound_b)
        new_tag = (b'<String name="eventName" value="' + value + suffix
                   + b'" refParamName="" useRefParam="false" />')
        new_tag = new_tag.replace(suffix * 2, suffix)
        if old_tag in content:
            content = content.replace(old_tag, new_tag)
            modified = True
    return modified, content

FILE_SKILL_SKIP = {
    "59901": {"S1B1.xml"},
    "59903": {"S1B1.xml"},
    "13213": {"S1B0.xml", "S1B1.xml"},
    "52414": {"S3.xml", "S3_1.xml"},
    "17408": {"17408_back.xml"},
    "11119": {"A1B1.xml", "A1b2.xml", "A2B1.xml", "A2b2.xml", "A4B1.xml", "A4b2.xml"},
    "11120": {"A1B1.xml", "A1b2.xml", "A2B1.xml", "A2b2.xml", "A4B1.xml", "A4b2.xml"},
    "10620": {"S2B1.xml"},
}

_132_BACK_SKIP = [b"CheckAnimationSystemVirtual", b"SetObjectDirection", b"MoveCityDuration"]

TRACK_SKIP = {
    "14120": {
        "S2.xml": [b"4a9c4cf1"],
        "S214112.xml": [b"SpawnObject"],
    },
    "54309": {
        "A1B2.xml": [b"StopTrack"],
    },
    "54807": {
        "U1E2.xml": [b"OldMoveActorDuration"],
    },
    "19111": {
        "P1E5.xml": [b"4ce328bd"],
    },
    "19908": {
        "S1.xml": [b"SetObjBehaviourMode"],
    },
    "13314": {
        "Death.xml": [b"SetObjectDirection"],
    },
    "51015": {
        "Death.xml": [b"SetObjectDirection"],
    },
    "59703": {
        "S1.xml": [b"CheckSkinIdVirtual"],
        "S11.xml": [b"CheckSkinIdVirtual"],
    },
    "12313": {
        "S1E71.xml": [b'CreateRandomNum', b'CheckRandomRange'],
        "U1.xml": [b'CheckRandomRange', b'CreateRandomNum', b'FilterTargetTypeClient'],
    },
    "10915": {
        "A2.xml": [b"ChangeSkillTrigger"],
    },
    "13706": {
        "A2.xml": [b"ChangeSkillTrigger"],
        "A5.xml": [b"ChangeSkillTrigger"],
        "A7.xml": [b"SetAttackDir"],
        "A8.xml": [b"SetAttackDir"],
        "A9.xml": [b"SetAttackDir"],
    },
    "59903": {
        "S1E60.xml": [b"ScaleMesh"],
        "S1.xml": [b"SpawnBullet"],
    },
    "59901": {
        "A5.xml": [b"SpawnObject"],
        "S1E60.xml": [b"ScaleMesh"],
        "S1.xml": [b"SpawnBullet"],
        "u1b1.xml": [b"SpawnObject", b"SetCollision"],
        "U11.xml": [b"SpawnObject", b"SetCollision"],
    },
    "59802": {
        "A1B2.xml": [b"SpawnObject"],
        "A1B5.xml": [b"Random"],
        "A1B6.xml": [b"Random"],
        "A1B12.xml": [b"SpawnObject"],
        "A1B61.xml": [b"Random"],
        "S2E6.xml": [b"HitTriggerTick"],
    },
    "19016": {
        **{f: [b"CheckSkinIdVirtual"] for f in
           ("P1E2.xml", "P1E22.xml", "P1E23.xml", "P1E24.xml", "P1E25.xml", "U1B0.xml", "U1E2.xml", "U1E6.xml")},
        **{f: [b"SpawnObjectDuration", b"SetCollision"] for f in
           ("S1B11.xml", "S1B22.xml", "S1B44.xml")},
        "S1.xml": [b"SpawnBullet"],
        "U1.xml": [b"Random"],
    },
    "52710": {f: [b"RemoveBullet"] for f in ("A1.xml", "A2.xml", "A3.xml", "S1.xml", "S2.xml", "U1.xml")
    },
    "56301": {
        **{f: [b"StopTracks"] for f in
           ("A6B2.xml", "A7B2.xml")},
       "S2.xml": [b"SpawnObjectDuration"],
    },
    "50119": {f: [b"FilterTargetType", b"CheckAndSetPreCrikRate"] for f in ("A1.xml", "A2.xml", "A3.xml", "A4.xml", "A5.xml", "A6.xml")
    },
    "50119": {f: [b"CheckAndSetPreCrikRate"] for f in ("A1.xml", "A2.xml", "A3.xml", "A4.xml", "A5.xml", "A6.xml")
    },
    "11215": {f: [b"SpawnObjectDuration"] for f in ("A1B1.xml", "A2B1.xml", "A3B1.xml", "A4B1.xml", "A1B2.xml", "A2B2.xml", "A3B2.xml", "A4B2.xml", "s1b3.xml")
    },
    "13215": {
        "A1B1.xml": [b"DebugLog", b"StopTracks"],
        "S2.xml": [b'<int name="buffId" value="132942"'],
        "132_Back.xml": _132_BACK_SKIP,
    },
    "13204": {"132_Back.xml": _132_BACK_SKIP},
    "132010": {"132_Back.xml": _132_BACK_SKIP},
    "13212": {"132_Back.xml": _132_BACK_SKIP},
    "13213": {"132_Back.xml": _132_BACK_SKIP},
}


def _attr(tag, name):
    key = name + b'="'
    i = tag.find(key)
    if i == -1:
        return None
    i += len(key)
    j = tag.find(b'"', i)
    if j == -1:
        return None
    return tag[i:j]


def _set_attr(tag, name, value):
    old = _attr(tag, name)
    if old is None:
        return tag
    return tag.replace(name + b'="' + old + b'"', name + b'="' + value + b'"', 1)


def _iter_child_tags(text, name):
    marker = b'<' + name
    pos = 0
    tags = []
    while True:
        start = text.find(marker, pos)
        if start == -1:
            break
        end = text.find(b'>', start)
        if end == -1:
            break
        tags.append(text[start:end + 1])
        pos = end + 1
    return tags


def _track_skin_ids(text, id_skin):
    ids = {id_skin}
    for tag in _iter_child_tags(text, b'SkinOrAvatarList'):
        sid = _attr(tag, b'id')
        if sid:
            ids.add(sid.decode('utf-8', 'ignore'))
    return ids


def _hits_skip_codes(text, filename, id_skin):
    codes = []
    for sid in _track_skin_ids(text, id_skin):
        codes.extend(TRACK_SKIP.get(sid, {}).get(filename, []))
    return any(code in text for code in codes)


def _skip_by_anim_rule(text, id_skin):
    no_anim_markers = (
        b'prefab_skill_effects' not in text
        and b'PlayHeroSoundTick' not in text
        and b'Anim' not in text
        and b'CheckAnimationSystemVirtualTick' in text
    )
    if not no_anim_markers:
        return False

    id_skin_b = id_skin.encode()
    return (
        b'<int name="skinId" value="235' + id_skin_b[-2:] not in text
        or b'<SkinOrAvatarList id="' + id_skin_b[:3] not in text
    )


def _rename_main_skin(text, id_skin):
    changed = False
    id_skin_b = id_skin.encode()
    new_id = b'235' + id_skin_b[-2:]

    for tag in _iter_child_tags(text, b'SkinOrAvatarList'):
        if _attr(tag, b'id') == id_skin_b:
            new_tag = _set_attr(tag, b'id', new_id)
            if new_tag != tag and tag in text:
                text = text.replace(tag, new_tag, 1)
                changed = True

    return text, changed


def _toggle_filter_type(text):
    head_end = text.find(b'>')
    if head_end == -1:
        return text
    head = text[:head_end + 1]

    val = _attr(head, b'SkinAvatarFilterType')
    if val is None:
        return text

    new_val = {b'9': b'11', b'11': b'9'}.get(val, val)
    new_head = _set_attr(head, b'SkinAvatarFilterType', new_val)
    return new_head + text[head_end + 1:]


def _rename_related_skins(text, filename, id_skin):
    changed = False
    id_skin_b = id_skin.encode()
    prefix = id_skin_b[:3]

    for tag in _iter_child_tags(text, b'SkinOrAvatarList'):
        sid = _attr(tag, b'id')
        if sid is None:
            continue
        sid_str = sid.decode('utf-8', 'ignore')

        if (
            sid != id_skin_b
            and filename not in FILE_SKILL_SKIP.get(id_skin, set())
            and filename not in FILE_SKILL_SKIP.get(sid_str, set())
            and sid.startswith(prefix)
        ):
            new_tag = _set_attr(tag, b'id', b'235' + sid[3:])
            if new_tag != tag and tag in text:
                text = text.replace(tag, new_tag, 1)
                changed = True

    return text, changed


def _process_track(text, filename, id_skin):
    if b'enabled="false"' in text.lower():
        return text, False

    if _hits_skip_codes(text, filename, id_skin):
        return text, False

    changed = False

    text, dung_skin = _rename_main_skin(text, id_skin)
    if dung_skin:
        changed = True
        text = _toggle_filter_type(text)

    if _hits_skip_codes(text, filename, id_skin):
        return text, changed

    if _skip_by_anim_rule(text, id_skin):
        return text, changed

    text, related_changed = _rename_related_skins(text, filename, id_skin)
    if related_changed:
        changed = True

    return text, changed


def _skip_file(filename, id_skin):
    lower = filename.lower()
    if lower in {f.lower() for f in FILE_SKILL_SKIP.get(id_skin, set())}:
        return True
    return False


def SkinAvatar(THU_MUC_SKILL, NAME_HERO, ID_SKIN):
    for filename in os.listdir(THU_MUC_SKILL):
        if not filename.endswith('.xml'):
            continue
        if _skip_file(filename, ID_SKIN):
            continue

        file_path = os.path.join(THU_MUC_SKILL, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, 'rb') as f:
                All = f.read()

            if b'"Jg\x00' in All:
                continue

            MOC = b'    <Track trackName="'
            if MOC not in All:
                MOC = b'<Track trackName="'

            parts = All.split(MOC)
            if len(parts) <= 1:
                continue

            changed_file = False

            for part in parts[1:]:
                text = MOC + part
                new_text, changed = _process_track(text, filename, ID_SKIN)

                if changed and new_text != text:
                    All = All.replace(text, new_text, 1)
                    changed_file = True

            if changed_file:
                with open(file_path, 'wb') as f:
                    f.write(All)

        except (OSError, ValueError):
            pass
            