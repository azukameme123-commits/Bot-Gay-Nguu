import os
import gc
import struct
import shutil
from pathlib import Path
from io import BytesIO
from ctypes import c_uint32
import Data.UnityPy_AOV
from Data.UnityPy_AOV.helpers import TypeTreeHelper
from Data.UnityPy_AOV.streams import EndianBinaryWriter
from Data.UnityPy_AOV.files import BundleFile
from Data.UnityPy_AOV.helpers import CompressionHelper
from Data.UnityPy_AOV.enums import ArchiveFlags, ArchiveFlagsOld


def _load_from_bytes(path):
    with open(path, "rb") as f:
        raw = f.read()
    return Data.UnityPy_AOV.load(BytesIO(raw))


def _close_env(env):
    try:
        env.file.reader.stream.close()
    except Exception:
        pass
    try:
        for f in env.files.values():
            try:
                f.reader.stream.close()
            except Exception:
                pass
    except Exception:
        pass
    del env
    gc.collect()


def ResourcePackerInfoSetAll(path, ID_SKIN):
    id3 = ID_SKIN[:3]
    id_full = ID_SKIN.encode()

    MARK = b"Juzu Mod" # 8 bytes phải nhớ ko đc trên hoặc dưới

    with open(path, "rb") as f:
        data = bytearray(f.read())

    pos = 0

    while True:
        start = data.find(b"assetbundle/", pos)
        if start == -1:
            break

        end = data.find(b"assetbundle/", start + 1)
        if end == -1:
            end = len(data)

        block = data[start:end]

        if b"CharBattle" not in block:
            pos = end
            continue

        if id_full in block:
            pos = end
            continue

        found = False

        for n in range(2, 46):
            check = f"/{id3}{n}_".encode()

            if check == f"/{ID_SKIN}_".encode():
                continue

            if ID_SKIN == "1505" and check == b"/15033_":
                continue

            if check in block:
                found = True
                break

        if not found:
            pos = end
            continue

        char_pos = start + block.find(b"CharBattle")

        count_pos = char_pos + len(b"CharBattle") + 6

        count = struct.unpack_from("<I", data, count_pos)[0]

        records = count_pos + 4

        if records + count * 12 > end:
            pos = end
            continue

        for i in range(count):
            p = records + i * 12
            data[p:p + 8] = MARK

        pos = end

    with open(path, "wb") as f:
        f.write(data)
        
def patched_decompress_data(self, compressed_data, uncompressed_size, flags, index=0):
    comp_flag = flags & 0x3F

    if comp_flag == 1:
        return CompressionHelper.decompress_lzma(compressed_data)

    elif comp_flag in [2, 3]:
        if hasattr(self, "decryptor") and self.decryptor:

            if isinstance(self.dataflags, ArchiveFlags):
                if flags & 0x400:
                    compressed_data = self.decryptor.decrypt_block(compressed_data)

            elif isinstance(self.dataflags, ArchiveFlagsOld):
                if flags & 0x200:
                    compressed_data = self.decryptor.decrypt_block(compressed_data)

            else:
                if flags & 0x400 or (flags & 0x200 and not (flags & 0x40)):
                    compressed_data = self.decryptor.decrypt_block(compressed_data)

        return CompressionHelper.decompress_lz4(compressed_data, uncompressed_size)

    return compressed_data


BundleFile.decompress_data = patched_decompress_data


def replace_in_dict(data, old_path, new_path):
    modified = False

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str) and old_path in v:
                data[k] = v.replace(old_path, new_path)
                modified = True
            elif isinstance(v, (dict, list)):
                if replace_in_dict(v, old_path, new_path):
                    modified = True

    elif isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], str) and old_path in data[i]:
                data[i] = data[i].replace(old_path, new_path)
                modified = True
            elif isinstance(data[i], (dict, list)):
                if replace_in_dict(data[i], old_path, new_path):
                    modified = True

    return modified


def ReplacePath(IDMODSKIN, ResourcePacker):
    if isinstance(IDMODSKIN, str):
        IDMODSKIN = IDMODSKIN.split()
    elif isinstance(IDMODSKIN, list):
        IDMODSKIN = [str(x) for x in IDMODSKIN]
    else:
        raise ValueError

    replace_pairs = []

    for ID_SKIN in IDMODSKIN:
        replace_pairs.append((
            f"Ages/Prefab_Characters/Prefab_Hero/Actor_{ID_SKIN[:3]}_Actions.pkg.bytes",
            f"Mod Được Hoàn Thiện Bởi Youtube Minh Anh Mod/.MINH-ANH-{ID_SKIN}-Effects"
        ))
        replace_pairs.append((
            f"Prefab_Characters/Actor_{ID_SKIN[:3]}_Infos.pkg.bytes",
            f"Mod Được Hoàn Thiện Bởi Youtube Minh Anh Mod/.MINH-ANH-{ID_SKIN}-Infos"
        ))

    replace_pairs.append((
        "Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes",
        "Mod Được Hoàn Thiện Bởi Youtube Minh Anh Mod/.MINH-ANH-CommonAction"
    ))

    try:
        env = _load_from_bytes(ResourcePacker)
        modified = False

        for obj in env.objects:
            if obj.type.name != "MonoBehaviour":
                continue

            if not obj.serialized_type.nodes:
                continue

            try:
                tree = obj.read_typetree()
            except Exception:
                continue

            local_modified = False
            for old_path, new_path in replace_pairs:
                if replace_in_dict(tree, old_path, new_path):
                    local_modified = True
                    modified = True

            if local_modified:
                obj.save_typetree(tree)

        if modified:
            try:
                save_bytes = env.file.save(packer="lz4")
            except Exception:
                save_bytes = env.file.save()
            _close_env(env)
            with open(ResourcePacker, "wb") as f:
                f.write(save_bytes)
            return 1

        _close_env(env)
        return 0

    except Exception:
        return 0

def FixReset(path):
    if not os.path.exists(path):
        return

    env = _load_from_bytes(path)
    changed = False

    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue

        data = obj.read()

        if data.name == "ResourceVerificationInfoSetXML":
            tree = data.read_typetree()
            tree["AllZipVerificationInfo"] = []
            tree["AllDatabinVerificationInfo"] = []

            nodes = obj.get_typetree_nodes()
            if not nodes:
                continue

            writer = EndianBinaryWriter(endian=obj.reader.endian)
            i = c_uint32(1)
            found_m_Name = False

            while i.value < len(nodes):
                node = nodes[i.value]

                if node.m_Level == 1:
                    if node.m_Name == "m_Name":
                        found_m_Name = True
                        i.value += len(TypeTreeHelper.get_nodes(nodes, i.value))
                        continue

                    elif found_m_Name:
                        val = tree.get(node.m_Name)
                        if val is not None:
                            TypeTreeHelper.write_value(val, nodes, writer, i)
                            i.value += 1
                            continue

                i.value += 1

            data.save(raw_data=writer.bytes)
            changed = True

    if changed:
        try:
            save_bytes = env.file.save(packer="none")
        except Exception:
            save_bytes = env.file.save()
        _close_env(env)
        with open(path, "wb") as f:
            f.write(save_bytes)
    else:
        _close_env(env)

def iOS(folder):
    old = bytes.fromhex("323032322E332E356631000D")
    new = bytes.fromhex("323032322E332E3566310009")

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".assetbundle"):
                path = os.path.join(root, file)

                with open(path, "rb") as f:
                    data = f.read()

                if old in data:
                    with open(path, "wb") as f:
                        f.write(data.replace(old, new))

def lz4(folder):
    for file in os.listdir(folder):
        if not file.endswith(".assetbundle"):
            continue

        path = os.path.join(folder, file)

        try:
            env = Data.UnityPy_AOV.load(path)

            try:
                data = env.save(packer="lz4")
            except:
                data = env.file.save(packer="lz4")

            with open(path, "wb") as f:
                f.write(data)

        except Exception as e:
            print("Lỗi:", file, e)

def NenAsset(folder, platform="adr", packer="lz4"):
    root = Path(folder)

    if not root.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục: {folder}")

    bundles = list(root.glob("*.assetbundle"))

    if not bundles:
        print("Không tìm thấy file .assetbundle")
        return

    for bundle_path in bundles:
        try:
            env = Data.UnityPy_AOV.load(str(bundle_path))

            if platform == "adr":
                if hasattr(env.file, "useADR"):
                    env.file.useADR = True
                if hasattr(env.file, "useIOS"):
                    env.file.useIOS = False

            elif platform == "ios":
                if hasattr(env.file, "useADR"):
                    env.file.useADR = False
                if hasattr(env.file, "useIOS"):
                    env.file.useIOS = True

            data = env.file.save(packer)

            with open(bundle_path, "wb") as f:
                f.write(data)

        except Exception as e:
            print(f"[X] {bundle_path.name}: {e}")

def AntiResetMod(Assetbundle):
    folder_name = Assetbundle
    file_name = "resourceverificationinfosetall.assetbundle"
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, file_name)
    with open(file_path, "wb") as f:
        f.write(b"MOD BY: KM MOD AOV")