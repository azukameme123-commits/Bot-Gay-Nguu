# -*- coding: utf-8 -*-
"""
Nhanh SHOP — thay icon cua hang trong battlecommon / battlecommon_raw.

Vi sao lam kieu GHI DE TAI CHO (in-place) chu khong import sprite moi roi tro PPtr
nhu ben joystick:

  * `BattleShop_Entrance` (96x116) co dung 1 Image tro tinh — GameObject `EquipBtn`.
  * `BattleShop_Entrance_OnRight` (104x56) thi KHONG Image nao tro tinh. Game doi
    sprite nay luc runtime (khi nut cua hang nam ben phai). Khong co PPtr tinh de
    tro lai => bat buoc phai ghi de chinh object sprite do.

Ghi de tai cho giu nguyen PathID va m_Name, nen:
  - moi Image dang tro toi no van tro dung
  - m_Container / lookup theo ten cua game van chay
  - khong them object, khong phai remap PPtr  -> it rui ro nhat

Cung ap dung mot cach cho ca hai slot de hanh vi nhat quan.
"""
import os

from .aovlib import UnityPy, decrypt_bundle, encrypt_bundle
from .joy_engine import (GraftError, _raw, _tt, _clone, _sf, _fresh_id,
                         _inline_texture)

# ten sprite trong battlecommon  ->  ten slot trong personalbuttonsprite_<ID>_raw
SHOP_MAP = {
    'BattleShop_Entrance':         'CustomJoyStick_ShopIcon',           # 96x116  <- 95x115
    'BattleShop_Entrance_OnRight': 'BattleShop_Entrance_OnRight',       # 104x56  <- 104x55
}

# nhung field lay tu sprite cua skin; m_Name / m_RenderDataKey / m_PhysicsShape /
# m_Bones giu nguyen cua ban goc de moi tham chieu cu van hop le
COPY_FIELDS = ('m_Rect', 'm_Offset', 'm_Border', 'm_PixelsToUnits',
               'm_Pivot', 'm_Extrude', 'm_IsPolygon')

RD_FIELDS = ('textureRect', 'textureRectOffset', 'atlasRectOffset',
             'uvTransform', 'downscaleMultiplier', 'settingsRaw')


def _load_skin_sprites(spr_raw_path, tmpdir):
    """Doc personalbuttonsprite_<ID>_raw -> (env, {ten: (obj, tree)}, rmap)."""
    dec = os.path.join(tmpdir, 'shop_src.assetbundle')
    decrypt_bundle(spr_raw_path, dec)
    env = UnityPy.load(dec)
    S = {o.path_id: o for o in env.objects}

    sprites = {}
    for pid, o in S.items():
        if o.type.name != 'Sprite':
            continue
        d = _tt(o)
        if d:
            sprites[d['m_Name']] = (o, d)

    rmap = {}
    for pid, o in S.items():
        if o.type.name != 'SpriteAtlas':
            continue
        sa = _tt(o)
        if sa:
            for k, v in sa.get('m_RenderDataMap', []):
                rmap[(tuple(k['first'].values()), k['second'])] = v
    return env, S, sprites, rmap


def graft_shop(bundle_path, spr_raw_path, out_path, tmpdir,
               log=lambda s: None, tag=''):
    """Ghep icon shop vao mot bundle battlecommon*. Tra ve so slot da thay."""
    dec = os.path.join(tmpdir, 'shop_%s.assetbundle' % (tag or 'x'))
    decrypt_bundle(bundle_path, dec)
    env = UnityPy.load(dec)
    sf = _sf(env)
    T = sf.objects

    # co slot nao trong bundle nay khong?
    targets = {}
    for pid, o in list(T.items()):
        if o.type.name != 'Sprite':
            continue
        d = _tt(o)
        if d and d.get('m_Name') in SHOP_MAP:
            targets[d['m_Name']] = (o, d)
    if not targets:
        return 0

    senv, S, sprites, rmap = _load_skin_sprites(spr_raw_path, tmpdir)

    proto_tex = next((o for o in env.objects if o.type.name == 'Texture2D'), None)
    if proto_tex is None:
        raise GraftError('%s khong co kieu Texture2D' % os.path.basename(bundle_path))

    tex_new = {}     # pathid texture nguon -> pathid moi trong bundle dich
    done = 0

    for tname, (tobj, tdict) in targets.items():
        sname = SHOP_MAP[tname]
        if sname not in sprites:
            log('   ! shop: skin khong co %s, bo qua' % sname)
            continue
        sobj, sd = sprites[sname]

        # --- S2: xac dinh nguon texture + rect that
        if sd['m_SpriteAtlas']['m_PathID'] != 0:                     # atlas-backed
            key = (tuple(sd['m_RenderDataKey']['first'].values()),
                   sd['m_RenderDataKey']['second'])
            rd = rmap.get(key)
            if rd is None:
                log('   ! shop: %s khong co trong RenderDataMap, bo qua' % sname)
                continue
            src_tex = rd['texture']['m_PathID']
            rd_src = rd
        else:                                                        # standalone
            src_tex = sd['m_RD']['texture']['m_PathID']
            rd_src = sd['m_RD']

        if src_tex == 0 or src_tex not in S:
            log('   ! shop: %s thieu texture, bo qua' % sname)
            continue

        # --- S3: inline texture (moi texture chi inline 1 lan cho ca bundle)
        if src_tex not in tex_new:
            nb = _inline_texture(S[src_tex])
            if nb is None:
                log('   ! shop: khong inline duoc texture cua %s' % sname)
                continue
            nid = _fresh_id(sf, src_tex)
            n = _clone(proto_tex)
            n.path_id = nid
            sf.objects[nid] = n
            n.set_raw_data(nb)
            tex_new[src_tex] = nid

        # --- ghi de tai cho: giu m_Name + PathID, thay hinh hoc + m_RD
        for f in COPY_FIELDS:
            if f in sd and f in tdict:
                tdict[f] = sd[f]
        for f in RD_FIELDS:
            if f in rd_src:
                tdict['m_RD'][f] = rd_src[f]
        tdict['m_RD']['texture'] = {'m_FileID': 0, 'm_PathID': tex_new[src_tex]}
        tdict['m_RD']['alphaTexture'] = {'m_FileID': 0, 'm_PathID': 0}
        tdict['m_SpriteAtlas'] = {'m_FileID': 0, 'm_PathID': 0}
        tdict['m_AtlasTags'] = []
        tobj.save_typetree(tdict)
        done += 1
        log('   SHOP: %-28s <- %-30s %gx%g'
            % (tname, sname, sd['m_Rect']['width'], sd['m_Rect']['height']))

    if not done:
        return 0

    std = os.path.join(tmpdir, 'shop_out_%s.assetbundle' % (tag or 'x'))
    with open(std, 'wb') as f:
        f.write(env.file.save(packer='lzma'))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    encrypt_bundle(std, out_path)
    return done
