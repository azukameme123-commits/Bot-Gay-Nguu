import os as a, re as b, struct as i, tempfile as n, copy as f, colorsys as _colorsys
from .aovlib import UnityPy as j, decrypt_bundle as L, encrypt_bundle as M
from .joy_engine import _rename_same_length, WATERMARK_TAG
G = -1052576695779864424
K = -6778797527077953754
E = -7030229213176759517
s = -4848959964831355422
w = 6485305281367891218
B = -7503665643471169985
o = -2799986137220178741
I = -8806829761678967762
H = -4911661404432915893
D = -5387546953004491050
k = [6206484994098663942, -5634152749686239543]
O = {s: 'CustomJoyStick_RockingBg', B: 'CustomJoyStick_RockingArrow', I: 'CustomJoyStick_Decorate', H: 'CustomJoyStick_Decorate', D: 'CustomJoyStick_RockingBar'}
l = {'CustomJoyStick_Skill_FrameBg': 4521965459771754491, 'CustomJoyStick_Skill_FrameBg_Six': 6506458135070959965, 'CustomJoyStick_Skill_FrameBg_xi': -713949546598136875, 'CustomJoyStick_Skill_Projress_Big_1': -5395921638815586778, 'CustomJoyStick_Skill_Projress_Big_2': -4903935140751036718, 'CustomJoyStick_Skill_Projress_Big_3': -2959032211592467614, 'CustomJoyStick_Skill_Projress_Small_1': -8876048917458090228, 'CustomJoyStick_Skill_Projress_Small_2': -6999763066223432891, 'CustomJoyStick_Skill_Projress_Small_3': 5534646747319590423, 'CustomJoyStick_Skill_Projress_Small_4': -2422750244921060046, 'CustomJoyStick_Skill_Projress_Small_5': 1331825504267759371, 'CustomJoyStick_Skill_Projress_Small_6': -6695676195481413409, 'CustomJoyStick_AttackBtn': 3949139964913276237, 'CustomJoyStick_SoldierAttackBtn': -5915282664084471117, 'CustomJoyStick_OrganAttackBtn': 3742358440233270382, 'CustomJoyStick_LockHero': -1928409702755600487, 'CustomJoyStick_LockSoldier': -7893426383174433136, 'CustomJoyStick_LockBtnBg': -6298055555695112407}
x = 290.0
A = (164.0, 144.0)
C = 1.32
z = 90.0
F = set(l) | set(O.values())
v = {'Material', 'Texture2D', 'Shader', 'Mesh', 'AnimationClip', 'Sprite', 'Cubemap', 'Font', 'TextAsset', 'AudioClip', 'MonoScript', 'AvatarMask', 'RuntimeAnimatorController', 'AnimatorController', 'PhysicMaterial'}

class t(Exception):
    pass

# Renderer dung che do Mesh (renderMode==4) ke thua m_CustomRenderQueue mac
# dinh -1 (dung queue rieng cua shader) tu material chua duoc author queue
# rieng -> queue nay co the thap hon cac renderer Billboard lan can, khien
# no bi lop opaque cua nut de len tren. _QUEUE_FIX_VALUE la san queue toi
# thieu dung de gan lai cho nhom nay (xem _ordered_renderer_components_source).
_QUEUE_FIX_VALUE = 3100
_NAME_SUFFIX_RE = b.compile(r'\s*\(\d+\)$')


def _base_name(name):
    return _NAME_SUFFIX_RE.sub('', name or '')


def _skip_minmax_curve(data, off):
    """Doc 1 struct MinMaxCurve cua ParticleSystem (minMaxState UInt16 +
    pad 2 + scalar float + minScalar float + AnimationCurve maxCurve +
    AnimationCurve minCurve, moi AnimationCurve = SInt32 size + size*28
    byte Keyframe + 12 byte trailer m_PreInfinity/m_PostInfinity/
    m_RotationOrder). Offset xac dinh qua get_typetree_nodes() (nodes van
    doc duoc ke ca khi class nam trong _SKIP_TYPETREE_CLASSES, vi day chi
    la metadata cau truc chu khong phai doc gia tri qua read_typetree()).

    Tra ve (offset sau struct, gia tri lon nhat trong scalar/minScalar/
    keyframe.value). Lay max khong phan biet minMaxState: du lieu du van
    an toan hon du lieu thieu, vi doc thieu se lam hieu ung bi cat ngang.
    """
    scalar = i.unpack_from('<f', data, off + 4)[0]
    minScalar = i.unpack_from('<f', data, off + 8)[0]
    off2 = off + 12
    best = max(abs(scalar), abs(minScalar))
    for _c in range(2):
        size = i.unpack_from('<i', data, off2)[0]
        if size < 0 or size > 10000:
            raise ValueError('kich thuoc curve khong hop le: %d' % size)
        off2 += 4
        for k in range(size):
            val = i.unpack_from('<f', data, off2 + k * 28 + 4)[0]
            if abs(val) > best:
                best = abs(val)
        off2 += size * 28 + 12
    return off2, best


def _particle_system_total_time(data):
    """Tra ve max(lengthInSec, startLifetime) cua 1 ParticleSystem, doc
    truc tiep tu byte tho (class nam trong _SKIP_TYPETREE_CLASSES nen
    read_typetree() luon that bai). Offset tinh tu get_typetree_nodes().

    lengthInSec chi la do dai 1 chu ky PHAT HAT, khong phai thoi gian
    hien thi thuc te -- hat phat ra con song tiep toi startLifetime giay
    sau do. Dung rieng lengthInSec se lam hieu ung bi cat ngan neu chu ky
    phat ngan hon nhieu so voi doi song hat (vd lengthInSec=0.1s nhung
    startLifetime=5s). Cong ca hai lai la sai (nhan doi thoi gian that);
    lay max moi ra dung gia tri hien thi thuc te.
    """
    lengthInSec = i.unpack_from('<f', data, 12)[0]
    off = 12 + 4 + 4 + 4 + 4 + 4 + 8 + 4  # lengthInSec, simulationSpeed, stopAction, cullingMode, ringBufferMode, ringBufferLoopRange(Vector2f), emitterVelocityMode
    off += 5  # looping, prewarm, playOnAwake, useUnscaledTime, autoRandomSeed (5 bool)
    if off % 4:
        off += 4 - (off % 4)
    off, _ = _skip_minmax_curve(data, off)  # startDelay (khong can gia tri)
    off += 4 + 12 + 4 + 4  # moveWithTransform, moveWithCustomTransform PPtr, scalingMode, randomSeed
    off += 1  # InitialModule.enabled (bool)
    if off % 4:
        off += 4 - (off % 4)
    off, best_life = _skip_minmax_curve(data, off)  # startLifetime
    if not (0 <= lengthInSec <= 120) or not (0 <= best_life <= 120):
        raise ValueError('gia tri khong hop ly, co the offset sai cho ban nay')
    return max(lengthInSec, best_life)


def _max_particle_duration_source(T0, root_pathid, az=lambda s: None):
    """Quet cay Transform o file NGUON (T0 = aT[0]) de tinh thoi luong FX
    dai nhat. Phai chay tren cay nguon truoc khi mount, khong doc lai tu
    file dich sau khi ghi: ObjectReader cua UnityPy fork nay khong cap
    nhat nguon doc lai sau save_typetree()/set_raw_data() trong cung
    phien, nen doc lai object vua ghi se luon ra du lieu cu.

    Tra ve (duration_lon_nhat_hoac_None, co_MeshRenderer). co_MeshRenderer
    bao hieu noi dung chinh co the dua vao Animation thay vi ParticleSystem
    -- truong hop nay duration tinh duoc o day khong dang tin, xem
    fix_timelife() de biet cach xu ly.
    """
    aI2 = 0.0
    aHasMeshContent = False
    aJ2 = [root_pathid]
    aK2 = set()
    while aJ2:
        aL2 = aJ2.pop()
        if aL2 in aK2:
            continue
        aK2.add(aL2)
        Zt = T0.get(aL2)
        if Zt is None or Zt.type.name not in ('Transform', 'RectTransform'):
            continue
        Ut = d(Zt)
        if Ut is None:
            continue
        Zgo = T0.get(Ut['m_GameObject']['m_PathID'])
        Ugo = d(Zgo) if Zgo else None
        if Ugo:
            for T in Ugo.get('m_Component', []):
                Zc = T0.get(T['component']['m_PathID'])
                if Zc is None:
                    continue
                if Zc.type.name in ('MeshRenderer', 'SkinnedMeshRenderer'):
                    aHasMeshContent = True
                if Zc.type.name == 'ParticleSystem':
                    aM2 = bytes(Zc.get_raw_data())
                    aN2 = 0.0
                    try:
                        aN2 = _particle_system_total_time(aM2)
                    except Exception:
                        # fallback ve cach doc cu (chi lengthInSec) neu ban
                        # nay khong khop cau truc mong doi, de khong bao
                        # gio lam hong build vi 1 object le
                        if len(aM2) >= 16:
                            aN2 = i.unpack_from('<f', aM2, 12)[0]
                    if aN2 > aI2:
                        aI2 = aN2
        for T in Ut.get('m_Children', []):
            aJ2.append(T['m_PathID'])
    az('   TIME: (nguon) FX max duration=%.2fs%s' % (
        aI2, ' (CO MeshRenderer -- do dai co the bi thieu)' if aHasMeshContent else ''))
    return (aI2 if aI2 > 0 else None), aHasMeshContent



def _ordered_renderer_components_source(T0, root_pathid):
    """Duyet cay Transform o file NGUON va tra ve danh sach
    (component_pathid, ten_GameObject_da_bo_hau_to) cho moi component co
    'Renderer' trong ten (ParticleSystemRenderer, MeshRenderer, ...), sap
    xep theo Z CONG DON (tu FX root xuong toi transform so huu renderer)
    tang dan theo do gan camera -- Unity: Z cang am cang gan camera, nen
    phai ve sau cung (lop tren). Z cong don la tin hieu khach quan artist
    tu tay dat de kiem soat depth, dang tin cay hon thu tu liet ke trong
    Hierarchy. Bang nhau thi giu thu tu DFS pre-order lam tie-break.
    """
    aP2 = []
    aQ3 = [0]  # bo dem thu tu DFS lam tie-break on dinh

    def _walk(tid, zaccum):
        Zt = T0.get(tid)
        if Zt is None or Zt.type.name not in ('Transform', 'RectTransform'):
            return
        Ut = d(Zt)
        if Ut is None:
            return
        zHere = zaccum + Ut.get('m_LocalPosition', {}).get('z', 0.0)
        Zgo = T0.get(Ut['m_GameObject']['m_PathID'])
        Ugo = d(Zgo) if Zgo else None
        if Ugo:
            goName = _base_name(Ugo.get('m_Name', ''))
            for T in Ugo.get('m_Component', []):
                cid = T['component']['m_PathID']
                Zc = T0.get(cid)
                if Zc is not None and 'Renderer' in Zc.type.name:
                    aP2.append((cid, goName, zHere, aQ3[0]))
                    aQ3[0] += 1
        for T in Ut.get('m_Children', []):
            _walk(T['m_PathID'], zHere)

    _walk(root_pathid, 0.0)
    # Z GIAM DAN (it am -> nhieu am, tuc xa camera -> gan camera), tie-break
    # bang thu tu DFS TANG DAN (giu nguyen thu tu goc khi Z bang nhau)
    aP2.sort(key=lambda r: (-r[2], r[3]))
    return [(cid, name) for cid, name, _z, _o in aP2]


def _force_material_render_queue(Z, value):
    """Tra ve bytes serialize lai cua Material Z voi m_CustomRenderQueue = value.

    Material khong nam trong _SKIP_TYPETREE_CLASSES nen read_typetree()
    doc dung. Phai doc typetree tu Material NGUON (Z, chua bi dong vao lan
    nao) va chi TRA VE bytes moi, khong set vao object dich roi doc lai --
    object dich (clone qua h()) van tro toi du lieu template cu tai
    byte_start goc, doc lai se ra du lieu cu chu khong phai du lieu vua ghi.
    """
    tree = Z.read_typetree()
    tree['m_CustomRenderQueue'] = value
    nodes = Z.get_typetree_nodes()
    from UnityPy.streams import EndianBinaryWriter
    from UnityPy.helpers import TypeTreeHelper
    writer = EndianBinaryWriter(endian=Z.reader.endian)
    writer = TypeTreeHelper.write_typetree(tree, nodes, writer)
    return writer.bytes


def h(S):
    R = object.__new__(type(S))
    R.__dict__.update(S.__dict__)
    R.data = b''
    return R

def e(R):
    return bytes(R.get_raw_data())

def y(T, U):
    if isinstance(T, dict):
        if 'm_FileID' in T and 'm_PathID' in T:
            R = (T['m_FileID'], T['m_PathID'])
            if R in U:
                T['m_FileID'] = 0
                T['m_PathID'] = U[R]
            return T
        for S in T.values():
            y(S, U)
    elif isinstance(T, (list, tuple)):
        for S in T:
            y(S, U)
    return T

def Q(T):
    if isinstance(T, dict):
        if 'm_FileID' in T and 'm_PathID' in T:
            R, S = (T['m_FileID'], T['m_PathID'])
            if isinstance(R, int) and isinstance(S, int) and (S != 0):
                yield (R, S)
            return
        for U in T.values():
            yield from Q(U)
    elif isinstance(T, (list, tuple)):
        for U in T:
            yield from Q(U)

# Cac class nay luon that bai khi doc read_typetree() tren ban Unity
# 2022.3.5f1 rieng cua AOV/HOK (cau truc thuc te khac generic typetree cua
# UnityPy), va viec goi read_typetree() se ton hang trieu lan goi de quy
# read_value() truoc khi that bai thay vi fail nhanh. Bo qua thang, di
# thang vao fallback quet byte u() (chi khac duong nhanh o cach tim vi
# tri, dieu kien Y()/X() giu nguyen).
_SKIP_TYPETREE_CLASSES = frozenset((
    'ParticleSystem', 'ParticleSystemRenderer', 'MeshRenderer',
    'Texture2D', 'Mesh', 'Shader',
))

def d(R):
    if R.type.name in _SKIP_TYPETREE_CLASSES:
        return None
    try:
        return R.read_typetree()
    except Exception:
        return None

def c(R):
    return list(R.objects)[0].assets_file

def p(R, T, V=None):
    S = T
    U = R.objects
    while S == 0 or S in U or (V is not None and S in V):
        S += 1
    if V is not None:
        V.add(S)
    return S

def g(T, U, S):
    R = a.path.join(U, S)
    L(T, R)
    return (j.load(R), R)

def u(W, Y, X=None):
    S = len(W)
    # Toi uu toc do: T hop le (0<=T<=32) duoi dang int32 little-endian
    # nghia la 4 byte co dang [T,0,0,0] (T<256 nen 3 byte cao luon =0) --
    # gom UNG VIEN vi tri bang W.find() (chay o tang C, nhanh hon RAT
    # nhieu so voi vong lap Python tung byte + 2 lan struct.unpack_from o
    # MOI vi tri nhu ban cu) roi moi kiem tra V/goi Y/X tren dung tap ung
    # vien do. Ket qua/thu tu yield GIU NGUYEN 100% logic goc (khop that
    # thi nhay qua 12 byte tiep theo giong R+=12 cu, khop hut/khong hop le
    # thi khong nhay, vi tri sau van duoc xet binh thuong).
    candidates = []
    for t in range(33):
        pattern = i.pack('<i', t)
        pos = W.find(pattern)
        while pos != -1 and pos <= S - 12:
            candidates.append((pos, t))
            pos = W.find(pattern, pos + 1)
    candidates.sort()
    skip_until = -1
    for R, T in candidates:
        if R < skip_until:
            continue
        V = i.unpack_from('<q', W, R + 4)[0]
        if V != 0:
            U = Y(T, V)
            if U is not None and (X is None or X(T, V, U)):
                yield (R, T, V)
                skip_until = R + 12

def q(S, Y, X=None):
    W = d(S)
    if W is not None:
        for T, V in Q(W):
            U = Y(T, V)
            if U is not None and (X is None or X(T, V, U)):
                yield (T, V)
        return
    for R, T, V in u(e(S), Y, X):
        yield (T, V)

def J(R, X, Z):
    ab = d(R)
    if ab is None:
        return None
    ad = {}
    for S, W in Q(ab):
        if Z(S, W):
            ad[S, W] = ad.get((S, W), 0) + 1
    U = []
    aa = bytes(X)
    for (S, W), ac in ad.items():
        V = i.pack('<iq', S, W)
        Y = [T for T in range(0, len(aa) - 11, 4) if aa[T:T + 12] == V]
        if len(Y) != ac:
            raise t('khong dinh vi chinh xac PPtr %s:%s trong %s (tree=%d, raw=%d)' % (S, W, R.type.name, ac, len(Y)))
        U.extend(((af, S, W) for af in Y))
    return U

def r(R):
    S = getattr(R, 'serialized_type', None)
    return (R.class_id, getattr(S, 'script_id', None), getattr(S, 'old_type_hash', None))

def m(bl, bo, bw, bb, az=lambda s: None):
    aM = c(bl)
    R = aM.objects
    bd, S = g(bo, bb, 'eff.assetbundle')
    aT = {0: {Z.path_id: Z for Z in bd.objects}}
    br = {}
    aL = c(bd)
    for ax, ah in enumerate(aL.externals, start=1):
        br[ax] = ah.path
    if bw and a.path.isfile(bw):
        bg, S = g(bw, bb, 'effraw.assetbundle')
        bf = c(bg).name if hasattr(c(bg), 'name') else ''
        bp = {Z.path_id: Z for Z in bg.objects}
        for ax, aa in br.items():
            if bf and bf in aa:
                aT[ax] = bp
                break
        else:
            for ax in br:
                if ax not in aT:
                    aT[ax] = bp
                    break

    def bh(by, bz):
        bx = aT.get(by)
        return bx.get(bz) if bx else None
    aI = None
    for aC, Z in aT[0].items():
        if Z.type.name not in ('Transform', 'RectTransform'):
            continue
        U = d(Z)
        if not U or U['m_Father']['m_PathID'] != 0:
            continue
        V = aT[0].get(U['m_GameObject']['m_PathID'])
        aj = d(V) if V else None
        if aj and str(aj.get('m_Name', '')).lower() == 'attackbutton':
            aI = (aC, Z, U)
            break
    if aI is None:
        raise t("khong tim thay root 'AttackButton' trong file effect")
    aJ, aH, ao = aI
    if len(ao['m_Children']) != 1:
        raise t('root co %d child (mong doi 1)' % len(ao['m_Children']))
    # Mount thang child duy nhat cua root (mang dung local position/scale
    # authored goc), khong mount ca root -- mount ca root roi ep them
    # m_LocalPosition tu 'circle' se cong don offset 2 lan.
    aW = ao['m_Children'][0]['m_PathID']
    aFxDuration, aFxHasMesh = _max_particle_duration_source(aT[0], aW, az)
    aF = set()
    aU = [aW]
    bQ = {}  # component_path_id -> ten GameObject goc (da bo hau to "(N)")
    while aU:
        aq = aU.pop()
        if aq in aF:
            continue
        Z = aT[0].get(aq)
        if Z is None:
            continue
        U = d(Z)
        if U is None:
            continue
        aF.add(aq)
        ak = U['m_GameObject']['m_PathID']
        if ak and ak not in aF:
            aF.add(ak)
            aj = d(aT[0][ak])
            if aj:
                bR = _base_name(aj.get('m_Name', ''))
                for T in aj.get('m_Component', []):
                    ae = T['component']['m_PathID']
                    if ae:
                        aF.add(ae)
                        bQ[ae] = bR
        for T in U.get('m_Children', []):
            aU.append(T['m_PathID'])
    bn = [aa for aa in list(aF) if aT[0].get(aa) is not None and aT[0][aa].type.name not in ('GameObject', 'Transform', 'RectTransform')]
    aP = {}
    aO = [(0, aa) for aa in bn]
    aK = set(aO)
    while aO:
        au, aC = aO.pop()
        Z = bh(au, aC)
        if Z is None:
            continue
        for ai, am in q(Z, bh, lambda bx, by, bz: bz.type.name in v):
            al = bh(ai, am)
            X = (ai, am)
            if X in aP or (ai == 0 and am in aF):
                continue
            aP[X] = al
            if X not in aK:
                aK.add(X)
                aO.append(X)
    aS = {}
    bq = set()
    for aa in sorted(aF):
        aS[0, aa] = p(aM, aa, bq)
    for X in sorted(aP):
        aS[X] = p(aM, X[1], bq)
    ba = c(bl)
    bm = {ah.path: W for W, ah in enumerate(ba.externals, start=1)}
    bs = {}
    for ax, aa in br.items():
        if ax in aT:
            continue
        if aa not in bm:
            ba.externals.append(f.copy(aL.externals[ax - 1]))
            bm[aa] = len(ba.externals)
            az('   + them external %s' % aa)
        bs[ax] = bm[aa]
    aY = {}
    for ab in list(aM.objects.values()):
        aY.setdefault(r(ab), ab)

    def bt(bx):
        return aY.get(r(bx))

    def bu(bD):
        bB = r(bD)
        for bx, by in enumerate(aM.types):
            bA = (getattr(by, 'class_id', None), getattr(by, 'script_id', None), getattr(by, 'old_type_hash', None))
            if bA == bB:
                return (bx, by)
        bC = bD.serialized_type
        if bC is None:
            return (None, None)
        bz = f.copy(bC)
        if hasattr(bC, 'nodes'):
            bz.nodes = f.deepcopy(bC.nodes)
        aM.types.append(bz)
        az('   + them SerializedType %s' % bD.type.name)
        return (len(aM.types) - 1, bz)
    bi = {(0, aa): aT[0][aa] for aa in aF if aa in aT[0]}
    bi.update(aP)

    # Chien luoc gan renderQueue: phan biet "gradient that" (nhieu material
    # mang queue goc PHAN BIET co chu dich, nen TIN TUONG va chi dich
    # deu/noi suy) voi "outlier le loi" (1 material duy nhat lech khoi so
    # dong, ban than no moi la loi -- van phai bo qua gia tri author, gan
    # lai theo Z/DFS).
    #
    # Lich su 3 phuong an, tung that bai tren du lieu that cua chinh skin
    # 15217 (xac nhan qua test tren may that ca 3 lan):
    #   1. Gan lai TOAN BO khong dieu kien (V6 goc): nen mat material "glow"
    #      (queue=3200, dat cao hon het co chu dich) xuong con ~3106 vi 1
    #      material KHAC trong nhom con o queue mac dinh -- lop glow bi cac
    #      lop khac de len, hieu ung mo/toi hon ban goc.
    #   2. Chi gan lai material co queue goc <=3000: 3 material cung ten
    #      "02" (cung vai tro, phai cung 1 tang) bi tach doi -- 2 con (queue
    #      mac dinh 3000) len 3103/3107, con 1 (queue goc 3003, giu nguyen
    #      vi >3000) ket lai o tang thap -- 1 lop dang le nam duoi cung lai
    #      bi day len tren cung.
    #   3. Gan lai theo nguong "ceiling" (queue goc > aFloor+so_luong moi
    #      giu): sua duoc trieu chung #2 nhung van vut bo TOAN BO 13/14 gia
    #      tri author that (3000/3001/3003/3004/3005/3010), thay bang thu
    #      tu Z/DFS tu doan lai -- co the trung hop dung voi 15217 nhung
    #      khong con la du lieu that nguoi lam hieu ung da can chinh tay.
    #
    # Giai phap dung: dem so material LECH KHOI gia tri PHO BIEN NHAT
    # (mode) trong nhom, khong phai dem so gia tri PHAN BIET -- da xac nhan
    # that tren skin 59903: chi co 2 gia tri phan biet (3000 va 3500) nhung
    # 3500 chi thuoc DUY NHAT 1 material ('baoguang01', chinh la bug goc:
    # author sai queue cao trong khi phai nam duoi cung) -- neu chi dem "co
    # >=2 gia tri phan biet" se tin nham material le loi nay. Yeu cau it
    # nhat 2 material KHAC gia tri pho bien (khong chi 2 gia tri) moi tin la
    # gradient that co chu dich (vd 15217: 6 gia tri lech nhau ro ret).
    #   - >=2 material lech mode: TIN TUONG thu tu tuong doi goc, chi DICH
    #     DEU ca nhom len neu gia tri thap nhat chua dat moc an toan (giu
    #     nguyen khoang cach tuong doi giua cac lop), va noi suy rieng cho
    #     material dang -1 (chua tung author) tu 2 hang xom gan nhat theo
    #     thu tu Z/DFS.
    #   - <2 material lech mode (tat ca giong nhau hoac deu -1): khong du
    #     tin hieu de tin gradient -- quay ve gan lai TOAN BO theo Z/DFS.
    aFloor = _QUEUE_FIX_VALUE - 1
    bO = _ordered_renderer_components_source(aT[0], aW)
    bV = {}  # material key -> queue hien tai, theo thu tu sibling
    bU = {}  # material key -> ten GameObject renderer dau tien dung no, chi de log
    for cid, goName in bO:
        Zc = aT[0].get(cid)
        if Zc is None:
            continue
        for ai, am in q(Zc, bh, lambda bx, by, bz: bz.type.name == 'Material'):
            X = (ai, am)
            if X in bV or X not in aP:
                continue
            Zmat = bh(*X)
            mTree = Zmat.read_typetree() if Zmat else None
            bV[X] = mTree.get('m_CustomRenderQueue', -1) if mTree else -1
            bU[X] = goName
    aAuthoredVals = [qv for qv in bV.values() if qv != -1]
    aKeys = list(bV.keys())
    aKeyIndex0 = {X: aIdx for aIdx, X in enumerate(aKeys)}
    aQueueAssign = {}
    # Authored queue CO CHU DICH = gia tri khac -1 (chua author) VA khac 3000
    # (default cua Unity khi author khong cham toi). Cac gia tri nay la neo
    # that nguoi lam FX can chinh tay (vd 52113: 2997 day glow xuong duoi
    # cung, 3001 day lop hero len tren; 50119: 3001 cho 'huan') -- TUYET DOI
    # khong duoc vut bo. Chi gia tri -1/3000 moi la 'khong co tin hieu'.
    aAuthoredAnchor = {X: bV[X] for X in aKeys if bV[X] not in (-1, 3000)}
    if aAuthoredVals:
        from collections import Counter
        aModeVal, _ = Counter(aAuthoredVals).most_common(1)[0]
        aDeviating = sum(1 for qv in aAuthoredVals if qv != aModeVal)
    else:
        aModeVal = 3000
        aDeviating = 0
    if aDeviating >= 2:
        # Gradient that: TIN TUONG thu tu tuong doi cua gia tri author, nhung
        # KHONG dich deu roi noi suy rieng cho -1 (da thu, phat hien loi that
        # tren chinh 15217: nhieu material cung mang gia tri mac dinh 3000 bi
        # dich toi CUNG mot con so -- vd 3100 -- khien thu tu VE GIUA CHUNG
        # VAN khong xac dinh, khong giai quyet duoc bug goc). Thay bang sap
        # xep (gia tri author, gia tri -1 coi nhu bang mode) roi tie-break
        # bang thu tu Z/DFS, cap SO NGUYEN LIEN TIEP KHONG TRUNG theo ket qua
        # sap xep -- vua giu dung thu tu tuong doi cua gia tri phan biet that,
        # vua dam bao khong con material nao trung queue voi material khac.
        #
        # Rieng material co gia tri author VUOT QUA ceiling (aFloor + so
        # luong) van duoc loai khoi vong cap so nay, giu nguyen gia tri goc --
        # dung cho outlier co tinh dat rat cao (vd 15217 mat "glow" =3200) de
        # danh khoang dem an toan voi cac UI khac ngoai pham vi FX nay, thay
        # vi bi nen xuong sat voi phan con lai.
        aCeiling = aFloor + len(bV)
        aOutliers = {X for X in bV if bV[X] > aCeiling}
        aKeyIndex = dict(aKeyIndex0)
        aRankPool = [X for X in aKeys if X not in aOutliers]
        aRankPool.sort(key=lambda X: (aModeVal if bV[X] == -1 else bV[X], aKeyIndex[X]))
        for aRank, X in enumerate(aRankPool):
            aNewQ = aFloor + 1 + aRank
            if aNewQ != bV[X]:
                aQueueAssign[X] = aNewQ
        if aQueueAssign:
            az('   Q  : phat hien gradient that (%d/%d material lech gia tri pho bien %d) -> giu thu tu tuong doi, gan lai KHONG TRUNG %d cho: %d..%d, GIU NGUYEN %d outlier vuot ceiling (%d)' % (
                aDeviating, len(bV), aModeVal, len(aQueueAssign), aFloor + 1, aFloor + len(aRankPool), len(aOutliers), aCeiling))
        else:
            az('   Q  : gradient that nhung ca %d material da dung vi tri, khong can doi' % len(bV))
    elif bV:
        # Khong du tin hieu tu renderQueue tac gia. Thay tieu chi tho
        # "prefix UX_/Ux_ = luon o tren" (rule cu bIsUxPrefix -- da xac nhan
        # SAI that tren 2 skin khi test lai trong game:
        #   * 50119: toan bo 6 material deu mang prefix UX_/Ux_ nhung thuc
        #     chat chung la hat hieu ung (glow/line/_Add), KHONG co khung UI
        #     nao -> aRestKeys rong, aRestMax = aFloor -> tat ca UX_ chong
        #     len nhau chi dua vao DFS-order, khong co material EF_ nao o
        #     duoi -> thu tu sai.
        #   * 52113: 2 material UX_hero_cpmj_hjx_045/046 bi ep len tren cung
        #     nhung day la lop hieu ung hero (hjx), khong phai khung vien UI;
        #     trong khi Glow_CPgt_zzy_018 (khong prefix UX_) bi xep duoi.
        # Nguyen nhan goc: UX_ la NAMESPACE TAI NGUYEN CHUNG cua HOK, khong
        # phai chi bao "khung UI". Dac trung that cua khung UI trang tri la
        # UX_Circle_.../UX_Plant_.../UX_Frame_.../UX_Border_... -- texture co
        # saturation trung-cao (>=0.15) NHUNG khong phai trang thuan
        # additive. Dac trung cua hat/glow: value V rat cao (~1.0) + sat ~0
        # (trang thuan cho additive blending), hoac ten chua _Add/glow/line/
        # flare/...
        #
        # Giai phap: phan loai DA TIN HIEU qua 3 ham duoi day -- chi ep len
        # TREN CUNG nhung material thoa CA 3 dieu kien "khung UI that".
        # (aKeyIndex0 da duoc tinh san o ngoai, dung chung cho ca 2 nhanh.)
        bMetaCache = {}

        def bMatMeta(X):
            """Doc 1 lan va cache (m_Name, ten texture _MainTex, hsv) cho
            moi material de tai su dung cho ca bIsParticleLike/bIsUiFrame va
            buoc sort -- tranh read_typetree + doc anh lap lai nhieu lan."""
            if X in bMetaCache:
                return bMetaCache[X]
            Zmat2 = bh(*X)
            aMeta = {'m_Name': '', 'tex_name_lower': '', 'hsv': None}
            if Zmat2 is not None:
                try:
                    mTree2 = Zmat2.read_typetree()
                    aMeta['m_Name'] = mTree2.get('m_Name', '') or ''
                    for aE2 in mTree2.get('m_SavedProperties', {}).get('m_TexEnvs', []):
                        if aE2[0] != '_MainTex':
                            continue
                        aPtr = aE2[1]['m_Texture']
                        if aPtr['m_PathID'] != 0:
                            aTex = bh(aPtr['m_FileID'], aPtr['m_PathID'])
                            if aTex is not None and aTex.type.name == 'Texture2D':
                                try:
                                    aMeta['tex_name_lower'] = (aTex.read().m_Name or '').lower()
                                except Exception:
                                    pass
                        break
                    aMeta['hsv'] = _material_color_info(Zmat2, bh)
                except Exception:
                    pass
            bMetaCache[X] = aMeta
            return aMeta

        _PARTICLE_KW = ('glow', 'line', 'huan', 'lizi', 'trail', 'flare',
                        'spark', 'light', 'flash', 'hjx', 'hg', 'guang',
                        'baoguang', 'guangyun', '_add', 'add_', 'ef_', 'fx_')
        _NEUTRAL_SAT_THRESHOLD = 0.15
        _ADDITIVE_V_THRESHOLD = 0.90

        def bIsParticleLike(X, aGoName):
            """Nhan dien hat hieu ung qua (1) keywords trong ten
            GameObject/material/texture, hoac (2) dac trung texture additive:
            V >= 0.90 va S < 0.15 (trang thuan -- danh rieng cho additive
            blending, KHONG bao gio la khung UI)."""
            aMeta = bMatMeta(X)
            aHay = (str(aGoName or '') + ' ' + aMeta['m_Name'] + ' ' +
                    aMeta['tex_name_lower']).lower()
            if any(aKw in aHay for aKw in _PARTICLE_KW):
                return True
            aHsv = aMeta['hsv']
            if aHsv is not None and aHsv[2] >= _ADDITIVE_V_THRESHOLD and \
                    aHsv[1] < _NEUTRAL_SAT_THRESHOLD:
                return True
            return False

        def bIsUiFrame(X, aGoName):
            """Chi tinh la 'khung UI that' khi thoa CA 3 dieu kien:
            (a) ten material co prefix UX_/Ux_,
            (b) KHONG roi vao dac trung hat (bIsParticleLike),
            (c) texture co saturation >= 0.15 (khung UI thuong duoc ve mau
                ro, khong phai trang thuan)."""
            aMeta = bMatMeta(X)
            if (aMeta['m_Name'][:3].lower()) != 'ux_':
                return False
            if bIsParticleLike(X, aGoName):
                return False
            aHsv = aMeta['hsv']
            if aHsv is None or aHsv[1] < _NEUTRAL_SAT_THRESHOLD:
                return False
            return True

        aUxKeys = [X for X in aKeys if bIsUiFrame(X, bU.get(X, ''))]
        # Sap xep TRONG nhom UX-khung theo saturation GIAM DAN, tie-break
        # bang thu tu Z/DFS goc (stable).
        aUxKeys.sort(key=lambda X: (-(bMatMeta(X)['hsv'][1] if bMatMeta(X)['hsv'] else 0.0),
                                     aKeyIndex0[X]))
        aRestKeys = [X for X in aKeys if X not in aUxKeys]

        aColorInfo = {}
        for X in aRestKeys:
            aColorInfo[X] = bMatMeta(X)['hsv']
        aHasAnyColor = any(v is not None for v in aColorInfo.values())

        # ---- Thu tu NEN mong muon cho nhom khong-khung (thap -> cao) ----
        # Uu tien 1: NEO AUTHORED (queue goc khac -1/3000) quyet dinh thu tu
        # tuong doi -- day la tin hieu that tac gia can tay (52113: 2997 <
        # 3001 nghia la glow phai DUOI lop hero; 50119: 'huan'=3001 co chu
        # dich nam tren). Ban cu VUT BO tin hieu nay -> 50119/52113 sai layer.
        # Uu tien 2: phan loai mau (trung tinh o day, vang/do xen ke) cho
        # phan khong co neo -- giu nguyen heuristic 59903 da xac nhan.
        # LOC NEO: chi tin neo sat mac dinh Unity (3000 +/- dung luong nho,
        # vd 2997/3001/3005 la nudge co chu dich). Neo CUC DOAN vuot ceiling
        # (aFloor + so material, vd 59903: baoguang01=3500) la OUTLIER SAI
        # goc (author dat nham queue qua cao trong khi lop do phai nam DUOI)
        # -- khong duoc tin lam neo, de heuristic mau xep lai dung cho no.
        aAnchorCeiling = aFloor + len(bV)
        aAnchoredRest = [X for X in aRestKeys
                         if X in aAuthoredAnchor and aAuthoredAnchor[X] <= aAnchorCeiling]
        aUnanchoredRest = [X for X in aRestKeys if X not in aAnchoredRest]
        aDroppedAnchors = [X for X in aRestKeys
                           if X in aAuthoredAnchor and aAuthoredAnchor[X] > aAnchorCeiling]
        if aDroppedAnchors:
            az('   Q  : ! bo qua %d neo authored vuot ceiling %d (outlier sai goc, vd kieu baoguang01=3500 cua 59903): %s' % (
                len(aDroppedAnchors), aAnchorCeiling,
                ', '.join('%s=%d' % (bMatMeta(X)['m_Name'] or '?', aAuthoredAnchor[X]) for X in aDroppedAnchors)))

        aOrderedRest = []
        if aHasAnyColor:
            def bIsYellowHue(hh):
                return 0.06 <= hh <= 0.20
            aNeutral = []
            aColoredKeys = []
            for X in aUnanchoredRest:
                info = aColorInfo[X]
                if info is None or info[1] < _NEUTRAL_SAT_THRESHOLD:
                    # KHONG gom chung 1 queue nhu ban cu (chinh no tao ra
                    # bug 4 material cung queue=3100 tren 50119 -> thu tu ve
                    # khong xac dinh -> mo/sai layer). Trung tinh van o DAY
                    # nhung moi material 1 queue RIENG theo thu tu Z/DFS.
                    aNeutral.append(X)
                else:
                    aColoredKeys.append(X)
            aYellows = sorted([X for X in aColoredKeys if bIsYellowHue(aColorInfo[X][0])],
                               key=lambda X: -aColorInfo[X][1])
            aReds = sorted([X for X in aColoredKeys if not bIsYellowHue(aColorInfo[X][0])],
                            key=lambda X: -aColorInfo[X][2])
            aInterleaved = []
            if aYellows:
                aInterleaved.append(aYellows[0])
            if aReds:
                aInterleaved.append(aReds[0])
            aInterleaved.extend(aYellows[1:])
            aInterleaved.extend(aReds[1:])
            # day -> dinh: trung tinh (Z/DFS), roi den nhom mau DA XEP
            # (aInterleaved dang la dinh->day nen dao lai), neo chen dung
            # vi tri tuong doi cua no o buoc sau.
            aOrderedRest = list(aNeutral) + list(reversed(aInterleaved))
        else:
            aOrderedRest = list(aUnanchoredRest)  # giu Z/DFS

        # Chen NEO vao thu tu nen: sort toan bo (neo + khong neo) theo
        # (queue neo hoac vi tri nen, Z/DFS). Neo co queue goc CAO duoc dat
        # tren neo thap; material khong neo duong nhien lap day con lai,
        # giu nguyen thu tu nen tuong doi giua chung.
        aMerged = aOrderedRest + aAnchoredRest
        aMerged.sort(key=lambda X: (
            aAuthoredAnchor[X] if X in aAuthoredAnchor else 3000.5 + aOrderedRest.index(X) * 1e-6,
            aKeyIndex0[X]))
        # Gan queue KHONG TRUNG, lien tiep tu aFloor+1, theo thu tu da merge
        for aRank, X in enumerate(aMerged):
            aQueueAssign[X] = aFloor + 1 + aRank
        aRestMax = aFloor + len(aMerged)
        for aIdx, X in enumerate(aUxKeys):
            aQueueAssign[X] = aRestMax + 1 + aIdx

        if aUxKeys:
            az('   Q  : co %d khung UI that (UX_ + khong particle-like + S>=0.15) -> ep len TREN CUNG (sort S giam dan), %d material con lai (trong do %d neo authored) xep theo %s: %d..%d' % (
                len(aUxKeys), len(aRestKeys), len(aAnchoredRest), 'neo authored + do sang mau' if aHasAnyColor else 'neo authored + Z/DFS',
                aFloor + 1, aFloor + len(aQueueAssign)))
        else:
            az('   Q  : khong co UX khung UI that -> xep toan bo theo %s%s: %d..%d' % (
                'neo authored + do sang mau _MainTex' if aHasAnyColor else 'neo authored + Z/DFS (khong doc duoc mau)',
                ' (%d neo)' % len(aAnchoredRest) if aAnchoredRest else '',
                aFloor + 1, aFloor + len(aQueueAssign)))

    # ---- SAFETY NET: khong bao gio de 2 material FX trung renderQueue ----
    # Bat ke nhanh nao phia tren sinh ra gia tri trung (bug lich su: nhanh
    # neutral cu gan chung aFloor+1 cho moi material trung tinh -> 50119 co
    # 4 material cung queue=3100 -> thu tu ve khong xac dinh -> lop chong
    # sai/mo). Quet lai toan bo gan cuoi: giu nguyen material dau tien theo
    # thu tu Z/DFS, moi material sau neu trung thi day len so trong tiep
    # theo. Thu tu tuong doi tong the van duoc bao toan vi day chi dich
    # chuyen cac phan tu TRUNG, theo chieu tang.
    if aQueueAssign:
        aSortedKeys = sorted(aQueueAssign.keys(), key=lambda X: (aQueueAssign[X], aKeyIndex0.get(X, 0)))
        aUsed = set()
        aFixed = 0
        for X in aSortedKeys:
            aQ = aQueueAssign[X]
            while aQ in aUsed:
                aQ += 1
                aFixed += 1
            aQueueAssign[X] = aQ
            aUsed.add(aQ)
        if aFixed:
            az('   Q  : SAFETY-NET tach %d lan trung renderQueue -> moi material FX deu co queue RIENG BIET' % aFixed)

    bv = {}
    for (au, aC), Z in bi.items():
        if (au, aC) in aQueueAssign and Z.type.name == 'Material':
            aTree = Z.read_typetree()
            aOldQ = aTree.get('m_CustomRenderQueue', -1)
            aNewQ = aQueueAssign[au, aC]
            if aOldQ != aNewQ:
                aD = bytearray(_force_material_render_queue(Z, aNewQ))
                az('   Q  : ep renderQueue=%d cho Material %s (nhom %s, cu=%s)' % (aNewQ, aTree.get('m_Name', '?'), bU.get((au, aC), '?'), aOldQ))
            else:
                aD = bytearray((P(Z, az) if Z.type.name == 'Texture2D' else None) or e(Z))
                az('   Q  : %s (nhom %s) da dung (%s), khong can doi' % (aTree.get('m_Name', '?'), bU.get((au, aC), '?'), aOldQ))
        else:
            aD = bytearray((P(Z, az) if Z.type.name == 'Texture2D' else None) or e(Z))
        ay = J(Z, aD, lambda bx, by: (bx, by) in aS)
        if ay is None:
            ay = list(u(bytes(aD), bh, lambda bx, by, bz: (bx, by) in aS))
        for aA, ai, am in ay:
            X = (ai, am)
            i.pack_into('<i', aD, aA, 0)
            i.pack_into('<q', aD, aA + 4, aS[X])
        if bs:
            at = J(Z, aD, lambda bx, by: bx in bs)
            if at is not None:
                for aA, ai, S in at:
                    i.pack_into('<i', aD, aA, bs[ai])
            elif Z.type.name == 'ParticleSystemRenderer' and len(aD) >= 136:
                # d(Z) luon None cho ParticleSystemRenderer (nam trong
                # _SKIP_TYPETREE_CLASSES), nen J() khong the tim va remap
                # external-index cho m_Mesh (PPtr<Mesh>) qua duong thuong.
                # Vá truc tiep vao dung offset m_Mesh, tinh dong theo so
                # luong Material thuc te cua tung object (m_Materials.size
                # nam o offset 116) thay vi quet mù ca buffer, de tranh sua
                # nham du lieu Texture2D/Mesh/Shader khac.
                mat_count = i.unpack_from('<i', aD, 116)[0]
                if 0 <= mat_count <= 64:
                    mat_end = 116 + 4 + mat_count * 12
                    vs_size_off = mat_end + 120
                    if vs_size_off + 4 <= len(aD):
                        vs_size = i.unpack_from('<i', aD, vs_size_off)[0]
                        if 0 <= vs_size <= 64:
                            mesh_off = (vs_size_off + 4 + vs_size + 3) & ~3
                            if mesh_off + 12 <= len(aD):
                                mfid = i.unpack_from('<i', aD, mesh_off)[0]
                                mpid = i.unpack_from('<q', aD, mesh_off + 4)[0]
                                if mfid in bs and mpid != 0:
                                    i.pack_into('<i', aD, mesh_off, bs[mfid])
        an = bt(Z)
        if an is None:
            aE, ap = bu(Z)
            if aE is None:
                az('   ! bo qua %s (khong dung duoc type)' % Z.type.name)
                continue
            an = next(iter(aM.objects.values()))
            Y = h(an)
            Y.type_id = aE
            Y.serialized_type = ap
            Y.class_id = Z.class_id
            Y.type = Z.type
            aY.setdefault(r(Z), Y)
        else:
            Y = h(an)
        Y.path_id = aS[au, aC]
        aM.objects[Y.path_id] = Y
        if Z.type.name in ('Texture2D', 'Material', 'Mesh'):
            # watermark AN TOAN: giu NGUYEN do dai byte cua m_Name (chi
            # doi noi dung ben trong thanh 'QuannDZ' + byte rong), KHONG
            # dich chuyen bat ky offset nao phia sau -- tranh lap lai loi
            # crash PPtr remap da gap truoc do khi doi ca do dai ten.
            aD = bytearray(_rename_same_length(bytes(aD), WATERMARK_TAG))
        Y.set_raw_data(bytes(aD))
        bv[Y.path_id] = bytes(aD)
    be = [(X, aG) for X, aG in aS.items() if aG not in aM.objects]
    if be:
        aZ = ', '.join(('%s:%s->%s' % (bx[0], bx[1], bz) for bx, bz in be[:5]))
        raise t('FX thieu object sau khi copy: %s' % aZ)
    aV = []
    for X, bj in bi.items():
        bk = e(bj)
        bc = bv[aS[X]]
        ar = J(bj, bk, lambda bx, by: (bx, by) in aS)
        if ar is None:
            ar = u(bk, bh, lambda bx, by, bz: (bx, by) in aS)
        for aA, ai, am in ar:
            aN = aS[ai, am]
            if aA + 12 > len(bc):
                aV.append((X, aA, aN, 'short'))
                continue
            aQ = i.unpack_from('<i', bc, aA)[0]
            aR = i.unpack_from('<q', bc, aA + 4)[0]
            if aQ != 0 or aR != aN:
                aV.append((X, aA, aN, (aQ, aR)))
    if aV:
        X, aA, aN, aw = aV[0]
        raise t('FX PPtr remap loi tai %s:%s +0x%X, can %s, gap %s' % (X[0], X[1], aA, aN, aw))

    aX = aS[0, aW]
    av = aM.objects.get(aX)
    if av is None:
        raise t('transform FX khong duoc copy sang')
    U = d(aT[0][aW])
    if U is None:
        raise t('khong doc duoc transform FX o file nguon')
    aWGoSrcId = U['m_GameObject']['m_PathID']
    y(U, aS)
    U['m_Father'] = {'m_FileID': 0, 'm_PathID': G}
    # Giu nguyen localPosition/scale cua child FX tu bundle nguon: toa do
    # authored trong FX source da dung chuan vi da mount dung node child
    # (khong phai ca root). KHONG compose transform cua root wrapper
    # ('AttackButton') vao child -- da kiem chung: root wrapper thuoc ve 1
    # ngu canh render khac trong game goc, khong phai ty le cho nut danh
    # thuong ma tool dang ghep vao; compose vao se lam hieu ung sai kich
    # thuoc (qua to).
    av.save_typetree(U)
    # Chuan hoa ten node mount ve 'Effect' bat ke ten goc trong file nguon
    # la gi (vd 'AttackButton', 'Fx', ...) de cau truc luon nhat quan giua
    # cac skin -- phong truong hop co logic trong game dua vao ten co
    # dinh de lookup.
    Zgo0 = aT[0].get(aWGoSrcId)
    Ugo0 = d(Zgo0) if Zgo0 is not None else None
    Ygo0Id = aS.get((0, aWGoSrcId))
    Ygo0 = aM.objects.get(Ygo0Id) if Ygo0Id is not None else None
    if Ugo0 is None or Ygo0 is None:
        az('   ! khong doi duoc ten node mount thanh Effect (thieu GameObject nguon/dich)')
    else:
        aOldName = Ugo0.get('m_Name', '')
        y(Ugo0, aS)
        Ugo0['m_Name'] = 'Effect'
        Ygo0.save_typetree(Ugo0)
        if aOldName != 'Effect':
            az("   NAME: doi ten node mount '%s' -> 'Effect' (dam bao cau truc effect -> Effect)" % aOldName)
    ag = R[G]
    af = d(ag)
    # Thay the m_Children cua 'effect' bang chi mot minh FX moi, mo coi
    # 'circle' (father=0, children=[]) thay vi giu no lam con. MonoBehaviour
    # "OLDSYS_CUIParticleScript" tren 'effect' tinh thoi luong runtime tu
    # con dau tien trong m_Children -- giu 'circle' (thoi luong ngan) lam
    # con se ghim tran thoi gian song cua ca hieu ung xuong ngan hon FX
    # skin thuc te.
    aB = [T['m_PathID'] for T in af['m_Children']]
    af['m_Children'] = [{'m_FileID': 0, 'm_PathID': aX}]
    ag.save_typetree(af)
    if K in R and K in aB:
        ad = R[K]
        ac = d(ad)
        ac['m_Father'] = {'m_FileID': 0, 'm_PathID': 0}
        ac['m_Children'] = []
        ad.save_typetree(ac)

    az('   FX : %d object, mount %s' % (len(bi), av.type.name))
    return aX, aFxDuration, aFxHasMesh

def _recover_shifted_stream_data(Z, R):
    """Khoi phuc du lieu anh cho Texture2D bi doc sai m_StreamData (path
    rong, offset la so rac lon bat thuong). Da xac nhan: gia tri rac nay
    thuong la offset_that << 32 (offset that bi day len 32-bit cao thay vi
    nam dung vi tri, do mot field 4-byte bi bo sot khi doc object). Neu
    offset rac chia het cho 2^32, dung thuong so lam offset that, lay path
    tu bat ky texture anh em nao co StreamData hop le trong cung
    assets_file, roi doc truc tiep tu resource stream. Tra ve bytes anh
    that neu khoi phuc thanh cong, None neu khong khop dieu kien.

    """
    try:
        sd = R.m_StreamData
        if sd is None or sd.path:
            return None  # da co path hop le, khong phai truong hop nay
        raw_offset = int(sd.offset)
        if raw_offset <= 0xFFFFFFFF or (raw_offset & 0xFFFFFFFF) != 0:
            return None  # khong khop dung dang "offset that * 2^32"
        true_offset = raw_offset >> 32
        true_size = int(getattr(R, 'm_CompleteImageSize', 0) or 0)
        if true_size <= 0:
            return None
        assets_file = Z.assets_file
        sibling_path = None
        for other in assets_file.objects.values():
            if other is Z or other.type.name != 'Texture2D':
                continue
            try:
                osd = other.read().__dict__.get('m_StreamData')
            except Exception:
                continue
            if osd and osd.path:
                sibling_path = osd.path
                break
        if not sibling_path:
            return None
        from UnityPy.helpers.ResourceReader import get_resource_data
        recovered = get_resource_data(sibling_path, assets_file, true_offset, true_size)
        if not recovered or len(recovered) != true_size:
            return None
        return bytes(recovered)
    except Exception:
        return None


def _material_color_info(Z, bh):
    """Do (hue, saturation, value) tu _MainTex cua 1 Material NGUON, dung
    lam tin hieu thay the thu tu Z/DFS khi renderQueue khong co gia tri tac
    gia phan biet (nhanh "khong du tin hieu" trong m()).

    Ly do: xac nhan qua test that skin 59903 -- nhom material CUNG TEN
    GameObject (vd 'lizi', 'trail_01_add_ri') co the chua material MAU SAC
    khac hoan toan nhau -- xep theo TEN NHOM (Z/DFS) sai o cap chi tiet tung
    material, trong khi mau sac tung material rieng le moi la tin hieu dung
    y do thi giac that.

    Tra ve None neu khong doc duoc anh de goi noi fallback ve Z/DFS an toan
    cho rieng material do.
    """
    try:
        tree = Z.read_typetree()
        for entry in tree.get('m_SavedProperties', {}).get('m_TexEnvs', []):
            if entry[0] != '_MainTex':
                continue
            ptr = entry[1]['m_Texture']
            if ptr['m_PathID'] == 0:
                return None
            texobj = bh(ptr['m_FileID'], ptr['m_PathID'])
            if texobj is None or texobj.type.name != 'Texture2D':
                return None
            img = texobj.read().image.convert('RGBA')
            pixels = img.getdata()
            rs = gs = bs = wsum = 0.0
            for (pr, pg, pb, pa) in pixels:
                wgt = pa / 255.0
                rs += pr * wgt; gs += pg * wgt; bs += pb * wgt; wsum += wgt
            if wsum == 0:
                return (0.0, 0.0, 0.0)
            rr, gg, bb = rs / wsum, gs / wsum, bs / wsum
            return _colorsys.rgb_to_hsv(rr / 255.0, gg / 255.0, bb / 255.0)
        return None
    except Exception:
        return None


def P(Z, az=lambda s: None):
    # Texture2D hiem gap co the co m_StreamData bi doc sai (path rong,
    # offset rac), khien Z.read()/R.image_data nem exception. Bat loi o day
    # de khong lam hong ca lan build; fallback ve du lieu tho e(Z) (metadata
    # giu nguyen, chi khong inline duoc anh) va log ro texture nao bi anh
    # huong.
    try:
        U = e(Z)
        R = Z.read()
        recovered = _recover_shifted_stream_data(Z, R)
        if recovered is not None:
            # Khong dung do dai chuoi path de tinh vi tri cat (path da hong
            # nen tinh theo do dai se sai). Tim truc tiep vi tri byte cua
            # offset rac (8-byte little-endian) trong U, cat tu do tru 4
            # byte (cho field image_data_size dung truoc no).
            raw_offset_bytes = i.pack('<Q', int(R.m_StreamData.offset))
            pos = U.rfind(raw_offset_bytes)
            if pos < 8:
                az('   ! CANH BAO: khoi phuc duoc anh Texture2D "%s" (pathID=%s) nhung khong dinh vi duoc vi tri byte de ghep -- bo qua, giu nguyen goc' % (
                    getattr(R, 'm_Name', '?'), getattr(Z, 'path_id', '?')))
                return None
            V = U[:pos - 4]
            # m_PlatformBlob rong bat thuong (gay crash that tren thiet bi,
            # xac nhan qua test): moi texture anh em khac trong file deu co
            # m_PlatformBlob dai 1 byte (gia tri 0x00) sau khi align, chi
            # rieng texture loi nay co blob rong (0 byte). 4 byte ngay
            # truoc "image_data_size" (tuc 4 byte cuoi cua V) chinh la
            # length-prefix cua blob rong do -- vá lai thanh blob 1 byte
            # dung format cua UnityPy (length=1 + data 0x00 + align_stream
            # them 3 byte 0 de ve boi so 4) cho khop voi cac texture khac.
            if V[-4:] == i.pack('<I', 0):
                V = V[:-4] + i.pack('<I', 1) + b'\x00\x00\x00\x00'
            az('   * KHOI PHUC anh Texture2D "%s" (pathID=%s) bi loi doc m_StreamData -- da tim lai dung du lieu goc trong .resS' % (
                getattr(R, 'm_Name', '?'), getattr(Z, 'path_id', '?')))
            return V + i.pack('<I', len(recovered)) + recovered + i.pack('<Q', 0) + i.pack('<I', 0) + i.pack('<I', 0)
        T = bytes(R.image_data)
        if not T:
            return None
        W = R.m_StreamData.path or ''
        if not W:
            return U
        X = len(W.encode('utf8'))
        Y = 8 + 4 + 4 + X
        Y += -X % 4
        S = 4 + Y
        V = U[:len(U) - S]
        return V + i.pack('<I', len(T)) + T + i.pack('<Q', 0) + i.pack('<I', 0) + i.pack('<I', 0)
    except Exception as ex:
        try:
            nm = Z.read_typetree().get('m_Name', '?')
        except Exception:
            nm = '?'
        az('   ! CANH BAO: khong doc duoc anh Texture2D "%s" (pathID=%s, loi: %s) -- giu nguyen du lieu goc, anh nay co the sai/thieu trong ket qua' % (nm, getattr(Z, 'path_id', '?'), ex))
        return None

def N(aC, aG, ax, an=lambda s: None):
    av = c(aC)
    S = av.objects
    ak, T = g(aG, ax, 'spr.assetbundle')
    R = {aa.path_id: aa for aa in ak.objects}
    az = {}
    for ap, aa in R.items():
        if aa.type.name != 'Sprite':
            continue
        V = d(aa)
        if V:
            az[V['m_Name']] = (ap, V)
    if not az:
        raise t('file sprite_raw khong co Sprite nao')
    au = {}
    for ap, aa in R.items():
        if aa.type.name != 'SpriteAtlas':
            continue
        ah = d(aa)
        if ah:
            for Y, ac in ah.get('m_RenderDataMap', []):
                au[tuple(Y['first'].values()), Y['second']] = ac
    aD = set()
    for at, (ap, V) in az.items():
        if at not in F:
            continue
        if V['m_SpriteAtlas']['m_PathID'] != 0:
            am = (tuple(V['m_RenderDataKey']['first'].values()), V['m_RenderDataKey']['second'])
            ag = au.get(am)
            if ag:
                aD.add(ag['texture']['m_PathID'])
        else:
            aD.add(V['m_RD']['texture']['m_PathID'])
    aD.discard(0)
    aF = next((aH for aH in aC.objects if aH.type.name == 'Texture2D'), None)
    aE = next((aH for aH in aC.objects if aH.type.name == 'Sprite'), None)
    if aF is None or aE is None:
        raise t('battleotherui thieu kieu Texture2D/Sprite')
    aB = {}
    for ai in sorted(aD):
        if ai not in R:
            continue
        af = P(R[ai], an)
        if af is None:
            continue
        ao = p(av, ai)
        Z = h(aF)
        Z.path_id = ao
        av.objects[ao] = Z
        Z.set_raw_data(af)
        aB[ai] = ao
    ay = {}
    for at in F:
        if at not in az:
            continue
        ap, V = az[at]
        if V['m_SpriteAtlas']['m_PathID'] != 0:
            am = (tuple(V['m_RenderDataKey']['first'].values()), V['m_RenderDataKey']['second'])
            ag = au.get(am)
            if ag is None:
                an('   ! %s: khong co trong RenderDataMap, bo qua' % at)
                continue
            for W in ('textureRect', 'textureRectOffset', 'atlasRectOffset', 'uvTransform', 'downscaleMultiplier', 'settingsRaw'):
                V['m_RD'][W] = ag[W]
            aA = ag['texture']['m_PathID']
        else:
            aA = V['m_RD']['texture']['m_PathID']
        if aA not in aB:
            an('   ! %s: thieu texture, bo qua' % at)
            continue
        V['m_SpriteAtlas'] = {'m_FileID': 0, 'm_PathID': 0}
        V['m_AtlasTags'] = []
        V['m_RD']['texture'] = {'m_FileID': 0, 'm_PathID': aB[aA]}
        V['m_RD']['alphaTexture'] = {'m_FileID': 0, 'm_PathID': 0}
        ao = p(av, ap)
        Z = h(aE)
        Z.path_id = ao
        av.objects[ao] = Z
        Z.save_typetree(V)
        ay[at] = ao
    ar = {l[Z]: ay[Z] for Z in ay if Z in l}
    al = 0
    for ae, at in O.items():
        if ae not in S or at not in ay:
            continue
        aq = e(S[ae])
        if len(aq) < 100 or i.unpack_from('<i', aq, 88)[0] != 0:
            continue
        U = bytearray(aq)
        i.pack_into('<q', U, 92, ay[at])
        S[ae].set_raw_data(bytes(U))
        al += 1
    for ap, aa in list(av.objects.items()):
        if aa is None or aa.type.name != 'MonoBehaviour':
            continue
        aq = e(aa)
        if len(aq) < 100:
            continue
        if i.unpack_from('<q', aq, 20)[0] != E:
            continue
        if i.unpack_from('<i', aq, 88)[0] != 0:
            continue
        aj = i.unpack_from('<q', aq, 92)[0]
        if aj not in ar:
            continue
        U = bytearray(aq)
        i.pack_into('<q', U, 92, ar[aj])
        aa.set_raw_data(bytes(U))
        al += 1
    for X in k:
        if X in S:
            V = d(S[X])
            if V is not None:
                V['m_IsActive'] = True
                S[X].save_typetree(V)
    if 'CustomJoyStick_RockingBg' in az:
        ad = az['CustomJoyStick_RockingBg'][1]['m_Rect']['width']
        aw = abs(ad - x / 2.0) < 0.5
        if w in S:
            U = bytearray(e(S[w]))
            U[12] = 1 if aw else 0
            S[w].set_raw_data(bytes(U))
        if s in S:
            U = bytearray(e(S[s]))
            if len(U) > 104:
                U[104] = 0 if aw else 1
            S[s].set_raw_data(bytes(U))
        an('   G1 : RockingBg %gpx -> mirror=%s' % (ad, 'ON' if aw else 'OFF'))
    if 'CustomJoyStick_RockingArrow' in az and o in S:
        ab = az['CustomJoyStick_RockingArrow'][1]['m_Rect']
        if abs(ab['width'] - A[0]) < 0.5 and abs(ab['height'] - A[1]) < 0.5:
            V = d(S[o])
            if V is not None:
                V['m_LocalScale'] = {'x': C, 'y': C, 'z': C}
                V['m_AnchoredPosition'] = {'x': z, 'y': 0.0}
                S[o].save_typetree(V)
                an('   G2 : arrow %gx%g -> scale %.2f / anchorX %g' % (ab['width'], ab['height'], C, z))
        else:
            an('   G2 : arrow %gx%g khac chuan -> khong bu' % (ab['width'], ab['height']))
    an('   JOY: %d sprite, %d texture, %d Image da tro lai' % (len(ay), len(aB), al))
    return (len(ay), al)

_MESH_FALLBACK_FIELD = 0.5  # tuong duong ~5s

def fix_timelife(S, az=lambda s: None, max_duration=None, has_mesh_content=False):
    # Thoi luong hien thi cua hieu ung bam nut duoc dieu khien boi 1 field
    # float tren MonoBehaviour cua script "CButtonActiveEffect" gan tren
    # GameObject 'AtkBtn' (thuoc file battleotherui goc, khong phai thu
    # duoc mount tu skin). Field ti le thuan voi duration dai nhat trong
    # so cac ParticleSystem cua FX: field = max_duration / 10.
    #
    # max_duration phai duoc m() tinh san tu cay NGUON va truyen qua day,
    # khong duoc tu doc lai node 'effect'/FX o file dich sau khi mount:
    # ObjectReader cua UnityPy fork nay khong cap nhat nguon doc lai sau
    # save_typetree()/set_raw_data() trong cung phien, doc lai se ra du
    # lieu cu.
    if max_duration is None:
        az('   TIME: ! khong co max_duration (chua mount FX, hoac goi sai cach) -> bo qua')
        return
    aO2 = max_duration
    aP2 = aO2 / 10.0
    az('   TIME: FX max duration=%.2fs -> target field=%.3f' % (aO2, aP2))
    R = c(S).objects
    aQ2 = False
    for Z in list(R.values()):
        if Z.type.name != 'MonoBehaviour':
            continue
        aq = bytearray(e(Z))
        if len(aq) < 32:
            continue
        aE = i.unpack_from('<q', aq, 20)[0]
        aa = R.get(aE)
        if aa is None:
            continue
        at = d(aa)
        if not at or at.get('m_ClassName') != 'CButtonActiveEffect':
            continue
        aP = i.unpack_from('<q', aq, 4)[0]
        aGo = R.get(aP)
        aGoT = d(aGo) if aGo else None
        if not aGoT or str(aGoT.get('m_Name', '')).lower() != 'atkbtn':
            continue
        aQ2 = True
        aN = i.unpack_from('<i', aq, 28)[0]
        aB = 32 + aN + (-aN % 4)
        aC = aB + 28
        if len(aq) < aC + 4:
            az('   TIME: ! MonoBehaviour AtkBtn qua ngan (%d byte) de doc field o offset %d -> bo qua' % (len(aq), aC))
            continue
        av = i.unpack_from('<f', aq, aC)[0]
        az('   TIME: tim thay CButtonActiveEffect tren AtkBtn, gia tri hien tai=%.3f' % av)
        # Khong bao gio ep field thap hon gia tri hien co. Khi FX dua vao
        # MeshRenderer+Animation thay vi ParticleSystem, max_duration tinh
        # tu ParticleSystem se bi thieu (AnimationClip dang Mecanim khong
        # doc duoc bang ca typetree lan native reader cua UnityPy). Dung
        # _MESH_FALLBACK_FIELD (0.5, ~5s) lam gia tri an toan cho truong
        # hop nay -- da xac nhan qua test that trong game.
        aFallback = _MESH_FALLBACK_FIELD if has_mesh_content else av
        aP2eff = max(aP2, aFallback)
        if aP2eff != aP2:
            az('   TIME: ! ket qua tinh duoc (%.3f) thap hon gia tri san (%.3f%s) -- dung gia tri san, khong ep xuong.' % (
                aP2, aFallback, ', co MeshRenderer' if has_mesh_content else ''))
        if abs(av - aP2eff) < 1e-4:
            az('   TIME: gia tri hien tai da dung (%.3f), khong can doi' % av)
            continue
        i.pack_into('<f', aq, aC, aP2eff)
        Z.set_raw_data(bytes(aq))
        az('   TIME: CButtonActiveEffect %.3f -> %.3f (FX max duration=%.2fs)' % (av, aP2eff, aO2))
    if not aQ2:
        az('   TIME: ! KHONG tim thay MonoBehaviour CButtonActiveEffect tren GameObject "AtkBtn" trong bundle nay')

