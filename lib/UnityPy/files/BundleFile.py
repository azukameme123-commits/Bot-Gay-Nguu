from collections import namedtuple
import re
from typing import Tuple, Union
from Crypto.Cipher import AES
from . import File
from ..enums import ArchiveFlags, ArchiveFlagsOld, CompressionFlags, BuildTarget
from ..helpers import ArchiveStorageManager, CompressionHelper
from ..streams import EndianBinaryReader, EndianBinaryWriter

from .. import config

BlockInfo = namedtuple("BlockInfo", "flags tmp compressedSize uncompressedSize")
DirectoryInfoFS = namedtuple("DirectoryInfoFS", "size offset flags path")
reVersion = re.compile(r"^(\d+)\.(\d+)\.(\d+)")


class BundleFile(File.File):
    format: int
    is_changed: bool
    signature: str
    version_engine: str
    version_player: str
    dataflags: Union[ArchiveFlags, ArchiveFlagsOld]
    decryptor: ArchiveStorageManager.ArchiveStorageDecryptor = None
    useIOS: bool = False
    useADR: bool = False

    def __init__(
        self,
        reader: EndianBinaryReader,
        parent: File,
        name: str = None,
        useIOS: bool = False,
        useADR: bool = False,
        **kwargs,
    ):
        super().__init__(parent=parent, name=name, **kwargs)
        self.HeaderAESKey = b'\xE3\x05\x62\x14\xD6\x0A\x20\x25\x36\x96\x1B\x07\x74\xDC\x24\x02'
        self.HeaderAESIV = b'\x1D\x6E\xEB\x4C\x86\xA9\x45\x44\x45\x72\x12\x21\x2B\x43\x25\x2F'
        self.useIOS = useIOS
        self.useADR = useADR
        self.decryptor = None
        self._block_info_flags = 0

        signature = self.signature = reader.read_string_to_null()
        self.version = reader.read_u_int()
        self.version_player = reader.read_string_to_null()
        self.version_engine = reader.read_string_to_null()

        if signature != "UnityFS":
            raise NotImplementedError(
                f"Only AOV UnityFS bundles are supported: {signature}"
            )

        m_DirectoryInfo, blocksReader = self.read_fs(reader)
        self.read_files(blocksReader, m_DirectoryInfo)

    def decryptHeader(self, data):
        data = bytes(data)
        data = data[7::-1] + data[8:12][::-1] + data[12:16][::-1]
        cipher = AES.new(self.HeaderAESKey, AES.MODE_CBC, self.HeaderAESIV)
        dataDecrypt = cipher.decrypt(data)
        return dataDecrypt

    def read_fs(self, reader: EndianBinaryReader):
        bundleHeader = reader.read_bytes(16)

        self.dataflags = reader.read_u_int()

        version = self.get_version_tuple()
        if (
            version < (2020,)
            or (version[0] == 2020 and version < (2020, 3, 34))
            or (version[0] == 2021 and version < (2021, 3, 2))
            or (version[0] == 2022 and version < (2022, 1, 1))
        ):
            self.dataflags = ArchiveFlagsOld(self.dataflags)
        else:
            self.dataflags = ArchiveFlags(self.dataflags)

        if self.version >= 7:
            reader.align_stream(16)

        if self.dataflags & self.dataflags.UsesAssetBundleEncryption:
            bundleHeader = self.decryptHeader(bundleHeader)
            size = int.from_bytes(bundleHeader[0x0:0x8], 'little')
            compressedSize = int.from_bytes(bundleHeader[0x8:0xc], 'little')
            uncompressedSize = int.from_bytes(bundleHeader[0xc:0x10], 'little')
        else:
            size = int.from_bytes(bundleHeader[0x0:0x8], 'big')
            compressedSize = int.from_bytes(bundleHeader[0x8:0xc], 'big')
            uncompressedSize = int.from_bytes(bundleHeader[0xc:0x10], 'big')

        start = reader.Position
        if (
            self.dataflags & ArchiveFlags.BlocksInfoAtTheEnd
        ):
            reader.Position = reader.Length - compressedSize
            blocksInfoBytes = reader.read_bytes(compressedSize)
            reader.Position = start
        else:
            if self.dataflags & self.dataflags.UsesAssetBundleEncryption:
                self.decryptor = ArchiveStorageManager.ArchiveStorageDecryptor(reader)
            blocksInfoBytes = reader.read_bytes(compressedSize)
            if self.dataflags & self.dataflags.UsesAssetBundleEncryption:
                blocksInfoBytes = self.decryptor.decrypt_block(bytes(blocksInfoBytes))

        blocksInfoBytes = self.decompress_data(
            blocksInfoBytes, uncompressedSize, self.dataflags
        )

        blocksInfoReader = EndianBinaryReader(blocksInfoBytes, endian=">", offset=start)

        uncompressedDataHash = blocksInfoReader.read_bytes(16)

        
        
        
        
        
        
        
        
        
        
        
        
        is_encrypted = bool(
            isinstance(self.dataflags, (ArchiveFlags, ArchiveFlagsOld))
            and self.dataflags & self.dataflags.UsesAssetBundleEncryption
        )

        def _read_blocks_standard(r, count):
            blocks = []
            for _ in range(count):
                u = r.read_u_int(); c = r.read_u_int(); f = r.read_u_short()
                if not (0 <= c <= 0x40000000 and 0 <= u <= 0x40000000):
                    raise ValueError("kich thuoc block khong hop le (standard)")
                blocks.append(BlockInfo(f, 0, c, u))
            return blocks

        def _read_blocks_aov(r, count):
            blocks = []
            for _ in range(count):
                f = r.read_u_short(); t = r.read_u_short(); c = r.read_u_int(); u = r.read_u_int()
                if not (0 <= c <= 0x40000000 and 0 <= u <= 0x40000000):
                    raise ValueError("kich thuoc block khong hop le (aov)")
                blocks.append(BlockInfo(f, t, c, u))
            return blocks

        def _valid_path(path):
            return bool(path) and len(path) <= 512 and path.isprintable()

        def _read_nodes_standard(r, count):
            nodes = []
            for _ in range(count):
                offset = r.read_long(); size = r.read_long(); flags = r.read_u_int()
                path = r.read_string_to_null()
                if size < 0 or offset < 0 or not _valid_path(path):
                    raise ValueError("node khong hop le (standard)")
                nodes.append(DirectoryInfoFS(size, offset, flags, path))
            return nodes

        def _read_nodes_aov(r, count):
            nodes = []
            for _ in range(count):
                size = r.read_long(); offset = r.read_long(); flags = r.read_u_int()
                path = r.read_string_to_null()
                if size < 0 or offset < 0 or not _valid_path(path):
                    raise ValueError("node khong hop le (aov)")
                nodes.append(DirectoryInfoFS(size, offset, flags, path))
            return nodes

        def _try_parse(block_fn, node_fn):
            saved = blocksInfoReader.Position
            try:
                count = blocksInfoReader.read_int()
                if not (0 < count <= 4096):
                    raise ValueError("blocksInfoCount khong hop le")
                blocks = block_fn(blocksInfoReader, count)
                ncount = blocksInfoReader.read_int()
                if not (0 < ncount <= 4096):
                    raise ValueError("nodesCount khong hop le")
                nodes = node_fn(blocksInfoReader, ncount)
                if blocksInfoReader.Position != blocksInfoReader.Length:
                    raise ValueError("con du byte thua sau khi doc blocksInfo")
                return blocks, nodes
            except Exception:
                blocksInfoReader.Position = saved
                raise

        _candidates = (
            [(_read_blocks_aov, _read_nodes_aov), (_read_blocks_standard, _read_nodes_standard)]
            if is_encrypted else
            [(_read_blocks_standard, _read_nodes_standard), (_read_blocks_aov, _read_nodes_aov)]
        )
        m_BlocksInfo = m_DirectoryInfo = None
        _last_err = None
        for block_fn, node_fn in _candidates:
            try:
                m_BlocksInfo, m_DirectoryInfo = _try_parse(block_fn, node_fn)
                break
            except Exception as e:
                _last_err = e
        if m_BlocksInfo is None:
            raise ValueError(f"Khong doc duoc blocksInfo (ca 2 dinh dang deu loi): {_last_err}")

        if m_BlocksInfo:
            self._block_info_flags = m_BlocksInfo[0].flags

        if (
            isinstance(self.dataflags, ArchiveFlags)
            and self.dataflags & ArchiveFlags.BlockInfoNeedPaddingAtStart
        ):
            reader.align_stream(16)

        blocksReader = EndianBinaryReader(
            b"".join(
                self.decompress_data(
                    reader.read_bytes(blockInfo.compressedSize),
                    blockInfo.uncompressedSize,
                    blockInfo.flags,
                    i,
                )
                for i, blockInfo in enumerate(m_BlocksInfo)
            ),
            offset=(blocksInfoReader.real_offset()),
        )
        return m_DirectoryInfo, blocksReader

    def save(self, packer=None):
        writer = EndianBinaryWriter()

        writer.write_string_to_null(self.signature)
        writer.write_u_int(self.version)
        writer.write_string_to_null(self.version_player)
        writer.write_string_to_null(self.version_engine)

        if self.signature != "UnityFS":
            raise NotImplementedError(
                f"Only AOV UnityFS bundles are supported: {self.signature}"
            )

        if not packer or packer == "none":
            self.save_fs(writer, 64, 64)
        elif packer == "lz4":
            self.save_fs(writer, data_flag=194, block_info_flag=2)
        elif packer == "lzma":
            self.save_fs(writer, data_flag=193, block_info_flag=1)
        elif isinstance(packer, tuple):
            self.save_fs(writer, *packer)
        else:
            raise NotImplementedError(f"Unsupported UnityFS packer: {packer!r}")
        return writer.bytes

    def save_fs(self, writer, data_flag, block_info_flag):
        if self.useIOS or self.useADR:
            target_platform = 0x09 if self.useIOS else 0x0D
            for f in self.files.values():
                if isinstance(f, File.SerializedFile.SerializedFile):
                    f._m_target_platform = target_platform
                    f.target_platform = BuildTarget(target_platform)
    
        data_writer = EndianBinaryWriter()
        files = [
            (
                name,
                f.flags,
                data_writer.write_bytes(
                    f.bytes
                    if isinstance(f, (EndianBinaryReader, EndianBinaryWriter))
                    else f.save()
                ),
            )
            for name, f in self.files.items()
        ]

        file_data = data_writer.bytes
        data_writer.dispose()
        uncompressed_data_size = len(file_data)

        switch = block_info_flag & 0x3F
        if switch == 1:
            file_data = CompressionHelper.compress_lzma(file_data)
        elif switch in [2, 3]:
            file_data = CompressionHelper.compress_lz4(file_data)
        elif switch == 4:
            raise NotImplementedError
        compressed_data_size = len(file_data)

        block_writer = EndianBinaryWriter(b"\x00" * 0x10)
        block_writer.write_int(1)

        block_writer.write_u_short(block_info_flag)
        block_writer.write_u_short(0)
        block_writer.write_u_int(compressed_data_size)
        block_writer.write_u_int(uncompressed_data_size)

        if not data_flag & 0x40:
            raise NotImplementedError(
                "UnityPy always writes DirectoryInfo, so data_flag must include 0x40"
            )
        block_writer.write_int(len(files))
        offset = 0
        for f_name, f_flag, f_len in files:
            block_writer.write_long(f_len)
            block_writer.write_long(offset)
            block_writer.write_u_int(f_flag)
            block_writer.write_string_to_null(f_name)
            offset += f_len

        block_data = block_writer.bytes
        block_writer.dispose()

        uncompressed_block_data_size = len(block_data)

        switch = data_flag & 0x3F
        if switch == 1:
            block_data = CompressionHelper.compress_lzma(block_data)
        elif switch in [2, 3]:
            block_data = CompressionHelper.compress_lz4(block_data)
        elif switch == 4:
            raise NotImplementedError

        compressed_block_data_size = len(block_data)

        writer_header_pos = writer.Position
        writer.write_u_long(7)
        writer.write_u_int(compressed_block_data_size)
        writer.write_u_int(uncompressed_block_data_size)
        writer.write_u_int(data_flag)

        if self.version >= 7:
            writer.align_stream(16)

        if data_flag & 0x80:
            if data_flag & 0x200:
                writer.align_stream(16)
            writer.write(file_data)
            writer.write(block_data)
        else:
            writer.write(block_data)
            if data_flag & 0x200:
                writer.align_stream(16)
            writer.write(file_data)

        writer_end_pos = writer.Position
        writer.Position = writer_header_pos

        writer.write_u_long(writer_end_pos)

        writer.Position = writer_end_pos

    def decompress_data(
            self, compressed_data: bytes, uncompressed_size: int, flags: int, index: int = 0
        ) -> bytes:
            
            
            
            
            
            
            
            
            
            
            
            comp_flag = flags & ArchiveFlags.CompressionTypeMask

            if comp_flag == CompressionFlags.LZMA:
                return CompressionHelper.decompress_lzma(compressed_data)
            elif comp_flag in [CompressionFlags.LZ4, CompressionFlags.LZ4HC]:
                return CompressionHelper.decompress_lz4(compressed_data, uncompressed_size)
            elif comp_flag == CompressionFlags.LZHAM:
                raise NotImplementedError("LZHAM decompression not implemented")
            else:
                return compressed_data

    def get_version_tuple(self) -> Tuple[int, int, int]:
        version = self.version_engine
        if not version or version == "0.0.0":
            version = config.get_fallback_version()
        match = reVersion.match(version)
        if match is None:
            raise ValueError(f"Invalid Unity version: {version!r}")
        return tuple(map(int, match.groups()))
       