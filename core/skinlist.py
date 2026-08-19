# -*- coding: utf-8 -*-
"""Doc skin.txt + notify.txt + quet Source -> danh sach button mod duoc."""
import os, re, glob

_ID_LINE = re.compile(r'^\s*(\d{4,6})\s*[-\u2013\u2014:]\s*(.+?)\s*$')
_HERO    = re.compile(r'^\s*(\S.*?)\s*:\s*$')


def parse_skin_txt(path):
    """Parse skin.txt theo section Hero -> {id:(skin_name, hero)}.

    Tuong thich 100% tool cu (chung format voi run.py ban dau)."""
    out, hero = {}, ''
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            m = _ID_LINE.match(line)
            if m:
                out[m.group(1)] = (m.group(2), hero); continue
            m = _HERO.match(line)
            if m and not m.group(1)[0].isdigit():
                hero = m.group(1)
    return out


# ============================================================ notify support
def parse_notify_txt(path):
    """Parse notify.txt -> {'IDS': set(id_str), 'MAP': {id_str: hero}}."""
    notify_ids = set()
    notify_map = {}
    if not os.path.isfile(path):
        return notify_ids, notify_map
    hero = ''
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.split('#', 1)[0]  # cho phep comment sau #
            m = _HERO.match(line)
            if m and not m.group(1)[0].isdigit():
                hero = m.group(1).strip()
                continue
            m = _ID_LINE.match(line)
            if m:
                sid = m.group(1)
                if sid not in notify_ids:
                    notify_ids.add(sid)
                    notify_map[sid] = hero
    return notify_ids, notify_map


def scan_source(src_dir):
    """Quet Source/ -> {sid: {effect, effect_raw, sprite_raw}}.

    Giu nguyen 100% logic cua tool goc (chi ho tro personalbutton(effect|sprite))."""
    res = {}
    for p in glob.glob(os.path.join(src_dir, '**', '*.assetbundle'), recursive=True):
        b = os.path.basename(p)
        m = re.match(r'^personalbutton(effect|sprite)_(\d+)(_raw)?\.assetbundle$', b, re.I)
        if not m:
            continue
        kind, sid, raw = m.group(1).lower(), m.group(2), bool(m.group(3))
        d = res.setdefault(sid, {'effect': None, 'effect_raw': None, 'sprite_raw': None})
        if kind == 'effect':
            d['effect_raw' if raw else 'effect'] = p
        elif kind == 'sprite' and raw:
            d['sprite_raw'] = p
    return res


def build_menu(src_dir, skin_txt, notify_txt=None, databin_dir=None):
    """Doc skin.txt + notify.txt + Source/ + ResBillboardSkinCfg.bytes -> menu.

    KHONG con phu thuoc notify.txt de quyet dinh skin nao patch duoc notify:
    danh sach notify lay TRUC TIEP tu ResBillboardSkinCfg.bytes (file config
    thuc cua game) -> bat ky skin nao co trong do deu patch duoc, khong theo
    bat ky format file mau nao. notify.txt (neu co) chi dung lam nguon
    ten/hero bo sung.

    Skin chi co thong bao ha (co trong SkinCfg nhung khong co nut trong
    Source/) van duoc dua vao menu voi tag 'NTF' -> mod duoc thong bao ha
    doc lap, khong can file nut.
    """
    skins = parse_skin_txt(skin_txt) if os.path.isfile(skin_txt) else {}
    notify_ids, notify_map = parse_notify_txt(notify_txt) if notify_txt else (set(), {})
    files = scan_source(src_dir)

    # Nguon chan tri cho notify: file config cua game
    cfg_skins = {}
    if databin_dir:
        try:
            from . import notify_engine
            cfg_skins = notify_engine.list_all_billboard_skins(databin_dir)
        except Exception:
            cfg_skins = {}

    rows = []
    seen = set()
    for sid, f in files.items():
        if not (f['effect'] or f['sprite_raw']):
            continue
        seen.add(sid)
        name, hero = skins.get(sid, ('(khong co trong skin.txt)', ''))
        has_notify = sid in cfg_skins or sid in notify_ids
        parts_b = []
        if f['effect']:     parts_b.append('FX')
        if f['sprite_raw']: parts_b.append('JOY')
        if has_notify:      parts_b.append('NTF')
        parts = '+'.join(parts_b) or '-'
        rows.append({
            'id': sid, 'name': name, 'hero': hero,
            'parts': parts, 'files': f,
            'known': sid in skins,
            'notify': has_notify,
            'notify_known': has_notify,
        })

    # Skin THUAN notify (co trong SkinCfg cua game nhung khong co nut):
    # van cho vao menu de mod thong bao ha doc lap.
    for sid in sorted(cfg_skins, key=int):
        if sid in seen:
            continue
        name, hero = skins.get(sid, ('', ''))
        if not name:
            name = '(chi thong bao ha)'
        if not hero:
            hero = notify_map.get(sid, '')
        rows.append({
            'id': sid, 'name': name, 'hero': hero,
            'parts': 'NTF',
            'files': {'effect': None, 'effect_raw': None, 'sprite_raw': None},
            'known': sid in skins,
            'notify': True,
            'notify_known': True,
        })

    rows.sort(key=lambda r: (not r['known'], r['hero'], r['id']))
    return rows
