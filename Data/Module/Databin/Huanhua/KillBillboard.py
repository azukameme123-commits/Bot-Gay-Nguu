import os
import re
import struct

def ModThongBao2(Huanhua, ID_SKIN):
    ID_SKIN = int(ID_SKIN)

    FILE_SKIN = os.path.join(Huanhua, "ResBillboardSkinCfg.bytes")
    FILE_BILLBOARD = os.path.join(Huanhua, "ResBillboardCfg.bytes")
    FILE_KILL = os.path.join(Huanhua, "ResKillBillboardCfg.bytes")

    def read_file(path):
        with open(path, "rb") as f:
            return f.read()

    def write_file(path, data):
        with open(path, "wb") as f:
            f.write(data)

    if not os.path.isfile(FILE_SKIN):
        return

    data_skin = read_file(FILE_SKIN)
    skin_hex = struct.pack("<I", ID_SKIN)

    billboard_id = None
    pos = 0

    while True:
        pos = data_skin.find(b"\x0C\x00\x00\x00", pos)
        if pos == -1:
            break

        check = pos + 8

        if (
            data_skin[check:check+4] == b"\x01\x00\x00\x00"
            and data_skin[check+4:check+8] == skin_hex
        ):
            billboard_id = data_skin[pos+4:pos+8]
            break

        pos += 1

    if billboard_id is None:
        return

    if os.path.isfile(FILE_BILLBOARD):
        data = read_file(FILE_BILLBOARD)
        new_data = bytearray(data)
        i = 0

        while True:
            i = data.find(b"\x0F\x00\x00\x00" + billboard_id, i)
            if i == -1:
                break

            new_data[i+4:i+8] = b"\x00\x00\x00\x00"
            new_data[i+13:i+17] = b"\x00\x00\x00\x00"
            i += 1

        write_file(FILE_BILLBOARD, bytes(new_data))

    if os.path.isfile(FILE_KILL):
        data_kill = read_file(FILE_KILL)
        new_data = bytearray(data_kill)

        size = len(data_kill)
        i = 0x8C

        while i < size - 8:
            block_len = struct.unpack("<I", data_kill[i:i+4])[0]

            if 0 < block_len < 500 and i + 4 + block_len <= size:
                offset = i + 4

                if data_kill[offset:offset+4] == billboard_id:
                    new_data[offset:offset+4] = b"\x00\x00\x00\x00"

                i += 4 + block_len
            else:
                i += 1

        write_file(FILE_KILL, bytes(new_data))

    try:
        os.remove(FILE_SKIN)
    except:
        pass
        
def ModThongBao(ResKillBillboardCfg, ID):
    with open(ResKillBillboardCfg, 'rb') as f:
        code = f.read()[140:]
        codelist =code.split(b'\x00\x01\x00\x00\x00\x00\x01')
    if ID[:3] == '150':
        A = ''
        if ID == '15015':
            A = b'UI3D/Battle/Broadcast/20/'
        if ID == '15012':
            A = b'UI3D/Battle/Broadcast/9/'
        if ID == '15013':
            A = b'UI3D/Battle/Broadcast/16/'
        if ID == '15009':
            A = b'UI3D/Battle/Broadcast/45/'
        if A != '':
            for i in codelist:
                if  b'UI3D/Battle/Broadcast/18/' in i:
                    M = i[1:8]
                    
                    B = i
                if  A in i:
                    M1 = i[1:8]
                    B1 = i
            C = B.replace(M, M1)
            C1 = B1.replace(M1, M)

            with open(ResKillBillboardCfg, 'rb') as f:
                code1 = f.read().replace(B, C).replace(B1,C1)
            with open(ResKillBillboardCfg, 'wb') as f:
                f.write(code1)