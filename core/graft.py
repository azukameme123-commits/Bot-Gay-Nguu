# -*- coding: utf-8 -*-
"""
Bo dieu phoi (orchestrator) — PHIEN BAN MOD TRUC TIEP 2 NEN TANG (v4).

Thay doi lon so voi v3 (KHONG CON CONVERT iOS):
  v3: mod 1 lan tren bundle ANDROID -> save ADR -> "convert" (copy bytes da
      mod, chi doi byte platform) thanh iOS.
  v4: mod 2 LAN DOC LAP tren dung file nen tang cua no:
      - Android: decrypt+mod tren  Button/Android/battleotherui.assetbundle
      - iOS    : decrypt+mod tren  Button/IOS/battleotherui.assetbundle
      Moi platform duoc load thanh 1 env rieng, chay dung pipeline mod goc
      (FX -> copyright -> JOY), roi save + ma hoa Plok (lib/Protect.py).
      KHONG con bat ky buoc "convert" nao — moi file iOS la ket qua mod
      truc tiep tren chinh file goc iOS.

Tai sao mod truc tiep iOS an toan (da probe 2026-08-06):
  * Button/Android/battleotherui.assetbundle va Button/IOS/battleotherui.assetbundle
    co externals GIONG HET nhau (10 fid, cung thu tu), va moi PathID neo
    (MOUNT_EFFECT / DEFAULT_CIRCLE / JOY_DEFAULT / SLOT_MAP / EXPLICIT_IMAGES /
    DECOR_GO / AXIS_* / BORDER_*) deu ton tai giong nhau o ca hai. Nen chay
    cung 1 engine mod tren 2 env la hop le, khong tro treo PPtr.
  * platform Android = 0x0D (13), iOS = 0x09 (9) — duoc set tu dong boi co
    useADR/useIOS cua fork UnityPy luc save (xem _save_platform).

Giu nguyen 100% cach mod cua Android (FX graft, joystick graft, shop graft,
copyright, fix_timelife) — chi thay phan dieu phoi platform.

iOS-SHADER-FIX (thay the cho buoc convert cu):
  Khi mod truc tiep iOS, material FX watermark ('DnTurboCuTo') duoc graft nguyen
  tu bundle Android co the tro shader chi ton tai tren Android -> iOS (Metal)
  fallback ra o hong magenta. Fix: remap shader sang shader IOS-SAFE da co
  san trong bundle (signature tex_env) + dam bao _MainTex duoc bind.
  (Ke thua nguyen logic _fix_fx_materials_ios tu v3 — voi v3 fix nay chay
  truoc khi save iOS tu env Android, voi v4 no chay TRUC TIEP tren env iOS.)

LUU Y (behavior UnityPy fork nay):
  watermark rename ('DnTurboCuTo') duoc fx_engine ghi THANG vao buffer raw bang
  set_raw_data(); read_typetree()/get_raw_data() trong CUNG PHIEN van tra
  du lieu CU tu reader goc. Vi vay ham fix doc/sua TRUC TIEP tren obj.data.

Moi platform hoan toan doc lap: neu 1 platform loi, platform kia van duoc
build va log rieng.
"""
import os, shutil, struct, tempfile

from .aovlib import UnityPy, decrypt_bundle, encrypt_bundle
from . import fx_engine
from . import joy_engine
from . import shop_engine
from . import copyright_engine

GraftError = joy_engine.GraftError


# ---------------------------------------------------------------- iOS shader map
# Cac shader nay DEU la external reference (fid=3) toi 1 CAB neighbor da duoc
# client iOS AOV load san, va DEU dang duoc it nhat 1 material GOC trong
# chinh bundle battleotherui.assetbundle nay dung (co Metal program san).
_IOS_SHADER_PARTICLE_ADD  = {'m_FileID': 3, 'm_PathID': 8043390017854118909}   # {_AlphaTex, _MainTex}
_IOS_SHADER_UI_ADD        = {'m_FileID': 3, 'm_PathID': 2760929606058318369}   # {_MainTex} - TransparentADD
_IOS_SHADER_UI_GLOW       = {'m_FileID': 3, 'm_PathID': -1149945574095256194}  # {_MainTex} - UI Glow
_IOS_SHADER_FX_ALPHA      = {'m_FileID': 3, 'm_PathID': 3473876783390398989}   # {_AlphaTex, _MainTex}
_IOS_SHADER_DUAL_TEX      = {'m_FileID': 3, 'm_PathID': -6828744275826868191}  # {_MainTex1, _MainTex2}
_IOS_SHADER_FX_TEX        = {'m_FileID': 3, 'm_PathID': -4653056259897887417}  # {_FXTex, _MainTex}
_IOS_SHADER_STD_STAR      = {'m_FileID': 3, 'm_PathID': 4880038547339996212}   # {_MainTex1, _MainTex2}

# Sprites-Default builtin (fid=7) — CHI last resort UI-only.
_IOS_FALLBACK_SPRITE = {'m_FileID': 7, 'm_PathID': 10753}

# Cac shader pid DA CO SAN Metal program tren client iOS — duoc chinh cac
# material GOC trong Button/IOS/battleotherui.assetbundle tham chieu (da probe
# thuc te 2026-08-06). Material FX nao da tro toi 1 trong cac shader nay thi
# GIU NGUYEN — remap chi lam hong (vd material alpha-blend 3473876783390398989
# tung bi remap sang particle ADD 8043390017854118909 -> lop do sang gap doi).
_IOS_NATIVE_SAFE_PIDS = frozenset((
    8043390017854118909,    # Particles/Additive      {_AlphaTex,_MainTex}
    3473876783390398989,    # Particles/Alpha Blended {_AlphaTex,_MainTex}
    2760929606058318369,    # UI TransparentADD       {_MainTex}
    -1149945574095256194,   # UI Glow (dissolve)      {_DissolveTex,_MainTex,...}
    -2154767994993168740,   # Equip Energy (mask kep) {_MainTex,_Mask1,_Mask2}
    -5999790399801098967,   # EF glow                 {_MainTex}
    -7620555118531013186,   # Particle vibrate        {_MainTex}
    5901460679245250462,    # Image mask              {_MainTex,_MaskTex}
    7487546758742308587,    # native khac
))


def _parse_material_layout(raw):
    """Parse cau truc Material -> dict offset cac field can sua (xem v3)."""
    try:
        if len(raw) < 20:
            return None
        nl = struct.unpack_from('<i', raw, 0)[0]
        if not (0 < nl <= 128 and 4 + nl <= len(raw)):
            return None
        off = (4 + nl + 3) & ~3
        shader_off = off
        off += 12
        # vec ValidKeywords
        n = struct.unpack_from('<i', raw, off)[0]; off += 4
        if not (0 <= n < 4096):
            return None
        for _ in range(n):
            sl = struct.unpack_from('<i', raw, off)[0]; off += 4
            if sl < 0 or off + sl > len(raw):
                return None
            off += sl
            off = (off + 3) & ~3
        # vec InvalidKeywords
        n = struct.unpack_from('<i', raw, off)[0]; off += 4
        if not (0 <= n < 4096):
            return None
        for _ in range(n):
            sl = struct.unpack_from('<i', raw, off)[0]; off += 4
            if sl < 0 or off + sl > len(raw):
                return None
            off += sl
            off = (off + 3) & ~3
        off += 4 + 1 + 1                                  # lightmap flags + 2 bool
        off = (off + 3) & ~3
        off += 4                                          # customRenderQueue
        # stringTagMap
        n = struct.unpack_from('<i', raw, off)[0]; off += 4
        if not (0 <= n < 4096):
            return None
        for _ in range(n):
            sl = struct.unpack_from('<i', raw, off)[0]; off += 4
            if sl < 0 or off + sl > len(raw):
                return None
            off += sl
            off = (off + 3) & ~3
            sl = struct.unpack_from('<i', raw, off)[0]; off += 4
            if sl < 0 or off + sl > len(raw):
                return None
            off += sl
            off = (off + 3) & ~3
        # disabledShaderPasses
        n = struct.unpack_from('<i', raw, off)[0]; off += 4
        if not (0 <= n < 4096):
            return None
        for _ in range(n):
            sl = struct.unpack_from('<i', raw, off)[0]; off += 4
            if sl < 0 or off + sl > len(raw):
                return None
            off += sl
            off = (off + 3) & ~3
        # m_TexEnvs
        n_tex = struct.unpack_from('<i', raw, off)[0]; off += 4
        if not (0 <= n_tex < 4096):
            return None
        tex_envs = []
        for _ in range(n_tex):
            sl = struct.unpack_from('<i', raw, off)[0]; off += 4
            if sl < 0 or off + sl > len(raw):
                return None
            name = raw[off:off+sl].decode('utf-8', errors='replace')
            off += sl
            off = (off + 3) & ~3
            off_tex_ptr = off
            fid, pid = struct.unpack_from('<iq', raw, off)
            off += 12
            off += 16                                     # scale + offset
            tex_envs.append({'name': name, 'tex_fid': fid, 'tex_pid': pid,
                             'off_tex_ptr': off_tex_ptr})
        return {'shader_off': shader_off, 'tex_envs': tex_envs}
    except Exception:
        return None


def _pick_ios_shader(tex_env_names, cur_fid, cur_pid):
    """Chon shader iOS-SAFE cho material FX. Tra ve None neu shader hien tai
    da iOS-native (GIU NGUYEN, khong remap).

    LY DO PHAI VIET LAI (bug 'choi/dam, khong dung mod that' tren iOS):
      Ban cu remap MOI material chi co _MainTex — gom ca nhom dissolve/distort
      von la shader ALPHA-BLEND — sang _IOS_SHADER_UI_ADD (TransparentADD,
      Blend One One). Blend ADD cong don do sang cua TUNG lop FX chong len
      nhau -> toan bo hieu ung bi 'chay sang' (overexposed), mat dissolve
      mask, mat hinh the goc. Tren skin 59903: 9/11 material FX bi ep sang
      ADD, 1 material alpha-blend native bi day sang particle ADD -> chi con
      dung 1/11 lop render dung y tac gia.
      Fix: shader da native (co Metal program san) thi giu nguyen; shader LA
      (dissolve/distort/detail/dual-dissolve/local default...) remap sang FX
      ALPHA-BLEND 3473876783390398989 (alpha-blend, co Metal program san vi
      chinh material goc iOS 'EF_HeroKey_ring' dang dung). Cac tex phu
      (_DissolveTex, _DistortTex, _DetailTex...) khong trung ten property se
      bi Metal bo qua an toan, _MainTex van bind binh thuong -> giu dung
      hinh the + do sang tac gia, het choi. Chi giu duong DUAL_TEX/FX_TEX cu
      cho cac chu ky 2-texture dac biet (khong co shader iOS-native thay the)."""
    if cur_fid == 3 and cur_pid in _IOS_NATIVE_SAFE_PIDS:
        return None
    s = set(tex_env_names)
    if '_MainTex1' in s and '_MainTex2' in s:
        return _IOS_SHADER_DUAL_TEX
    if '_FXTex' in s and '_MainTex' in s:
        return _IOS_SHADER_FX_TEX
    return _IOS_SHADER_FX_ALPHA


def _find_valid_maintex_source(env_objects):
    """Tim 1 PPtr _MainTex hop le (uu tien texture watermark 'DnTurboCuTo')."""
    tag = joy_engine.WATERMARK_TAG.encode('utf-8')
    fallback = None
    for obj in env_objects:
        if obj.type.name != 'Texture2D':
            continue
        raw_data = getattr(obj, 'data', None)
        raw = bytes(raw_data) if raw_data else None
        if raw and len(raw) >= 4:
            try:
                nl = struct.unpack_from('<i', raw, 0)[0]
                if 0 < nl < 128 and raw[4:4+nl].startswith(tag):
                    return {'m_FileID': 0, 'm_PathID': obj.path_id}
            except Exception:
                pass
        if fallback is None:
            fallback = {'m_FileID': 0, 'm_PathID': obj.path_id}
    return fallback


def _fix_fx_materials_ios(env, log=lambda s: None):
    """Remap shader + bind _MainTex cho moi material FX watermark 'DnTurboCuTo'.
    Chay TRUC TIEP tren env iOS (doc/sua obj.data da set_raw_data).
    Tra ve so shader da remap."""
    tag = joy_engine.WATERMARK_TAG.encode('utf-8')
    n_shader = 0
    n_tex_fixed = 0
    n_skip = 0
    n_keep = 0

    obj_list = list(env.objects)
    fallback_tex = _find_valid_maintex_source(obj_list)

    for obj in obj_list:
        if obj.type.name != 'Material':
            continue
        raw_data = getattr(obj, 'data', None)
        if not raw_data:
            continue
        raw = bytes(raw_data)
        if len(raw) < 20:
            continue
        nl = struct.unpack_from('<i', raw, 0)[0]
        if not (0 < nl <= 128 and 4 + nl <= len(raw)):
            continue
        name = raw[4:4+nl]
        if not name.startswith(tag):
            continue

        info = _parse_material_layout(raw)
        if info is None:
            n_skip += 1
            continue

        buf = bytearray(raw)

        tex_names = [t['name'] for t in info['tex_envs']]
        cur_fid, cur_pid = struct.unpack_from('<iq', raw, info['shader_off'])
        target = _pick_ios_shader(tex_names, cur_fid, cur_pid)
        if target is None:
            n_keep += 1
        elif (cur_fid, cur_pid) != (target['m_FileID'], target['m_PathID']):
            struct.pack_into('<iq', buf, info['shader_off'],
                             target['m_FileID'], target['m_PathID'])
            n_shader += 1

        for te in info['tex_envs']:
            if te['name'] != '_MainTex':
                continue
            if te['tex_fid'] == 0 and te['tex_pid'] == 0 and fallback_tex is not None:
                struct.pack_into('<iq', buf, te['off_tex_ptr'],
                                 fallback_tex['m_FileID'],
                                 fallback_tex['m_PathID'])
                n_tex_fixed += 1

        if bytes(buf) != raw:
            obj.set_raw_data(bytes(buf))

    if n_shader or n_tex_fixed or n_keep:
        log('   iOS FIX : remap %d shader sang ALPHA-BLEND / giu nguyen %d shader native / bind %d _MainTex (chong choi sang + o hong)'
            % (n_shader, n_keep, n_tex_fixed))
    if n_skip:
        log('   iOS FIX : bo qua %d material FX parse fail (giu shader cu)'
            % n_skip)
    return n_shader


graft_fx = fx_engine.m
graft_joystick = joy_engine.graft_joystick
graft_shop = shop_engine.graft_shop

SHOP_BUNDLES = ['battlecommon.assetbundle', 'battlecommon_raw.assetbundle']


def _set_platform(bundle_file, platform):
    """Set co useIOS / useADR TRUOC khi save (fork UnityPy se set
    _m_target_platform = 0x09 (iOS) hoac 0x0D (Android) cho moi SerializedFile)."""
    if not hasattr(bundle_file, 'useADR') or not hasattr(bundle_file, 'useIOS'):
        raise RuntimeError('BundleFile trong lib/UnityPy khong ho tro useADR/useIOS.')
    bundle_file.useADR = (platform == 'adr')
    bundle_file.useIOS = (platform == 'ios')


def _save_platform(env_file, platform, tmpdir, tag):
    """Save 1 lan cho 1 platform -> file std (chua ma hoa Plok).
    packer='lz4' de sinh dataflags=0x642 giong bundle goc."""
    _set_platform(env_file, platform)
    out_std = os.path.join(tmpdir, 'out_%s_%s.assetbundle' % (platform, tag))
    with open(out_std, 'wb') as f:
        f.write(env_file.save(packer='lz4'))
    return out_std


# ---------------------------------------------------------------- dieu phoi 1 platform
def _build_battle_ui_platform(base_bundle, platform, files, skin_id, out_path,
                              sprite_raw_for_build, tmpdir, log, step, tag):
    """Mod truc tiep battleotherui.assetbundle cua 1 platform.

    base_bundle : duong dan file Plok GOC cua platform do
                  (Button/Android/... hoac Button/IOS/...)
    platform    : 'adr' | 'ios'
    Tra ve kich thuoc file output (byte).
    """
    # 1) Decrypt bundle nen tang goc
    base = os.path.join(tmpdir, 'base_%s.assetbundle' % tag)
    decrypt_bundle(base_bundle, base)
    step()

    env = UnityPy.load(base)
    step()

    # 2) Mount FX (cach mod GOC — giu nguyen)
    fx_max_duration = None
    fx_has_mesh = False
    if files.get('effect'):
        _fx_root, fx_max_duration, fx_has_mesh = fx_engine.m(
            env, files['effect'], files.get('effect_raw'), tmpdir, log)
    step()

    fx_engine.fix_timelife(env, log, fx_max_duration, fx_has_mesh)

    # 3) Mount JOYSTICK (cach mod GOC — giu nguyen)
    if sprite_raw_for_build:
        joy_engine.graft_joystick(env, sprite_raw_for_build, tmpdir, log)
    step()

    # 4) iOS-SHADER-FIX: chi ap dung cho env iOS (thay buoc convert cu).
    #    Android giu nguyen shader goc cua skin.
    if platform == 'ios':
        _fix_fx_materials_ios(env, log)

    # 5) Save platform + ma hoa Plok bang Protect.py
    std = _save_platform(env.file, platform, tmpdir, 'ui_' + tag)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    encrypt_bundle(std, out_path)
    size = os.path.getsize(out_path)
    log('   %s saved (Plok): %s (%.2f MB)'
        % ('Android' if platform == 'adr' else 'iOS    ',
           os.path.basename(out_path), size / 1048576.0))
    step()
    return size


def _build_shop_platform(src_encrypted, sprite_raw, out_dir, platform,
                         name, tmpdir, log, tag):
    """Mod battlecommon*.assetbundle TRUC TIEP cho 1 platform roi ma hoa Plok.

    shop_engine.graft_shop tu lam tron 1 luot: decrypt(src) -> load -> mod
    -> save -> ma hoa Plok ra tmp_out. Vi src la file GOC cua dung platform
    do (Button/Android/... hoac Button/IOS/...) va graft_shop KHONG doi co
    platform khi save, nen tmp_out giu dung _m_target_platform cua platform
    do (ADR=0x0D / iOS=0x09). Chi can chuyen file ket qua vao output.
    """
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, name)
    tmp_out = os.path.join(tmpdir, 'shop_out_%s_%s.assetbundle' % (platform, tag))
    n = shop_engine.graft_shop(src_encrypted, sprite_raw, tmp_out, tmpdir,
                               log, tag='%s_%s' % (platform, tag))
    if n and os.path.isfile(tmp_out):
        shutil.move(tmp_out, dst)
        log('   Shop %s: %s (mod %d slot + Plok)'
            % ('ADR' if platform == 'adr' else 'iOS', name, n))
    else:
        # Khong co slot shop nao trong bundle nay -> giu nguyen file goc cua
        # CHINH platform do (copy thang, khong doi platform, khong convert).
        shutil.copy2(src_encrypted, dst)
        log('   Shop %s: %s (khong co slot, copy nguyen ban %s)'
            % ('ADR' if platform == 'adr' else 'iOS', name, platform))


def _copy_raw_platform(src_encrypted, out_dir, name, log, platform):
    """battleotherui_raw: khong mod, copy nguyen file goc cua CHINH platform do."""
    if not os.path.isfile(src_encrypted):
        return False
    os.makedirs(out_dir, exist_ok=True)
    shutil.copy2(src_encrypted, os.path.join(out_dir, name))
    log('   %s raw: %s (copy nguyen ban, khong mod)'
        % ('ADR' if platform == 'adr' else 'iOS', name))
    return True


def build_one(skin_id, files, button_dir, out_android, out_ios,
              log=lambda s: None, step=lambda: None,
              out_dir_android=None, out_dir_ios=None,
              copyright_spec=None):
    """Ghep 1 skin -> mod truc tiep tren file nen tang cua Android VA iOS.

    button_dir : thu muc Button/ (chua 2 thu muc con Android/ va IOS/)
    Tra ve (size_adr, size_ios, errs) — errs la dict {platform: loi} neu co.
    """
    adr_dir = os.path.join(button_dir, 'Android')
    ios_dir = os.path.join(button_dir, 'IOS')

    errs = {}
    size_adr = 0
    size_ios = 0

    with tempfile.TemporaryDirectory() as tmp:
        # ===== COPYRIGHT (dung chung cho ca 2 platform, patch 1 lan) =====
        sprite_raw_for_build = files.get('sprite_raw')
        if sprite_raw_for_build and copyright_spec:
            sprite_raw_for_build = copyright_engine.patch_sprite_bundle(
                sprite_raw_for_build, tmp, copyright_spec, log)
            log('   BQ      saved: personalbuttonsprite_%s_raw.assetbundle' % skin_id)

        # ===== ANDROID =====
        adr_ui = os.path.join(adr_dir, 'battleotherui.assetbundle')
        if os.path.isfile(adr_ui):
            try:
                size_adr = _build_battle_ui_platform(
                    adr_ui, 'adr', files, skin_id, out_android,
                    sprite_raw_for_build, tmp, log, step, 'a')
            except Exception as e:
                errs['adr'] = str(e)
                log('   [X] Android battleotherui LOI: %s' % e)
        else:
            errs['adr'] = 'thieu Button/Android/battleotherui.assetbundle'
            log('   [X] thieu Button/Android/battleotherui.assetbundle')

        # ===== iOS (mod truc tiep tren file iOS — KHONG convert) =====
        ios_ui = os.path.join(ios_dir, 'battleotherui.assetbundle')
        if os.path.isfile(ios_ui):
            try:
                size_ios = _build_battle_ui_platform(
                    ios_ui, 'ios', files, skin_id, out_ios,
                    sprite_raw_for_build, tmp, log, step, 'i')
            except Exception as e:
                errs['ios'] = str(e)
                log('   [X] iOS battleotherui LOI: %s' % e)
        else:
            errs['ios'] = 'thieu Button/IOS/battleotherui.assetbundle'
            log('   [X] thieu Button/IOS/battleotherui.assetbundle')

        # ===== SHOP: battlecommon* — mod truc tiep tung platform =====
        if sprite_raw_for_build:
            for i, name in enumerate(SHOP_BUNDLES):
                # Android
                src_adr = os.path.join(adr_dir, name)
                if out_dir_android and os.path.isfile(src_adr):
                    try:
                        _build_shop_platform(src_adr, sprite_raw_for_build,
                                             out_dir_android, 'adr', name,
                                             tmp, log, 's%d' % i)
                    except Exception as e:
                        log('   ! Shop ADR %s LOI: %s — copy nguyen ban' % (name, e))
                        os.makedirs(out_dir_android, exist_ok=True)
                        shutil.copy2(src_adr, os.path.join(out_dir_android, name))
                # iOS
                src_ios = os.path.join(ios_dir, name)
                if out_dir_ios and os.path.isfile(src_ios):
                    try:
                        _build_shop_platform(src_ios, sprite_raw_for_build,
                                             out_dir_ios, 'ios', name,
                                             tmp, log, 's%d' % i)
                    except Exception as e:
                        log('   ! Shop iOS %s LOI: %s — copy nguyen ban' % (name, e))
                        os.makedirs(out_dir_ios, exist_ok=True)
                        shutil.copy2(src_ios, os.path.join(out_dir_ios, name))

        # ===== battleotherui_raw: khong mod, copy nguyen tung platform =====
        raw_name = 'battleotherui_raw.assetbundle'
        if out_dir_android:
            _copy_raw_platform(os.path.join(adr_dir, raw_name),
                               out_dir_android, raw_name, log, 'adr')
        if out_dir_ios:
            _copy_raw_platform(os.path.join(ios_dir, raw_name),
                               out_dir_ios, raw_name, log, 'ios')
        step()

    return size_adr, size_ios, errs
