import os


# ============================================================================
#  CAM XA MODULE
#  - CamXa(chedocamyn, CamXa_MOD): giữ lại chế độ y/n (mặc định heightRate = 1.3)
#  - CamXaFile(CamXa_MOD, percent): mod cam xa theo phần trăm (1%..100%)
#      + Mặc định heightRate = 1.0
#      + Cứ mỗi 1%  -> +0.05
#      + 35%        -> 1.0 + 35 * 0.05 = 2.75  ✓
# ============================================================================


def _format_height_rate(v: float) -> str:
    """
    Format số float chuẩn cho heightRate:
      - 1.0  -> "1.0"
      - 1.05 -> "1.05"
      - 2.75 -> "2.75"
      - 6.0  -> "6.0"
    """
    s = f"{v:.2f}"
    # Bỏ trailing zero, nhưng luôn giữ ít nhất 1 chữ số thập phân
    if s.endswith('0') and not s.endswith('.0'):
        s = s.rstrip('0')
    if s.endswith('.'):
        s += '0'
    return s


def _build_track_block(height_rate: float) -> bytes:
    """
    Trả về block <Track>...</Track> có cấu trúc CHUẨN, thụt lề CHUẨN của
    các file .xml trong Ages (2-space indent + CRLF), khớp form của những
    <Track>/<Event> khác trong junglemark.xml, Back.xml, ... và luôn dán
    NGAY TRƯỚC </Action>.
    """
    hr = _format_height_rate(height_rate)
    block = (
        b'  <Track trackName="SetCameraHeightDuration0" eventType="SetCameraHeightDuration" '
        b'guid="9489c796-894b-4c2e-9a95-acf27873964a" enabled="true" useRefParam="false" '
        b'refParamName="" r="0.000" g="0.000" b="0.000" execOnForceStopped="false" '
        b'execOnActionCompleted="false" stopAfterLastEvent="true">\r\n'
        b'      <Event eventName="SetCameraHeightDuration" time="0.000" length="1.000" '
        b'isDuration="true" guid="422a1ed9-a12c-44b3-a9c5-3fe899d689dd">\r\n'
        b'        <int name="slerpTick" value="0" refParamName="" useRefParam="false"/>\r\n'
        b'        <float name="heightRate" value="' + hr.encode() + b'" refParamName="" useRefParam="false"/>\r\n'
        b'        <bool name="bOverride" value="true" refParamName="" useRefParam="false"/>\r\n'
        b'        <bool name="leftTimeSlerpBack" value="true" refParamName="" useRefParam="false"/>\r\n'
        b'        <bool name="cutBackOnExit" value="true" refParamName="" useRefParam="false"/>\r\n'
        b'        <bool name="exitKeepCurrentValue" value="true" refParamName="" useRefParam="false"/>\r\n'
        b'        <bool name="isSlerpBackWhenInterrupted" value="true" refParamName="" useRefParam="false"/>\r\n'
        b'        <int name="slerpBackTick" value="1500" refParamName="" useRefParam="false"/>\r\n'
        b'        <String name="refParamName" value="" refParamName="" useRefParam="false"/>\r\n'
        b'      </Event>\r\n'
        b'    </Track>\r\n'
        b'  </Action>'
    )
    return block


def _strip_existing_camxa_track(content: bytes) -> bytes:
    """
    Nếu file trước đó đã bị mod cam xa (đã có Track SetCameraHeightDuration0)
    thì gỡ nguyên block Track đó ra trước khi dán mới -> tránh dán chồng.
    Sau khi gỡ, khôi phục lại </Action> đúng vị trí và indent chuẩn.
    """
    marker = b'<Track trackName="SetCameraHeightDuration0"'
    idx = content.find(marker)
    if idx == -1:
        return content

    # Đầu dòng chứa marker (kể cả indent phía trước)
    line_start = content.rfind(b'\n', 0, idx)
    line_start = 0 if line_start == -1 else line_start + 1

    # Kết thúc block: </Track> đầu tiên sau marker + xuống dòng sau nó
    end_track = content.find(b'</Track>', idx)
    if end_track == -1:
        return content
    after_track_line = content.find(b'\n', end_track)
    after_track_line = len(content) if after_track_line == -1 else after_track_line + 1

    tail = content[after_track_line:]
    # Nếu ngay sau block Track đó đã có </Action> (do dán từ lần trước)
    # thì bỏ luôn dòng </Action> đó để cấu trúc quay về nguyên gốc.
    tail_stripped = tail.lstrip()
    if tail_stripped.startswith(b'</Action>'):
        # bỏ dòng </Action> hiện tại
        nl = tail.find(b'\n')
        tail = tail[nl + 1:] if nl != -1 else b''
        # Trả lại </Action> chuẩn (không có indent thừa)
        return content[:line_start] + b'</Action>' + (b'\r\n' if tail else b'') + tail
    return content[:line_start] + tail


def CamXa(chedocamyn, CamXa_MOD):
    """
    Chế độ cũ (Y/N). heightRate cố định = 1.3.
    Giữ nguyên để không phá vỡ các luồng gọi cũ.
    """
    if chedocamyn is None:
        return
    if str(chedocamyn).lower() != 'y':
        return
    if not os.path.exists(CamXa_MOD):
        return

    with open(CamXa_MOD, 'rb') as f:
        content = f.read()
    content = _strip_existing_camxa_track(content)
    block = _build_track_block(1.3)
    if b'</Action>' in content:
        content = content.replace(b'</Action>', block, 1)
    with open(CamXa_MOD, 'wb') as f:
        f.write(content)


def CamXaFile(CamXa_MOD, percent):
    """
    Mod cam xa theo phần trăm (1..100).
      heightRate = 1.0 + percent * 0.05
      -  1% -> 1.05
      - 35% -> 2.75
      -100% -> 6.00
    Dán CHUẨN form <Track>/<Event> vào ngay trước </Action> đầu tiên của
    file junglemark.xml (hoặc bất kỳ xml Ages nào truyền vào).
    """
    try:
        pct = int(percent)
    except (TypeError, ValueError):
        return
    if pct <= 0 or pct > 100:
        return
    if not os.path.exists(CamXa_MOD):
        return

    height_rate = 1.0 + pct * 0.05  # 1% = +0.05

    with open(CamXa_MOD, 'rb') as f:
        content = f.read()

    # Nếu file đã bị mod cam xa trước đó -> gỡ ra để dán lại đúng %
    content = _strip_existing_camxa_track(content)

    block = _build_track_block(height_rate)
    if b'</Action>' in content:
        content = content.replace(b'</Action>', block, 1)

    with open(CamXa_MOD, 'wb') as f:
        f.write(content)
