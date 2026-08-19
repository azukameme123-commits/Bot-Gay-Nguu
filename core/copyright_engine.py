# -*- coding: utf-8 -*-
"""
Them chu ban quyen mo len 2 sprite shop trong personalbuttonsprite_<ID>_raw.

Muc tieu:
- khong sua file Source goc
- chi tao ban tam trong tmpdir roi dua vao luong build hien co
- viet chu de len dung vung cua nut, khong de icon/nen bi mat
- ho tro ca sprite standalone lan atlas-backed
"""
import math
import os
import re
import unicodedata
from collections import defaultdict

DEFAULT_OPACITY = 20
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

SPRITE_TARGETS = {
    'shop_icon': 'CustomJoyStick_ShopIcon',
    'on_right': 'BattleShop_Entrance_OnRight',
}

TEXTURE_NAME_FALLBACKS = {
    'shop_icon': (
        'Texture2D_CustomJoyStick_ShopIcon',
        'CustomJoyStick_ShopIcon',
        'Texture2D_ShopIcon',
        'ShopIcon',
    ),
    'on_right': (
        'Texture2D_BattleShop_Entrance_OnRight',
        'BattleShop_Entrance_OnRight',
    ),
}

COLOR_MAP = {
    'do': '#ff3b30',
    'red': '#ff3b30',
    'luc': '#34c759',
    'green': '#34c759',
    'lam': '#007aff',
    'blue': '#007aff',
    'xanh': '#00bcd4',
    'cyan': '#00bcd4',
    'tram': '#7f8c8d',
    'gray': '#7f8c8d',
    'grey': '#7f8c8d',
    'tim': '#af52de',
    'purple': '#af52de',
    'hong': '#ff2d92',
    'pink': '#ff2d92',
    'den': '#111111',
    'black': '#111111',
    'trang': '#ffffff',
    'white': '#ffffff',
    'nau': '#8e5a3c',
    'brown': '#8e5a3c',
    'vang': '#ffd60a',
    'yellow': '#ffd60a',
}

_FONT_CACHE = {}
Image = None
ImageDraw = None
ImageFont = None
ImageFilter = None


def _strip_accents(text):
    return ''.join(ch for ch in unicodedata.normalize('NFD', text or '')
                   if unicodedata.category(ch) != 'Mn')


def _norm(text):
    text = _strip_accents(text).lower().strip()
    text = re.sub(r'[^a-z0-9#]+', '', text)
    return text


def parse_opacity(raw):
    raw = (raw or '').strip()
    if not raw:
        return DEFAULT_OPACITY
    if raw.endswith('%'):
        raw = raw[:-1].strip()
    if not raw.isdigit():
        raise ValueError('Do trong suot phai la so 0-100.')
    val = int(raw)
    if not (0 <= val <= 100):
        raise ValueError('Do trong suot phai nam trong 0-100.')
    return val


def _hex_to_rgb(hex_value):
    s = hex_value.strip().lstrip('#')
    if s.lower().startswith('0x'):
        s = s[2:]
    if len(s) == 3:
        s = ''.join(ch * 2 for ch in s)
    if len(s) != 6 or re.search(r'[^0-9a-fA-F]', s):
        raise ValueError('Ma mau khong hop le. Dung dang #RRGGBB hoac ten mau.')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def parse_color(raw):
    raw = (raw or '').strip()
    if not raw:
        raise ValueError('Mau khong duoc de trong.')
    key = _norm(raw)
    if key in COLOR_MAP:
        return _hex_to_rgb(COLOR_MAP[key])
    return _hex_to_rgb(raw)


def build_spec(text, color, opacity):
    text = (text or '').strip()
    if not text:
        raise ValueError('Text ban quyen khong duoc de trong.')
    return {
        'text': text,
        'color': tuple(color),
        'opacity': int(opacity),
    }


def _ensure_pillow():
    global Image, ImageDraw, ImageFont, ImageFilter
    if Image is not None and ImageDraw is not None and ImageFont is not None and ImageFilter is not None:
        return
    try:
        from PIL import Image as _Image, ImageDraw as _ImageDraw, ImageFont as _ImageFont, ImageFilter as _ImageFilter
    except Exception as e:
        raise RuntimeError('Thieu Pillow (PIL). Neu muon bat Ban Quyen = y, hay cai: pip install Pillow') from e
    Image = _Image
    ImageDraw = _ImageDraw
    ImageFont = _ImageFont
    ImageFilter = _ImageFilter


def _font_candidates():
    win = os.environ.get('WINDIR', r'C:\\Windows')
    return [
        os.path.join(ASSET_DIR, 'Oswald-wght.ttf'),
        os.path.join(ASSET_DIR, 'Oswald-Medium.ttf'),
        os.path.join(win, 'Fonts', 'arial.ttf'),
        os.path.join(win, 'Fonts', 'arialbd.ttf'),
        os.path.join(win, 'Fonts', 'tahoma.ttf'),
        os.path.join(win, 'Fonts', 'seguiemj.ttf'),
        os.path.join(win, 'Fonts', 'segoeui.ttf'),
        os.path.join(win, 'Fonts', 'times.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
    ]


def _load_font(size):
    _ensure_pillow()
    size = max(8, int(size))
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    for path in _font_candidates():
        if os.path.isfile(path):
            try:
                font = ImageFont.truetype(path, size=size)
                if os.path.basename(path).lower().startswith('oswald'):
                    try:
                        if hasattr(font, 'get_variation_names') and hasattr(font, 'set_variation_by_name'):
                            for name in font.get_variation_names() or []:
                                label = name.decode('utf-8', 'ignore') if isinstance(name, bytes) else str(name)
                                if 'medium' in label.lower():
                                    font.set_variation_by_name(name)
                                    break
                    except Exception:
                        pass
                _FONT_CACHE[size] = font
                return font
            except Exception:
                pass
    try:
        font = ImageFont.truetype('arial.ttf', size=size)
        _FONT_CACHE[size] = font
        return font
    except Exception:
        font = ImageFont.load_default()
        _FONT_CACHE[size] = font
        return font


def _balance_lines(text, line_count):
    words = text.split()
    if not words or line_count <= 1 or len(words) == 1:
        return text
    total = sum(len(w) for w in words) + max(0, len(words) - 1)
    target = max(1, int(math.ceil(total / float(line_count))))
    lines = []
    cur = []
    cur_len = 0
    remaining_words = len(words)
    remaining_lines = line_count
    for w in words:
        piece = len(w) if not cur else len(w) + 1
        force_break = cur and cur_len + piece > target and remaining_words > remaining_lines - 1
        if force_break:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
            remaining_lines -= 1
        else:
            cur.append(w)
            cur_len += piece
        remaining_words -= 1
    if cur:
        lines.append(' '.join(cur))
    return '\n'.join(lines[:line_count])


def _char_wrap(text, line_count):
    text = ' '.join((text or '').split())
    if not text or line_count <= 1:
        return text
    width = max(1, int(math.ceil(len(text) / float(line_count))))
    out = []
    for i in range(0, len(text), width):
        out.append(text[i:i + width])
    return '\n'.join(out[:line_count])


def _candidate_layouts(text, role):
    text = ' '.join((text or '').split())
    if not text:
        return ['']
    out = [text]
    max_lines = 3 if role == 'shop_icon' else 2
    words = text.split()
    if len(words) > 1:
        for n in range(2, max_lines + 1):
            out.append(_balance_lines(text, n))
    elif len(text) >= 8:
        for n in range(2, max_lines + 1):
            out.append(_char_wrap(text, n))
    uniq = []
    seen = set()
    for item in out:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    return uniq


def _safe_box(size, role):
    w, h = size
    if role == 'shop_icon':
        return (
            int(w * 0.07),
            int(h * 0.42),
            int(w * 0.93),
            int(h * 0.90),
        )
    return (
        int(w * 0.10),
        int(h * 0.12),
        int(w * 0.95),
        int(h * 0.78),
    )


def _fit_text(draw, text, role, box):
    bw = max(1, box[2] - box[0])
    bh = max(1, box[3] - box[1])
    max_size = max(10, int(min(bw, bh) * (0.62 if role == 'on_right' else 0.52)))
    min_size = 8
    for candidate in _candidate_layouts(text, role):
        line_count = candidate.count('\n') + 1
        for size in range(max_size, min_size - 1, -1):
            font = _load_font(size)
            spacing = max(0, int(size * 0.06))
            try:
                left, top, right, bottom = draw.multiline_textbbox(
                    (0, 0), candidate, font=font, spacing=spacing, align='center'
                )
            except Exception:
                continue
            tw = right - left
            th = bottom - top
            if tw <= bw and th <= bh:
                return candidate, font, spacing, line_count
    font = _load_font(min_size)
    return text, font, max(0, int(min_size * 0.06)), 1


def _overlay_text(img, text, color, opacity, role):
    _ensure_pillow()
    base = img.convert('RGBA')
    if not text or opacity <= 0:
        return base

    box = _safe_box(base.size, role)
    measure = ImageDraw.Draw(Image.new('RGBA', base.size, (0, 0, 0, 0)))
    content, font, spacing, line_count = _fit_text(measure, text, role, box)
    left, top, right, bottom = measure.multiline_textbbox(
        (0, 0), content, font=font, spacing=spacing, align='center'
    )
    tw = right - left
    th = bottom - top
    x = box[0] + (box[2] - box[0] - tw) / 2.0 - left
    y = box[1] + (box[3] - box[1] - th) / 2.0 - top

    alpha = max(0, min(255, int(round(255 * (opacity / 100.0)))))
    shadow_alpha = max(18, min(92, alpha // 2 + 12))
    text_fill = tuple(color) + (alpha,)
    shadow_fill = (0, 0, 0, shadow_alpha)
    blur_radius = 1.4 if role == 'on_right' else 1.0

    shadow_layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.multiline_text((x + 1, y + 1), content, font=font, fill=shadow_fill,
                               spacing=spacing, align='center')
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    text_layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.multiline_text((x, y), content, font=font, fill=text_fill,
                             spacing=spacing, align='center')
    soft_layer = text_layer.filter(ImageFilter.GaussianBlur(radius=0.35 if role == 'shop_icon' else 0.55))

    merged = Image.alpha_composite(base, shadow_layer)
    merged = Image.alpha_composite(merged, soft_layer)
    merged = Image.alpha_composite(merged, text_layer)
    return merged


def _rect_to_box(rect, tex_w, tex_h):
    x = int(round(float(rect.get('x', 0))))
    y = int(round(float(rect.get('y', 0))))
    w = int(round(float(rect.get('width', 0))))
    h = int(round(float(rect.get('height', 0))))
    if w <= 0 or h <= 0:
        return None
    left = max(0, min(tex_w, x))
    right = max(left, min(tex_w, x + w))
    top = max(0, min(tex_h, tex_h - (y + h)))
    bottom = max(top, min(tex_h, tex_h - y))
    if right <= left or bottom <= top:
        return None
    return (left, top, right, bottom)


def _resolve_targets(env, log):
    objects = {o.path_id: o for o in env.objects}
    sprites = {}
    rmap = {}

    for o in objects.values():
        if o.type.name != 'Sprite':
            continue
        try:
            d = o.read_typetree()
        except Exception:
            continue
        name = d.get('m_Name')
        if name:
            sprites[name] = (o, d)

    for o in objects.values():
        if o.type.name != 'SpriteAtlas':
            continue
        try:
            sa = o.read_typetree()
        except Exception:
            continue
        for k, v in sa.get('m_RenderDataMap', []):
            rmap[(tuple(k['first'].values()), k['second'])] = v

    out = {}
    for role, sprite_name in SPRITE_TARGETS.items():
        item = sprites.get(sprite_name)
        if not item:
            continue
        _, sd = item
        rd = sd.get('m_RD', {})
        if sd.get('m_SpriteAtlas', {}).get('m_PathID'):
            key = (tuple(sd['m_RenderDataKey']['first'].values()), sd['m_RenderDataKey']['second'])
            rd = rmap.get(key)
            if rd is None:
                log('   ! BQ: %s co atlas nhung khong tim thay RenderDataMap' % sprite_name)
                continue
        tex_pid = rd.get('texture', {}).get('m_PathID', 0)
        rect = rd.get('textureRect') or sd.get('m_Rect') or {}
        if tex_pid and tex_pid in objects:
            out[role] = {
                'sprite_name': sprite_name,
                'texture_pid': tex_pid,
                'rect': rect,
            }

    # fallback theo ten Texture2D neu sprite khong loi duoc
    for role, aliases in TEXTURE_NAME_FALLBACKS.items():
        if role in out:
            continue
        for o in objects.values():
            if o.type.name != 'Texture2D':
                continue
            try:
                name = o.read_typetree().get('m_Name', '')
            except Exception:
                continue
            if name in aliases:
                out[role] = {
                    'sprite_name': name,
                    'texture_pid': o.path_id,
                    'rect': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                }
                break
    return objects, out


def patch_sprite_bundle(src_encrypted_path, tmpdir, spec, log=lambda s: None):
    """Tao 1 sprite_raw tam da duoc de chu ban quyen, tra ve duong dan FILE MA HOA moi."""
    if not spec:
        return src_encrypted_path

    _ensure_pillow()
    from .aovlib import UnityPy, decrypt_bundle, encrypt_bundle

    os.makedirs(tmpdir, exist_ok=True)
    dec = os.path.join(tmpdir, 'copyright_src.assetbundle')
    std = os.path.join(tmpdir, 'copyright_std.assetbundle')
    enc = os.path.join(tmpdir, 'copyright_enc.assetbundle')

    decrypt_bundle(src_encrypted_path, dec)
    env = UnityPy.load(dec)

    objects, targets = _resolve_targets(env, log)
    if not targets:
        raise RuntimeError('Khong tim thay sprite/texture shop de them ban quyen.')

    grouped = defaultdict(list)
    for role, info in targets.items():
        grouped[info['texture_pid']].append((role, info))

    changed_roles = []
    for tex_pid, items in grouped.items():
        tex_reader = objects.get(tex_pid)
        if tex_reader is None:
            continue
        tex = tex_reader.read(return_typetree_on_error=False)
        img = tex.image.convert('RGBA')
        tex_w, tex_h = img.size
        edited = False

        for role, info in items:
            rect = info.get('rect') or {}
            box = _rect_to_box(rect, tex_w, tex_h)
            if box is None:
                box = (0, 0, tex_w, tex_h)
            region = img.crop(box)
            region = _overlay_text(region, spec['text'], spec['color'], spec['opacity'], role)
            img.paste(region, box)
            changed_roles.append(role)
            edited = True
            log('   BQ : %-8s <- %s' % (role, info['sprite_name']))

        if edited:
            mip_count = getattr(tex, 'm_MipCount', 1) or 1
            tex.set_image(img, target_format=tex.m_TextureFormat, in_cab=True,
                          mipmap_count=max(1, int(mip_count)))
            tex.save()

    if not changed_roles:
        raise RuntimeError('Khong sua duoc texture shop nao de them ban quyen.')

    missing = [r for r in SPRITE_TARGETS if r not in changed_roles]
    if missing:
        log('   ! BQ: thieu slot: %s' % ', '.join(missing))

    with open(std, 'wb') as f:
        f.write(env.file.save(packer='lzma'))
    encrypt_bundle(std, enc)
    return enc
