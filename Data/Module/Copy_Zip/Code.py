from __future__ import annotations

import ctypes
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Iterable, Iterator


class _OS(Enum):
    WINDOWS = auto()
    MACOS = auto()
    LINUX = auto()
    ANDROID = auto()
    IOS = auto()
    UNKNOWN = auto()


def _detect_os() -> _OS:
    s = platform.system()
    if s == "Windows":
        return _OS.WINDOWS
    if s == "Darwin":
        try:
            r = subprocess.run(["uname", "-m"], capture_output=True, text=True)
            if "arm" in r.stdout and not os.path.exists("/Applications"):
                return _OS.IOS
        except Exception:
            pass
        return _OS.MACOS
    if s == "Linux":
        if os.path.exists("/system/build.prop") or os.environ.get("ANDROID_ROOT"):
            return _OS.ANDROID
        return _OS.LINUX
    return _OS.UNKNOWN


_PLATFORM: _OS = _detect_os()
_IS_LINUX: bool = _PLATFORM in (_OS.LINUX, _OS.ANDROID)
_IS_WINDOWS: bool = _PLATFORM == _OS.WINDOWS
_IS_MACOS: bool = _PLATFORM == _OS.MACOS
_IS_MOBILE: bool = _PLATFORM in (_OS.ANDROID, _OS.IOS)

_CPU_COUNT = os.cpu_count() or 4
_MAX_IO_WORKERS: int = min(_CPU_COUNT * 2, 8) if _IS_MOBILE else min(_CPU_COUNT * 4, 64)
_CHUNK: int = 1 << 19 if _IS_MOBILE else 1 << 20

log = logging.getLogger(__name__)


def set_max_workers(n: int) -> None:
    global _MAX_IO_WORKERS
    _MAX_IO_WORKERS = max(1, n)
    log.info("max_workers set to %d", _MAX_IO_WORKERS)


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


@dataclass
class OpResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    stats: dict[str, float] = field(default_factory=dict)

    def add_error(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)
        log.error(msg)

    def __bool__(self) -> bool:
        return self.ok


if _IS_WINDOWS:
    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _CopyFileExW = _KERNEL32.CopyFileExW
    _CopyFileExW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    _CopyFileExW.restype = ctypes.c_int


def _ensure_parent(dst: str) -> None:
    parent = os.path.dirname(os.path.abspath(dst))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _copy_metadata(src: str, dst: str) -> None:
    try:
        shutil.copystat(src, dst, follow_symlinks=True)
    except OSError:
        pass


def _sendfile_copy(src: str, dst: str) -> None:
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        src_fd = fsrc.fileno()
        dst_fd = fdst.fileno()
        size = os.fstat(src_fd).st_size
        offset = 0
        while offset < size:
            sent = os.sendfile(dst_fd, src_fd, offset, min(size - offset, 1 << 30))
            if sent <= 0:
                raise OSError("sendfile returned 0 before copy completed")
            offset += sent


def _fcopyfile_copy(src: str, dst: str) -> None:
    shutil.copy2(src, dst)


def _win_copyfileex(src: str, dst: str) -> None:
    ok = _CopyFileExW(
        src,
        dst,
        None,
        None,
        None,
        0,
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), f"CopyFileExW failed: {src!r} -> {dst!r}")


def _chunked_copy(src: str, dst: str) -> None:
    buf = bytearray(_CHUNK)
    view = memoryview(buf)
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        while True:
            n = fsrc.readinto(buf)
            if not n:
                break
            fdst.write(view[:n])


def _build_copy_chain() -> list[tuple[str, Callable[[str, str], None], bool]]:
    chain: list[tuple[str, Callable[[str, str], None], bool]] = []
    if _IS_LINUX and hasattr(os, "sendfile"):
        chain.append(("sendfile", _sendfile_copy, True))
    if _IS_WINDOWS:
        chain.append(("CopyFileExW", _win_copyfileex, True))
    if _IS_MACOS:
        chain.append(("fcopyfile", _fcopyfile_copy, False))
    chain.append(("chunked", _chunked_copy, True))
    chain.append(("shutil", shutil.copy2, False))
    return chain


_COPY_CHAIN = _build_copy_chain()


def _copy_file_strict(src: str, dst: str) -> None:
    _ensure_parent(dst)

    last_exc: Exception | None = None
    for name, fn, need_meta in _COPY_CHAIN:
        try:
            fn(src, dst)
            if need_meta:
                _copy_metadata(src, dst)
            return
        except Exception as exc:
            last_exc = exc
            log.debug("copy backend %r failed (%s -> %s): %s", name, src, dst, exc)

    raise OSError(f"all copy backends failed ({src} -> {dst}): {last_exc}")


def fast_copy_file(src: str, dst: str) -> None:
    try:
        _copy_file_strict(src, dst)
    except Exception as exc:
        log.error("fast_copy_file failed (%s -> %s): %s", src, dst, exc)


def MoveFile(src: str, dst: str) -> None:
    try:
        _ensure_parent(dst)
        os.replace(src, dst)
        return
    except OSError:
        pass

    try:
        _copy_file_strict(src, dst)
        os.remove(src)
    except Exception as exc:
        log.error("MoveFile failed (%s -> %s): %s", src, dst, exc)


def MoveFolder(src: str, dst: str) -> None:
    try:
        parent = os.path.dirname(os.path.abspath(dst.rstrip("/\\")))
        if parent:
            os.makedirs(parent, exist_ok=True)
        os.replace(src, dst)
        return
    except OSError:
        pass

    result = CopyFolder(src, dst)
    if result:
        fast_rmtree(src)
    else:
        log.error("MoveFolder failed (%s -> %s): %s", src, dst, result.errors)


def fast_rmtree(path: str, retries: int = 4, base_delay: float = 0.2) -> None:
    if not os.path.exists(path):
        return

    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return
        except Exception as exc:
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt)
                log.debug(
                    "rmtree attempt %d/%d failed (%r): %s — retry in %.2fs",
                    attempt + 1, retries, path, exc, wait
                )
                time.sleep(wait)
            else:
                log.warning("rmtree gave up after %d attempts (%r): %s", retries, path, exc)
                shutil.rmtree(path, ignore_errors=True)


def CopyFolder(
    src_folder: str,
    dest_folder: str,
    exclude: Iterable[str] | None = None,
) -> OpResult:
    result = OpResult()

    if not os.path.exists(src_folder):
        result.add_error(f"CopyFolder: source does not exist: {src_folder!r}")
        return result

    os.makedirs(dest_folder, exist_ok=True)
    copied = False

    if _IS_LINUX:
        copied = _native_cp_linux(src_folder, dest_folder)
    elif _IS_MACOS:
        copied = _native_cp_macos(src_folder, dest_folder)
    elif _IS_WINDOWS:
        copied = _native_robocopy(src_folder, dest_folder)

    if not copied:
        _threaded_copy_folder(src_folder, dest_folder, result)

    if exclude:
        for item in exclude:
            ex = os.path.join(dest_folder, item)
            if os.path.isdir(ex):
                fast_rmtree(ex)
            elif os.path.exists(ex):
                try:
                    os.remove(ex)
                except OSError as exc:
                    result.add_error(f"exclude remove failed {ex!r}: {exc}")

    return result


def _native_cp_linux(src: str, dst: str) -> bool:
    try:
        proc = subprocess.run(
            ["cp", "-af", os.path.join(src, "."), dst],
            check=False,
            capture_output=True
        )
        return proc.returncode == 0
    except Exception as exc:
        log.debug("cp -af failed: %s", exc)
        return False


def _native_cp_macos(src: str, dst: str) -> bool:
    try:
        proc = subprocess.run(
            ["cp", "-Rpf", os.path.join(src, "."), dst],
            check=False,
            capture_output=True
        )
        return proc.returncode == 0
    except Exception as exc:
        log.debug("cp -Rpf failed: %s", exc)
        return False


def _native_robocopy(src: str, dst: str) -> bool:
    try:
        w = max(1, min(_MAX_IO_WORKERS, 128))
        proc = subprocess.run(
            ["robocopy", src, dst, "/E", f"/MT:{w}", "/NP", "/NFL", "/NDL", "/NJH", "/NJS"],
            check=False,
            capture_output=True,
        )
        return proc.returncode <= 7
    except FileNotFoundError:
        return False
    except Exception as exc:
        log.debug("robocopy failed: %s", exc)
        return False


def _threaded_copy_folder(src: str, dst: str, result: OpResult) -> None:
    tasks: list[tuple[str, str]] = []

    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        dst_root = dst if rel_root == "." else os.path.join(dst, rel_root)
        os.makedirs(dst_root, exist_ok=True)

        for d in dirs:
            os.makedirs(os.path.join(dst_root, d), exist_ok=True)

        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(dst_root, f)
            tasks.append((s, d))

    if not tasks:
        return

    workers = min(len(tasks), _MAX_IO_WORKERS)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_copy_file_strict, s, d): (s, d) for s, d in tasks}
        for fut in as_completed(futures):
            s, d = futures[fut]
            if exc := fut.exception():
                result.add_error(f"copy failed {s!r} -> {d!r}: {exc}")


def CopyFile1(src_list: list[str], dest_list: list[str]) -> OpResult:
    result = OpResult()

    if len(src_list) != len(dest_list):
        result.add_error(
            f"CopyFile1: length mismatch src_list={len(src_list)} dest_list={len(dest_list)}"
        )
        return result

    if not src_list:
        return result

    w = min(len(src_list), _MAX_IO_WORKERS, 32)
    with ThreadPoolExecutor(max_workers=w) as pool:
        futures = {
            pool.submit(_copy_file_strict, s, d): (s, d)
            for s, d in zip(src_list, dest_list)
        }
        for fut in as_completed(futures):
            s, d = futures[fut]
            if exc := fut.exception():
                result.add_error(f"CopyFile1 {s!r} -> {d!r}: {exc}")

    return result


def CopyFile(s: str, d: str) -> None:
    fast_copy_file(s, d)


def _iter_folder_files(folder: str) -> Iterator[tuple[str, str]]:
    for root, _, files in os.walk(folder):
        for f in files:
            abs_path = os.path.join(root, f)
            arcname = os.path.relpath(abs_path, folder).replace(os.sep, "/")
            yield abs_path, arcname


def Zip_Folder(
    folder_path: str,
    output_zip_path: str,
    compression: int = zipfile.ZIP_STORED,
    level: int | None = None,
) -> None:
    if not os.path.exists(folder_path):
        log.warning("Zip_Folder: folder does not exist: %r", folder_path)
        return

    folder_abs = os.path.abspath(folder_path)
    output_abs = os.path.abspath(output_zip_path)
    out_dir = os.path.dirname(output_abs) or "."
    fd, tmp = tempfile.mkstemp(dir=out_dir, suffix=".tmp")
    os.close(fd)

    try:
        kw: dict = {"compression": compression, "allowZip64": True}
        if level is not None and compression == zipfile.ZIP_DEFLATED:
            kw["compresslevel"] = level

        tmp_abs = os.path.abspath(tmp)

        with zipfile.ZipFile(tmp, "w", **kw) as zf:
            for abs_path, arcname in _iter_folder_files(folder_abs):
                file_abs = os.path.abspath(abs_path)
                if file_abs == tmp_abs or file_abs == output_abs:
                    continue
                zf.write(file_abs, arcname)

        os.replace(tmp, output_abs)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

    fast_rmtree(folder_path)


def ZipFolderCompressed(folder_path: str, output_zip_path: str, level: int = 6) -> None:
    Zip_Folder(
        folder_path,
        output_zip_path,
        compression=zipfile.ZIP_DEFLATED,
        level=level
    )


def AddFoldersToZip(zip_path: str, folder_list: list[str]) -> None:
    if not folder_list:
        return

    zip_path = os.path.abspath(zip_path)
    new_files: dict[str, str] = {}

    for folder_path in folder_list:
        if not os.path.exists(folder_path):
            log.warning("AddFoldersToZip: folder missing, skipping: %r", folder_path)
            continue

        folder_abs = os.path.abspath(folder_path)
        parent_name = os.path.basename(folder_abs.rstrip("/\\"))
        for abs_path, rel in _iter_folder_files(folder_abs):
            new_files[f"{parent_name}/{rel}"] = abs_path

    zip_dir = os.path.dirname(zip_path) or "."
    fd, temp_zip = tempfile.mkstemp(dir=zip_dir, suffix=".tmp")
    os.close(fd)

    try:
        with zipfile.ZipFile(
            temp_zip,
            "w",
            compression=zipfile.ZIP_STORED,
            allowZip64=True
        ) as new_zf:
            if os.path.exists(zip_path):
                with zipfile.ZipFile(zip_path, "r") as old_zf:
                    for info in old_zf.infolist():
                        if info.filename in new_files:
                            continue
                        with old_zf.open(info) as src, new_zf.open(info, "w") as dst:
                            shutil.copyfileobj(src, dst, length=_CHUNK)

            for arcname, full_path in new_files.items():
                new_zf.write(full_path, arcname)

        os.replace(temp_zip, zip_path)

    except Exception:
        try:
            os.remove(temp_zip)
        except OSError:
            pass
        raise

    for folder_path in folder_list:
        if os.path.exists(folder_path):
            fast_rmtree(folder_path)


def _safe_extract_target(dest_dir: str, member_name: str) -> str | None:
    target = os.path.realpath(os.path.join(dest_dir, member_name))
    if target == dest_dir or target.startswith(dest_dir + os.sep):
        return target
    return None


def UnzipTo(zip_path: str, dest_dir: str, workers: int | None = None) -> OpResult:
    result = OpResult()
    dest_dir = os.path.abspath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        entries = [info for info in zf.infolist() if not info.filename.endswith("/")]

    if not entries:
        return result

    n = min(len(entries), workers or _MAX_IO_WORKERS)

    def _extract(info: zipfile.ZipInfo) -> None:
        target = _safe_extract_target(dest_dir, info.filename)
        if not target:
            log.warning("UnzipTo: path traversal blocked: %r", info.filename)
            return

        parent = os.path.dirname(target)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as local_zf:
            with local_zf.open(info.filename) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, length=_CHUNK)

        try:
            ts = time.mktime(info.date_time + (0, 0, -1))
            os.utime(target, (ts, ts))
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = {pool.submit(_extract, info): info for info in entries}
        for fut in as_completed(futures):
            info = futures[fut]
            if exc := fut.exception():
                result.add_error(f"extract failed {info.filename!r}: {exc}")

    return result


def get_folder_size(path: str) -> int:
    total = 0
    stack = [path]

    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                    except OSError:
                        pass
        except OSError as exc:
            log.warning("get_folder_size: cannot scan %r: %s", cur, exc)

    return total


log.debug(
    "file_utils ready | os=%s | workers=%d | chunk=%d KiB | backends=%s",
    _PLATFORM.name,
    _MAX_IO_WORKERS,
    _CHUNK >> 10,
    [name for name, _, _ in _COPY_CHAIN],
)
