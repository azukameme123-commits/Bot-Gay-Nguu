# -*- coding: utf-8 -*-
"""
Loi ghep (graft engine) — hien thuc hoa AOV_battleotherui_graft_rules.md

FX  : R1 dò root · R2 root la neo rong · R3 mount an toan theo kieu node
JOY : S1 tro m_Sprite · S2 atlas/standalone · S3 inline texture · G1 mirror · G2 border
"""
import os, re, struct, tempfile

from .aovlib import UnityPy, decrypt_bundle, encrypt_bundle

# ---------------------------------------------------------------- hang so battleotherui
MOUNT_EFFECT   = -1052576695779864424      # Transform 'effect'
DEFAULT_CIRCLE = -6778797527077953754      # Transform 'circle' (FX mac dinh)

IMAGE_SCRIPT   = -7030229213176759517      # MonoScript UnityEngine.UI.Image
AXIS_IMAGE     = -4848959964831355422
AXIS_MIRROR    = 6485305281367891218       # MirrorImageEffect (m_Enabled @12)
BORDER_IMAGE   = -7503665643471169985
BORDER_RT      = -2799986137220178741
DECOR_R_IMAGE  = -8806829761678967762
DECOR_L_IMAGE  = -4911661404432915893
CURSOR_IMAGE   = -5387546953004491050
DECOR_GO       = [6206484994098663942, -5634152749686239543]   # DecorateRight / DecorateLeft

# slot 59901-style  ->  PathID sprite mac dinh trong battleotherui  (bang §4)
# battleotherui co HAI bo joystick:
#   Form_Battle_Part_Joystick    -> Joystick        (nut di chuyen, dang hien)
#   Form_Battle_Part_CameraMove  -> Joystick_Camera (keo camera, mac dinh tat)
# 3 sprite duoi day chi duoc dung boi dung 2 Image (moi bo 1) nen match theo
# sprite mac dinh la an toan va bat duoc CA HAI bo.
JOY_DEFAULT = {
    -7759551373688354208: 'CustomJoyStick_RockingBg',     # Battle_rockingBarBg  (Axis x2)
    -2764057117710524258: 'CustomJoyStick_RockingBar',    # Battle_rockingBar    (Cursor x2)
    5208577705698041403:  'CustomJoyStick_RockingArrow',  # Img_light_bar        (BorderIndicator x2)
}

# Nhung slot dung chung sprite placeholder 'default_pic' (369 Image dung chung!)
# thi BAT BUOC chi dich danh theo MonoBehaviour.
EXPLICIT_IMAGES = {
    DECOR_R_IMAGE:        'CustomJoyStick_Decorate',      # DecorateRight/DecorateImage
    DECOR_L_IMAGE:        'CustomJoyStick_Decorate',      # DecorateLeft/DecorateImage
    -578305678275466672:  'CustomJoyStick_RockingArrow',  # BorderIndicatorUp   164x144 (native)
    3798768872398327745:  'CustomJoyStick_RockingArrow',  # BorderIndicatorDown 164x144 (native)
}

SLOT_MAP = {
    'CustomJoyStick_Skill_FrameBg':           4521965459771754491,
    'CustomJoyStick_Skill_FrameBg_Six':       6506458135070959965,
    'CustomJoyStick_Skill_FrameBg_xi':        -713949546598136875,
    'CustomJoyStick_Skill_Projress_Big_1':   -5395921638815586778,
    'CustomJoyStick_Skill_Projress_Big_2':   -4903935140751036718,
    'CustomJoyStick_Skill_Projress_Big_3':   -2959032211592467614,
    'CustomJoyStick_Skill_Projress_Small_1': -8876048917458090228,
    'CustomJoyStick_Skill_Projress_Small_2': -6999763066223432891,
    'CustomJoyStick_Skill_Projress_Small_3':  5534646747319590423,
    'CustomJoyStick_Skill_Projress_Small_4': -2422750244921060046,
    'CustomJoyStick_Skill_Projress_Small_5':  1331825504267759371,
    'CustomJoyStick_Skill_Projress_Small_6': -6695676195481413409,
    'CustomJoyStick_AttackBtn':               3949139964913276237,
    'CustomJoyStick_SoldierAttackBtn':       -5915282664084471117,
    'CustomJoyStick_OrganAttackBtn':          3742358440233270382,
    'CustomJoyStick_LockHero':               -1928409702755600487,
    'CustomJoyStick_LockSoldier':            -7893426383174433136,
    'CustomJoyStick_LockBtnBg':              -6298055555695112407,
    # 2 slot duoi khong co doi ung trong battleotherui (nam o bundle UI shop)
    # 'CustomJoyStick_ShopIcon', 'BattleShop_Entrance_OnRight'
}

# Kich thuoc GOC (m_Rect) cua tung sprite mac dinh trong STOCK battleotherui,
# dung de tinh ty le bu meo (S1.5) -- quet 75/75 skin (2026-08-04) xac nhan
# da so skin khop dung kich thuoc nay, mot so it skin lech nhe 1-8px (vd
# 13213, 14111) gay meo nho do preserveAspect=false. KHONG dat sizeDelta ve
# dung 1:1 (nhieu Image dung CHUNG 1 sprite nhung co chu y hien thi o kich
# thuoc KHAC nhau, vd SkillFrame/SkillEnergy/LearnBtn) -- chi NHAN TY LE
# (kich_thuoc_skin / kich_thuoc_stock) vao sizeDelta hien co cua tung Image,
# giu nguyen thiet ke tuong doi giua cac Image.
STOCK_SPRITE_SIZE = {
    'CustomJoyStick_Skill_FrameBg':          (70.0, 70.0),
    'CustomJoyStick_Skill_Projress_Small_1': (40.0, 25.0),
    'CustomJoyStick_Skill_Projress_Small_2': (10.0, 48.0),
    'CustomJoyStick_Skill_Projress_Small_3': (40.0, 26.0),
    'CustomJoyStick_Skill_Projress_Small_4': (40.0, 26.0),
    'CustomJoyStick_Skill_Projress_Small_5': (10.0, 48.0),
    'CustomJoyStick_Skill_Projress_Small_6': (40.0, 25.0),
}

AXIS_SIZE_X   = 290.0      # sizeDelta cua 'Axis'

IMPORT_NAMES = set(SLOT_MAP) | set(EXPLICIT_IMAGES.values()) | set(JOY_DEFAULT.values())

ASSET_TYPES = {'Material', 'Texture2D', 'Shader', 'Mesh', 'AnimationClip', 'Sprite',
               'Cubemap', 'Font', 'TextAsset', 'AudioClip', 'MonoScript', 'AvatarMask',
               'RuntimeAnimatorController', 'AnimatorController', 'PhysicMaterial'}


class GraftError(Exception):
    pass


# ---------------------------------------------------------------- tien ich
def _clone(o):
    n = object.__new__(type(o))
    n.__dict__.update(o.__dict__)
    n.data = b''
    return n


def _raw(o):
    # QUAN TRONG: ObjectReader.get_raw_data() LUON doc lai tu file reader, bo qua
    # du lieu da set_raw_data(). Doc-sua-ghi 2 lan tren cung 1 object se mat lan ghi
    # dau. Phai uu tien o.data neu da co.
    d = getattr(o, 'data', None)
    if d:
        return bytes(d)
    return bytes(o.get_raw_data())


def _remap_tree(node, newid):
    """Doi moi PPtr trong 1 typetree dict theo bang newid {(fid,pid): newpid}."""
    if isinstance(node, dict):
        if 'm_FileID' in node and 'm_PathID' in node:
            k = (node['m_FileID'], node['m_PathID'])
            if k in newid:
                node['m_FileID'] = 0
                node['m_PathID'] = newid[k]
            return node
        for v in node.values():
            _remap_tree(v, newid)
    elif isinstance(node, (list, tuple)):
        for v in node:
            _remap_tree(v, newid)
    return node


def _tt(o):
    try:
        return o.read_typetree()
    except Exception:
        return None


def _sf(env):
    return list(env.objects)[0].assets_file


def _fresh_id(sf, base, reserved=None):
    pid = base
    taken = sf.objects
    while pid == 0 or pid in taken or (reserved is not None and pid in reserved):
        pid += 1
    if reserved is not None:
        reserved.add(pid)
    return pid


def _load(path, tmpdir, name):
    """Giai ma roi mo. Tra ve (env, duong_dan_da_giai_ma)."""
    dec = os.path.join(tmpdir, name)
    decrypt_bundle(path, dec)
    return UnityPy.load(dec), dec


# ---------------------------------------------------------------- quet PPtr
def _iter_pptr(raw, resolver):
    """Duyet raw, tra (offset, fileID, pathID) voi moi PPtr hop le."""
    n = len(raw)
    i = 0
    while i <= n - 12:
        fid = struct.unpack_from('<i', raw, i)[0]
        if 0 <= fid <= 32:
            pid = struct.unpack_from('<q', raw, i + 4)[0]
            if pid != 0 and resolver(fid, pid) is not None:
                yield i, fid, pid
                i += 12
                continue
        i += 1


# ---------------------------------------------------------------- FX
def graft_fx(tgt_env, eff_path, eff_raw_path, tmpdir, log=lambda s: None):
    """Bê subtree FX tu personalbuttoneffect_<ID> vao battleotherui."""
    sf_t = _sf(tgt_env)
    T = sf_t.objects

    eff_env, _ = _load(eff_path, tmpdir, 'eff.assetbundle')
    pools = {0: {o.path_id: o for o in eff_env.objects}}
    ext_paths = {}
    sf_e = _sf(eff_env)
    for idx, ex in enumerate(sf_e.externals, start=1):
        ext_paths[idx] = ex.path

    if eff_raw_path and os.path.isfile(eff_raw_path):
        raw_env, _ = _load(eff_raw_path, tmpdir, 'effraw.assetbundle')
        raw_cab = _sf(raw_env).name if hasattr(_sf(raw_env), 'name') else ''
        raw_objs = {o.path_id: o for o in raw_env.objects}
        for idx, p in ext_paths.items():
            if raw_cab and raw_cab in p:
                pools[idx] = raw_objs
                break
        else:
            # khong khop ten CAB -> gan vao external dau tien chua dung
            for idx in ext_paths:
                if idx not in pools:
                    pools[idx] = raw_objs
                    break

    def resolve(fid, pid):
        p = pools.get(fid)
        return p.get(pid) if p else None

    # --- R1: dò root
    root = None
    for pid, o in pools[0].items():
        if o.type.name not in ('Transform', 'RectTransform'):
            continue
        d = _tt(o)
        if not d or d['m_Father']['m_PathID'] != 0:
            continue
        g = pools[0].get(d['m_GameObject']['m_PathID'])
        gd = _tt(g) if g else None
        if gd and str(gd.get('m_Name', '')).lower() == 'attackbutton':
            root = (pid, o, d)
            break
    if root is None:
        raise GraftError("khong tim thay root 'AttackButton' trong file effect")

    rpid, robj, rd = root
    if len(rd['m_Children']) != 1:
        raise GraftError('root co %d child (mong doi 1)' % len(rd['m_Children']))
    fx_pid = rd['m_Children'][0]['m_PathID']

    # --- gom cay transform + GameObject + component
    keep = set()
    stack = [fx_pid]
    while stack:
        tp = stack.pop()
        if tp in keep:
            continue
        o = pools[0].get(tp)
        if o is None:
            continue
        d = _tt(o)
        if d is None:
            continue
        keep.add(tp)
        go = d['m_GameObject']['m_PathID']
        if go and go not in keep:
            keep.add(go)
            gd = _tt(pools[0][go])
            if gd:
                for c in gd.get('m_Component', []):
                    cp = c['component']['m_PathID']
                    if cp:
                        keep.add(cp)
        for c in d.get('m_Children', []):
            stack.append(c['m_PathID'])

    # --- dong bao asset (Material -> Shader/Texture, Mesh, AnimationClip ...)
    comp_ids = [p for p in list(keep) if pools[0].get(p) is not None]
    extra = {}          # (fid,pid) -> obj
    work = [(0, p) for p in comp_ids]
    seen = set(work)
    while work:
        fid, pid = work.pop()
        o = resolve(fid, pid)
        if o is None:
            continue
        for _, f2, p2 in _iter_pptr(_raw(o), resolve):
            o2 = resolve(f2, p2)
            if o2 is None or o2.type.name not in ASSET_TYPES:
                continue
            k = (f2, p2)
            if k in extra or (f2 == 0 and p2 in keep):
                continue
            extra[k] = o2
            if k not in seen:
                seen.add(k)
                work.append(k)

    # --- cap PathID moi
    newid = {}
    reserved = set()
    for p in sorted(keep):
        newid[(0, p)] = _fresh_id(sf_t, p, reserved)
    for k in sorted(extra):
        newid[k] = _fresh_id(sf_t, k[1], reserved)

    # --- map external cua nguon sang external cua dich (giu ref builtin)
    tgt_ext = {ex.path: i for i, ex in enumerate(_sf(tgt_env).externals, start=1)}
    ext_remap = {}
    for idx, p in ext_paths.items():
        if idx in pools:
            continue                                 # da noi hoa
        ext_remap[idx] = tgt_ext.get(p, 0)

    # --- copy + remap
    protos = {}
    for _o in list(sf_t.objects.values()):
        protos.setdefault(_o.type.name, _o)

    def proto_for(tname):
        return protos.get(tname)

    def ensure_type(src_obj):
        """Tra ve (type_id, serialized_type) trong file dich; them type moi neu thieu."""
        cid = src_obj.class_id
        for i, t in enumerate(sf_t.types):
            if getattr(t, 'class_id', None) == cid:
                return i, t
        st = src_obj.serialized_type
        if st is None:
            return None, None
        sf_t.types.append(st)
        log('   + them SerializedType %s' % src_obj.type.name)
        return len(sf_t.types) - 1, st

    src_all = {(0, p): pools[0][p] for p in keep if p in pools[0]}
    src_all.update(extra)

    for (fid, pid), o in src_all.items():
        raw = bytearray(_raw(o))
        for off, f2, p2 in list(_iter_pptr(bytes(raw), resolve)):
            k = (f2, p2)
            if k in newid:
                struct.pack_into('<i', raw, off, 0)
                struct.pack_into('<q', raw, off + 4, newid[k])
            else:
                # PPtr chac chan (da resolve duoc o nguon) nhung khong duoc copy sang
                # -> de nguyen se thanh con tro treo vao battleotherui => CRASH.
                struct.pack_into('<i', raw, off, 0)
                struct.pack_into('<q', raw, off + 4, 0)
        pr = proto_for(o.type.name)
        if pr is None:
            tid, st = ensure_type(o)
            if tid is None:
                log('   ! bo qua %s (khong dung duoc type)' % o.type.name)
                continue
            pr = next(iter(sf_t.objects.values()))
            n = _clone(pr)
            n.type_id = tid
            n.serialized_type = st
            n.class_id = o.class_id
            n.type = o.type
            protos.setdefault(o.type.name, n)
        else:
            n = _clone(pr)
        n.path_id = newid[(fid, pid)]
        sf_t.objects[n.path_id] = n
        n.set_raw_data(bytes(raw))

    # --- KIEM TRA AN TOAN TRUOC KHI MOUNT ---------------------------------
    # Dau hieu chac chan cua ban build gay crash: co ParticleSystemRenderer nhung
    # dong bao asset khong keo duoc Material/Shader/Texture nao sang. Khi do renderer
    # tro toi material khong ton tai -> magenta roi crash.
    n_psr = sum(1 for _, o in src_all.items() if o.type.name == 'ParticleSystemRenderer')
    n_mat = sum(1 for _, o in src_all.items() if o.type.name == 'Material')
    n_shd = sum(1 for _, o in src_all.items() if o.type.name == 'Shader')
    n_tex = sum(1 for _, o in src_all.items() if o.type.name == 'Texture2D')
    if n_psr and (n_mat == 0 or n_shd == 0):
        raise GraftError('dong bao asset khong day du — %d ParticleSystemRenderer nhung '
                         'chi %d Material / %d Shader / %d Texture2D'
                         % (n_psr, n_mat, n_shd, n_tex))

    # --- R2/R3: mount
    # LUU Y: khong duoc read_typetree() tren object vua clone — no doc lai du lieu cua
    # proto chu khong phai raw minh vua set. Phai lay tree tu NGUON roi remap.
    new_fx = newid[(0, fx_pid)]
    fxo = sf_t.objects.get(new_fx)
    if fxo is None:
        raise GraftError('transform FX khong duoc copy sang')
    d = _tt(pools[0][fx_pid])
    if d is None:
        raise GraftError('khong doc duoc transform FX o file nguon')
    _remap_tree(d, newid)
    d['m_Father'] = {'m_FileID': 0, 'm_PathID': MOUNT_EFFECT}
    if fxo.type.name == 'RectTransform':
        p = d['m_LocalPosition']
        d['m_AnchorMin'] = {'x': 0.5, 'y': 0.5}
        d['m_AnchorMax'] = {'x': 0.5, 'y': 0.5}
        d['m_AnchoredPosition'] = {'x': p['x'], 'y': p['y']}
    fxo.save_typetree(d)

    # effect.children = [FX] ; circle -> mo coi
    eo = T[MOUNT_EFFECT]
    ed = _tt(eo)
    old = [c['m_PathID'] for c in ed['m_Children']]
    ed['m_Children'] = [{'m_FileID': 0, 'm_PathID': new_fx}]
    eo.save_typetree(ed)
    if DEFAULT_CIRCLE in T and DEFAULT_CIRCLE in old:
        co = T[DEFAULT_CIRCLE]
        cd = _tt(co)
        cd['m_Father'] = {'m_FileID': 0, 'm_PathID': 0}
        cd['m_Children'] = []
        co.save_typetree(cd)

    log('   FX : %d object, mount %s' % (len(src_all), fxo.type.name))
    return len(src_all)


# ---------------------------------------------------------------- watermark
# Chi doi TEN Texture2D (m_Name) -- KHONG dung cho Sprite/GameObject vi
# nhung loai do co the bi game/tool tra theo ten (da xac nhan that voi
# 'BattleShop_Entrance_OnRight', xem shop_engine.py). Texture2D chi duoc
# Sprite/Material tro toi qua PathID, doi ten khong anh huong gi.
WATERMARK_TAG = 'AnnnDz'


def _rename_texture_raw(raw, new_name):
    """Doi truong m_Name (string dau tien: int32 do dai + UTF8 + align 4
    byte) trong raw bytes cua Texture2D. Tra ve raw KHONG doi neu bat
    thuong (an toan, khong lam hong texture)."""
    if len(raw) < 4:
        return raw
    name_len = struct.unpack_from('<i', raw, 0)[0]
    if name_len < 0 or 4 + name_len > len(raw):
        return raw
    old_end = 4 + name_len + ((-name_len) % 4)
    nb = new_name.encode('utf-8')
    pad = b'\x00' * ((-len(nb)) % 4)
    return struct.pack('<i', len(nb)) + nb + pad + raw[old_end:]


def _rename_same_length(raw, tag):
    """Doi NOI DUNG m_Name thanh 'tag' + byte rong, giu NGUYEN do dai byte
    cua chuoi goc (khong doi length-prefix, khong dich chuyen gi phia sau)
    -- an toan de dung trong fx_engine.py, noi cac buoc va PPtr phia sau
    dua theo vi tri byte tinh tu du lieu goc (doi do dai se lam lech het).
    Bo qua (tra ve raw goc) neu ten qua ngan khong du cho tag."""
    if len(raw) < 4:
        return raw
    name_len = struct.unpack_from('<i', raw, 0)[0]
    tag_b = tag.encode('utf-8')
    if name_len < len(tag_b) or 4 + name_len > len(raw):
        return raw
    filled = tag_b + b'\x00' * (name_len - len(tag_b))
    return raw[:4] + filled + raw[4 + name_len:]


# ---------------------------------------------------------------- JOYSTICK
def _inline_texture(tex_obj, log=lambda s: None):
    """S3 — nhet image data vao raw, xoa m_StreamData. Tra raw moi hoac None.

    Dung chung co che khoi phuc voi P()/fx_engine.py cho truong hop
    m_StreamData bi doc sai (xem _recover_shifted_stream_data).
    """
    raw = _raw(tex_obj)
    try:
        t = tex_obj.read()
        from .fx_engine import _recover_shifted_stream_data
        recovered = _recover_shifted_stream_data(tex_obj, t)
        if recovered is not None:
            raw_offset_bytes = struct.pack('<Q', int(t.m_StreamData.offset))
            pos = raw.rfind(raw_offset_bytes)
            if pos < 8:
                log('   ! CANH BAO: khoi phuc duoc anh nhung khong dinh vi duoc vi tri byte -- bo qua')
                return None
            head = raw[:pos - 4]
            # xem giai thich chi tiet trong fx_engine.P() -- vá m_PlatformBlob
            # rong bat thuong (0 byte) thanh 1 byte 0x00 cho khop cac texture
            # anh em khac, tranh crash that tren thiet bi.
            if head[-4:] == struct.pack('<I', 0):
                head = head[:-4] + struct.pack('<I', 1) + b'\x00\x00\x00\x00'
            log('   * KHOI PHUC anh Texture2D "%s" bi loi doc m_StreamData' % getattr(t, 'm_Name', '?'))
            return head + struct.pack('<I', len(recovered)) + recovered + struct.pack('<Q', 0) \
                + struct.pack('<I', 0) + struct.pack('<I', 0)
        img = bytes(t.image_data)
        if not img:
            return None
        path = t.m_StreamData.path or ''
        if not path:
            return raw                                   # da inline san
        plen = len(path.encode('utf8'))
        tail = 8 + 4 + 4 + plen                          # offset+size+strlen+chuoi
        tail += (-plen) % 4                              # align
        cut = 4 + tail                                   # +4 byte imageData-size (=0)
        head = raw[:len(raw) - cut]
        return head + struct.pack('<I', len(img)) + img + struct.pack('<Q', 0) \
            + struct.pack('<I', 0) + struct.pack('<I', 0)
    except Exception as ex:
        log('   ! CANH BAO: khong doc duoc anh Texture2D (pathID=%s, loi: %s) -- bo qua texture nay' % (
            getattr(tex_obj, 'path_id', '?'), ex))
        return None




def graft_joystick(tgt_env, spr_raw_path, tmpdir, log=lambda s: None):
    sf_t = _sf(tgt_env)
    T = sf_t.objects
    env, _ = _load(spr_raw_path, tmpdir, 'spr.assetbundle')
    S = {o.path_id: o for o in env.objects}

    sprites = {}
    for pid, o in S.items():
        if o.type.name != 'Sprite':
            continue
        d = _tt(o)
        if d:
            sprites[d['m_Name']] = (pid, d)
    if not sprites:
        raise GraftError('file sprite_raw khong co Sprite nao')

    # atlas map (neu co)
    rmap = {}
    for pid, o in S.items():
        if o.type.name != 'SpriteAtlas':
            continue
        sa = _tt(o)
        if sa:
            for k, v in sa.get('m_RenderDataMap', []):
                rmap[(tuple(k['first'].values()), k['second'])] = v

    # --- S3: inline moi texture duoc dung toi
    need_tex = set()
    for name, (pid, d) in sprites.items():
        if name not in IMPORT_NAMES:
            continue
        if d['m_SpriteAtlas']['m_PathID'] != 0:
            key = (tuple(d['m_RenderDataKey']['first'].values()), d['m_RenderDataKey']['second'])
            rd = rmap.get(key)
            if rd:
                need_tex.add(rd['texture']['m_PathID'])
        else:
            need_tex.add(d['m_RD']['texture']['m_PathID'])
    need_tex.discard(0)

    proto_tex = next((o for o in tgt_env.objects if o.type.name == 'Texture2D'), None)
    proto_spr = next((o for o in tgt_env.objects if o.type.name == 'Sprite'), None)
    if proto_tex is None or proto_spr is None:
        raise GraftError('battleotherui thieu kieu Texture2D/Sprite')

    tex_new = {}
    for tp in sorted(need_tex):
        if tp not in S:
            continue
        nb = _inline_texture(S[tp])
        if nb is None:
            continue
        nid = _fresh_id(sf_t, tp)
        # dat CUNG 1 ten cho MOI texture (khong con hau to rieng) -- co
        # chu dich: khi ai do dung tool export hang loat theo ten (vd
        # AssetStudio, luu file = m_Name.png) se bi TRUNG TEN hang loat,
        # de mat/de-ghi-de du lieu, gay kho khan cho viec dao lai sach se.
        nb = _rename_texture_raw(nb, WATERMARK_TAG)
        n = _clone(proto_tex)
        n.path_id = nid
        sf_t.objects[nid] = n
        n.set_raw_data(nb)
        tex_new[tp] = nid

    # --- S2: import sprite
    spr_new = {}
    for name in IMPORT_NAMES:
        if name not in sprites:
            continue
        pid, d = sprites[name]
        if d['m_SpriteAtlas']['m_PathID'] != 0:                      # S2-a
            key = (tuple(d['m_RenderDataKey']['first'].values()), d['m_RenderDataKey']['second'])
            rd = rmap.get(key)
            if rd is None:
                log('   ! %s: khong co trong RenderDataMap, bo qua' % name)
                continue
            for f in ('textureRect', 'textureRectOffset', 'atlasRectOffset',
                      'uvTransform', 'downscaleMultiplier', 'settingsRaw'):
                d['m_RD'][f] = rd[f]
            src_tex = rd['texture']['m_PathID']
        else:                                                        # S2-b
            src_tex = d['m_RD']['texture']['m_PathID']
        if src_tex not in tex_new:
            log('   ! %s: thieu texture, bo qua' % name)
            continue
        d['m_SpriteAtlas'] = {'m_FileID': 0, 'm_PathID': 0}
        d['m_AtlasTags'] = []
        d['m_RD']['texture'] = {'m_FileID': 0, 'm_PathID': tex_new[src_tex]}
        d['m_RD']['alphaTexture'] = {'m_FileID': 0, 'm_PathID': 0}
        nid = _fresh_id(sf_t, pid)
        n = _clone(proto_spr)
        n.path_id = nid
        sf_t.objects[nid] = n
        n.save_typetree(d)
        spr_new[name] = nid

    # --- S1: tro lai m_Sprite cua moi Image
    rev = {SLOT_MAP[n]: spr_new[n] for n in spr_new if n in SLOT_MAP}
    for old, name in JOY_DEFAULT.items():
        if name in spr_new:
            rev[old] = spr_new[name]

    # --- S1.5 (2026-08-04): bu meo nho cho cac sprite co kich thuoc anh
    # THAT cua skin lech vai px so voi anh mac dinh (preserveAspect=false
    # nen bi keo/bop nhe). CHI nhan ty le vao sizeDelta HIEN CO cua tung
    # Image, KHONG dat ve 1:1 -- vi nhieu Image dung CHUNG 1 sprite mac dinh
    # nhung co chu y hien thi o kich thuoc khac nhau (SkillFrame/SkillEnergy/
    # LearnBtn...), dat ve 1:1 se pha thiet ke do.
    slot_ratio_by_stockpid = {}
    for name, stock_pid in SLOT_MAP.items():
        if name not in STOCK_SPRITE_SIZE or name not in sprites:
            continue
        sw, sh = STOCK_SPRITE_SIZE[name]
        kr = sprites[name][1]['m_Rect']
        kw, kh = kr['width'], kr['height']
        if sw <= 0 or sh <= 0 or (abs(kw - sw) < 0.5 and abs(kh - sh) < 0.5):
            continue          # khop san voi mac dinh, khong can bu
        slot_ratio_by_stockpid[stock_pid] = (kw / sw, kh / sh, kw, kh)

    hit = 0
    resized = 0
    for mb, name in EXPLICIT_IMAGES.items():
        if mb not in T or name not in spr_new:
            continue
        raw = _raw(T[mb])
        if len(raw) < 100 or struct.unpack_from('<i', raw, 88)[0] != 0:
            continue
        b = bytearray(raw)
        struct.pack_into('<q', b, 92, spr_new[name])
        T[mb].set_raw_data(bytes(b))
        hit += 1
    for pid, o in list(sf_t.objects.items()):
        if o is None or o.type.name != 'MonoBehaviour':
            continue
        raw = _raw(o)
        if len(raw) < 100:
            continue
        if struct.unpack_from('<q', raw, 20)[0] != IMAGE_SCRIPT:
            continue
        if struct.unpack_from('<i', raw, 88)[0] != 0:
            continue
        cur = struct.unpack_from('<q', raw, 92)[0]
        if cur not in rev:
            continue
        ratio = slot_ratio_by_stockpid.get(cur)
        b = bytearray(raw)
        struct.pack_into('<q', b, 92, rev[cur])
        o.set_raw_data(bytes(b))
        hit += 1
        if ratio is not None:
            rw, rh, kw, kh = ratio
            go_pid = struct.unpack_from('<q', raw, 4)[0]
            go = T.get(go_pid)
            if go is not None:
                gt = go.read_typetree()
                for comp in gt.get('m_Component', []):
                    c_obj = T.get(comp['component']['m_PathID'])
                    if c_obj is not None and c_obj.type.name == 'RectTransform':
                        rt = c_obj.read_typetree()
                        old_sd = rt['m_SizeDelta']
                        rt['m_SizeDelta'] = {'x': old_sd['x'] * rw, 'y': old_sd['y'] * rh}
                        c_obj.save_typetree(rt)
                        log('   S1.5: bu meo %gx%g -> sizeDelta %gx%g -> %gx%g'
                            % (kw, kh, old_sd['x'], old_sd['y'],
                               rt['m_SizeDelta']['x'], rt['m_SizeDelta']['y']))
                        resized += 1
                        break

    # --- bat DecorateLeft / DecorateRight
    for g in DECOR_GO:
        if g in T:
            d = _tt(T[g])
            if d is not None:
                d['m_IsActive'] = True
                T[g].save_typetree(d)

    # --- G1: mirror theo kich thuoc RockingBg
    if 'CustomJoyStick_RockingBg' in sprites:
        w = sprites['CustomJoyStick_RockingBg'][1]['m_Rect']['width']
        mirror = abs(w - AXIS_SIZE_X / 2.0) < 0.5           # 145 => manh 1/4 => giu guong
        if AXIS_MIRROR in T:
            b = bytearray(_raw(T[AXIS_MIRROR]))
            b[12] = 1 if mirror else 0
            T[AXIS_MIRROR].set_raw_data(bytes(b))
        if AXIS_IMAGE in T:
            b = bytearray(_raw(T[AXIS_IMAGE]))
            if len(b) > 104:
                b[104] = 0 if mirror else 1                 # preserveAspect
            T[AXIS_IMAGE].set_raw_data(bytes(b))
        log('   G1 : RockingBg %gpx -> mirror=%s' % (w, 'ON' if mirror else 'OFF'))

    # --- G2: chinh RectTransform cua BorderIndicator cho khop RockingArrow
    #
    # 'BorderIndicator' (so it, BORDER_RT) moi la object THAT hien thi vien
    # chi huong keo joystick (xac nhan qua m_IsActive: BorderIndicatorUp/
    # Down = FALSE trong file goc, chi BorderIndicator = TRUE).
    #
    # RockingArrow la texture TINH -- GAME tu an/hien (mo khi khong keo,
    # hien khi keo) va tu xoay ca khoi quanh joystick theo huong keo, kich
    # thuoc khong bao gio doi. Vi vay KHONG duoc sua noi dung/kich thuoc
    # pixel cua sprite.
    #
    # LAN THU 1 (2026-08-04, DA BO): dat m_SizeDelta = dung kich thuoc goc
    # sprite (164x144). Test THAT cho ket qua xau hon ("keo doc").
    #
    # LAN THU 2 (2026-08-04): xac nhan duoc quy luat that qua 2 nguon doc
    # lap -- (a) sizeDelta GOC cua BorderIndicator (100x210) = dung GAP DOI
    # chieu cao anh RockingArrow MAC DINH (100x105); (b) texture hoan chinh
    # cua ban mod PUBLIC that (skin 15009, da fix loi nhoi ra) la 164x288 =
    # dung gap doi 144 (chieu cao anh RockingArrow cua rat nhieu skin,
    # trong do co 14111). Ca 2 deu khop quy luat "sizeDelta = (rong goc,
    # cao goc x2)" -- rat co the BorderIndicator chi thuc su hien thi/tinh
    # toan tren 1 NUA chieu cao sizeDelta (nua con lai do MirrorImageEffect
    # tu lat them vao), nen sizeDelta phai gap doi chieu cao anh moi khong
    # bi keo/bop. Ap dung: sizeDelta = (rong sprite, cao sprite x2).
    # LAN THU 3 (2026-08-04, DA BO): giu scale=1/anchorX=132 y het stock.
    # Test that: kich thuoc dung nhung "bay ra" khoi joystick theo chieu
    # doc -- vi pivot cua RectTransform la tam (0.5,0.5), neo (anchorX=132)
    # tinh cho khung GOC 100x210; khung moi 164x288 to hon nhung van neo
    # dung tam do nen phinh ra moi huong nhieu hon (ca ngang lan doc).
    #
    # LAN THU 4 (2026-08-04, DA BO cong thuc "82 + w/2"): du doan anchorX=164
    # cho 14111 -- test that lai xa hon, SAI cong thuc. Test tay nhieu gia
    # tri (60/82/100/120/140/164) tren cung 1 file da build (chi patch
    # anchoredPosition, khong build lai) cho thay 82 la gia tri KHOP THAT
    # (60 hoi lo vao trong, 164 xa) -- khong khop du doan hinh hoc don
    # gian cua toi (co the do MirrorImageEffect anh huong them, chua ro).
    #
    # Quet toan bo 75/75 skin xac nhan RockingArrow LUON dung 164x144 --
    # khong co skin nao khac kich thuoc, nen KHONG can cong thuc theo w/h,
    # dung thang 1 hang so co dinh.
    #
    # LAN THU 5 (2026-08-04): anchorX=82 con lech nhe (test that + do anh
    # chup that cung do phan giai, dung khoang-cach-tuyet-doi-vuot-mep-nut
    # thay vi ty le -- ty le khuech dai nhieu qua muc). Ket qua do: anchorX
    # dung ~77. Neu sau nay muon chinh lai, SUA THANG SO NAY (hang so code,
    # khong doc file/config ngoai -- theo yeu cau nguoi dung 2026-08-04).
    ARROW_ANCHOR_X = 77.0
    if 'CustomJoyStick_RockingArrow' in sprites and BORDER_RT in T:
        r = sprites['CustomJoyStick_RockingArrow'][1]['m_Rect']
        d = _tt(T[BORDER_RT])
        if d is not None:
            new_w = r['width']
            new_h = r['height'] * 2.0
            d['m_SizeDelta'] = {'x': new_w, 'y': new_h}
            d['m_AnchoredPosition'] = {'x': ARROW_ANCHOR_X, 'y': 0.0}
            T[BORDER_RT].save_typetree(d)
            log('   G2 : arrow %gx%g -> sizeDelta %gx%g, anchorX %g'
                % (r['width'], r['height'], new_w, new_h, ARROW_ANCHOR_X))

    log('   JOY: %d sprite, %d texture, %d Image da tro lai, %d sizeDelta da bu meo'
        % (len(spr_new), len(tex_new), hit, resized))
    return len(spr_new), hit


# ---------------------------------------------------------------- dieu phoi
