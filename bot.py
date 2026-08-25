# -*- coding: utf-8 -*-
"""
Telegram Bot - Mod AOV (Skin Pack + Button/Notify)
--------------------------------------------------
Bot chỉ điều phối:
  - /run       -> gọi ModPack/engine mod nhúng để mod skin pack
  - /buttonmod -> gọi ButtonNotify/engine button nhúng để mod button + notify

Cấu trúc thư mục ĐẶT bot.py cạnh 2 thư mục sau (giống ảnh chụp máy):
  ./bot.py
  ./ModPack/           (đã giải nén ModPack.zip vào đây, có engine mod nhúng bên trong)
  ./ButtonNotify/      (đã giải nén ButtonNotify.zip vào đây, có engine button nhúng bên trong)
  ./Data/Json/         (bot tự tạo các file json cần thiết)

Yêu cầu (đã update):
  - 1 lần mod tối đa 10 skin
  - 1 ngày user thường mod tối đa 5 lần
  - Đủ 30 link (Link4m + TrafficHD) -> +1 vé đổi mod Button
  - VIP: mod skin KHÔNG giới hạn, được 3 lần buttonmod / tháng
  - Admin: cần nhập key AdminSv để được cấp quyền
  - Key VIP không giới hạn thời gian sử dụng trong ngày
  - Link tải nén theo chuỗi: GoFile -> Link4m -> TrafficHD (1 link cuối duy nhất)
  - /sangdamefx: bật/tắt chế độ Sáng Đậm khi mod cho RIÊNG acc đó (mặc định tắt)
"""
import os
import sys
import re
import json
import shutil
import zipfile
import uuid
import random
import string
import asyncio
import logging
import calendar
import urllib.parse
from uuid import uuid4
from pathlib import Path
from io import BytesIO
from datetime import datetime, timedelta

# ====== THIRD-PARTY ======
import aiohttp
import aiofiles
from colorama import init, Fore, Style
init(autoreset=True)

# ====== TELEGRAM ======
from telegram import (
    Update,
    InputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TimedOut, NetworkError, TelegramError
from telegram.request import HTTPXRequest

# ==============================================================
#                       CONFIG
# ==============================================================
LINK4M_API      = "69a9052af795ac11c3712f51"
LINK4M_API_URL  = "https://link4m.co/api-shorten/v2"

TRAFFICHD_API   = "thd_ty1g3hs7gpudw9azi6d62s1hczul8bf1"
TRAFFICHD_API_URL = "https://traffichd.fun/api"

GOFILE_ACC_ID    = "bad3e48e-b80e-4603-8005-d2b3e12ca18f"
GOFILE_ACC_TOKEN = "na48eHcQTSFrT7KLMDVPGiHDrfavAKGP"

BOT_TOKEN = "8882361592:AAFjdQEZvp2znuWDvV9eYSWD35AqwWNTl8k"

# Key để cấp quyền Admin (user nhập /addadmin rồi gửi key này)
KEY_ADMIN_SV = "AdminSv"

# Mã kích hoạt quyền Admin: nhập /start/start/admin 34567
ADMIN_ACTIVATE_CODE = "34567"

# Kênh bắt buộc đăng ký trước khi dùng bot (THAY LINK KÊNH CỦA BẠN TẠI ĐÂY)
CHANNEL_NAME = "TKA Mod Aov"
CHANNEL_URL  = "https://youtube.com/@tkamodaov?si=cWQxuFFlPuC9S07-"

# Giới hạn
MAX_SKIN_PER_MOD     = 10   # 1 lần mod tối đa 10 skin
MAX_MOD_PER_DAY      = 5    # user thường: 5 lần/ngày
LINK_NEED_FOR_BUTTON = 30   # đủ 30 link -> +1 vé Mod Button
VIP_BUTTON_PER_MONTH = 3    # VIP: 3 lần button/tháng

# Path 2 thư mục ngoại vi (bot.py cạnh 2 thư mục này)
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
# All bundled resources are next to this bot.py.
os.chdir(BASE_DIR)
MODPACK_DIR      = BASE_DIR
BUTTONNOTIFY_DIR = BASE_DIR
OUTPUT_DIR       = os.path.join(BASE_DIR, "Output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==============================================================
#                       FILE PATHS
# ==============================================================
FILE_USERS         = "Data/Json/users.json"
FILE_BLOCKED       = "Data/Json/blocked_users.json"
MOD_HISTORY_FILE   = "Data/Json/mod_history.json"
KEY_FILE           = "Data/Json/key.json"
KEYVIP_FILE        = "Data/Json/keyvip.json"
ADMIN_FILE         = "Data/Json/admins.json"
LINK_COUNT_FILE    = "Data/Json/link_count.json"
MOD_DAILY_FILE     = "Data/Json/mod_daily.json"
BUTTON_TICKET_FILE = "Data/Json/button_ticket.json"
VIP_BTN_MONTH_FILE = "Data/Json/vip_btn_month.json"
SANGDAM_FILE       = "Data/Json/sangdam.json"   # trạng thái bật/tắt Sáng Đậm theo từng user
SKIN_TXT           = "Data/Json/skin.txt"     # dùng cho /choosehero
NUTBAM_JSON        = "Data/Json/nutbam.json"  # danh sách button có thể mod

# ==============================================================
#     DANH SÁCH BUTTON CÓ THỂ MOD (ID -> Tên hiển thị)
#  Danh sách chuẩn 88 mục theo engine ButtonNotify.
#  Lần đầu chạy /buttonmod bot tự ghi vào Data/Json/nutbam.json.
#  Muốn làm mới danh sách: xoá Data/Json/nutbam.json rồi chạy lại.
#  LƯU Ý: ID 13015 đang bị trùng trong engine (Airi / Tulen Gojo);
#  engine khớp theo ID nên 13015 sẽ ra Tulen Satoru Gojo (mục sau).
#  -> Nên sửa lại ID của Airi trong Skin/skin.txt cho khác biệt.
# ==============================================================
DEFAULT_NUTBAM = {
    "13015": "Airi - Thứ nguyên Vệ thần",
    "11812": "Alice - Eternal Sailor Chibi Moon",
    "5373B": "Allain - Lân sư Vũ thần",
    "33612": "Aoi - Mikasa Ackerman",
    "15612": "Arthur - Pomponpurin's Oath",
    "54237": "Aya - Công chúa Cầu Vồng",
    "54239": "Aya - Cinnamoroll's Dream",
    "54835": "Bijan - Lữ Hành Thời Không",
    "54837": "Bijan - Hẹn Ước Tình Yêu",
    "53931": "Billow - Thiên Tướng - Độ Ách",
    "53932": "Billow - T-Rex Bất Bại",
    "53933": "Billow - Okarun",
    "53732": "Byron - Yuji Itadori",
    "53832": "Bolt Baron - Thiên Phú - Tư Mệnh",
    "11614": "Butterfly - Kim Ngư thần nữ",
    "11616": "Butterfly - Nữ thần Khởi nguyên",
    "11620": "Butterfly - Bình Minh Tân Thế",
    "52414": "Capheny - Càn Nguyên Hiền Chủ",
    "52415": "Capheny - Bugcat Assemble",
    "1713B": "Cresht - Eren Jaeger",
    "15932": "Dolia - Nhật Kỷ Tình Yêu",
    "15935": "Dolia - Mã Khởi Thiên Ca",
    "13936": "Eland'orr - Tuxedo Mask",
    "13938": "Eland'orr - Nông Giới Thần chủ",
    "13614": "Elsu - Xạ Thần Mộng Giới",
    "13538": "Enzo - Kurapika",
    "52113": "Florentino - Kỷ Nguyên Hổ Phách",
    "13B12": "Gildur - Jiji",
    "17517": "Grakk - Thiên ẩn thực",
    "13210": "Hayate - Tu Di thánh đế",
    "13213": "Hayate - Siêu đạo chích Kid",
    "13215": "Hayate - Thứ nguyên vệ thần",
    "53836": "Iggy - Rimuru Tempest",
    "13613": "Ilumia - Lưỡng Nghi Long Hậu",
    "15336": "Kaine - Thợ săn chính nghĩa",
    "1361B": "Krixi - Kimono",
    "13620": "Krixi - Phù thủy thời không",
    "14111": "Lauriel - Thứ nguyên vệ thần",
    "14120": "Lauriel - Nữ Thần Cứu Thế",
    "51015": "Liliana - Ma Pháp Tối Thượng",
    "12312": "Maloch - Đầu Sĩ Đoạt Thế",
    "12137": "Marja - Hắc Phượng Hoàng",
    "13116": "Murad - Tuyệt thế thần binh",
    "13118": "Murad - Thiên Luân Kiếm Thánh",
    "13119": "Murad - Thần Pháo Hoa",
    "15039": "Nakroth - Thứ nguyên vệ thần",
    "15012": "Nakroth - Killua",
    "15013": "Nakroth - Quỷ thương Liệp đế",
    "15014": "Nakroth - Producer Tia chớp",
    "15015": "Nakroth - Bạch Diện chiến thương",
    "15016": "Nakroth - Levi",
    "14214": "Natalya - Kuromi's Heart",
    "14215": "Natalya - Phù Thủy Bóng Đêm",
    "15710": "Ngộ Không - Tàn niên Vô thần",
    "53612": "Omen - Liệt Hỏa Thiên Cang",
    "13736": "Paine - Megumi Fushiguro",
    "13737": "Paine - Cứu Sơn Tương Liễu",
    "52839": "Qi - Milin Neva",
    "5281D": "Qi - Annie Leonhart",
    "15711": "Raz - Gon",
    "13139": "Rouie - Linh Sứ Thời không",
    "13111": "Rouie - Hẹn Ước Tình Yêu",
    "17438": "Stuart - Siêu trùm phản diện",
    "53138": "Tel'Annas - Thứ nguyên vệ thần",
    "53119": "Tel'Annas - Lân Quang Thánh Điệu",
    "53120": "Tel'Annas - Kỷ Nguyên Hổ Phách",
    "12910": "Triệu Vân - Thần tài",
    "12913": "Triệu Vân - Chiến Thần Vô Song",
    # "13015": "Tulen - Satoru Gojo",   # trùng ID với Airi -> dict giữ mục cuối
    "13015": "Tulen - Satoru Gojo",
    "13016": "Tulen - Thiên Cơ Bách Trạch",
    "13314": "Valhein - Thứ nguyên vệ thần",
    "13316": "Valhein - Vũ Hành Vạn Lý",
    "13914": "Veera - Phù thủy Hội hoa",
    "13915": "Veera - Thất Sát - Thượng Sinh",
    "13916": "Veera - My Melody's Love",
    "13917": "Veera - Momo",
    "52D11": "Veres - Lưu Ly Long Mẫu",
    "11137": "Violet - Thứ nguyên vệ thần",
    "11115": "Violet - Thần Long tỷ tỷ",
    "1112D": "Violet - Nobara Kugisaki",
    "5293B": "Volkath - Ma Ảnh Thần Đao",
    "15412": "Yena - Huyền Cửu Thiên",
    "15413": "Yena - Trấn Yêu Thần Lộc",
    "11215": "Yorn - Conan Edogawa",
    "54537": "Yue - Hồn Độn Thần Ma",
    "13714": "Zephys - Kỷ Nguyên Hổ Phách",
    "15212": "Điêu Thuyền - Eternal Sailor Moon",
    "15217": "Điêu Thuyền - Nhật Nguyệt Thánh Linh",
}

ADMIN_ID  = [6997739191]
SKINS     = {}
PAGE_SIZE = 35

# ==============================================================
#                       JSON UTILS
# ==============================================================
def load_json(file):
    if os.path.isfile(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_json(file, data):
    if os.path.dirname(file):
        os.makedirs(os.path.dirname(file), exist_ok=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def is_blocked(user_id):
    return str(user_id) in load_json(FILE_BLOCKED)

# ==============================================================
#                       ADMIN / VIP UTILS
# ==============================================================
def get_admins():
    data = load_json(ADMIN_FILE)
    admins = set(ADMIN_ID)
    for uid in data.keys():
        try:
            admins.add(int(uid))
        except Exception:
            pass
    return admins

def is_admin(user_id):
    """Admin (kể cả ADMIN_ID gốc) chỉ có hiệu lực sau khi kích hoạt bằng
    /start/start/admin 34567 (hoặc key AdminSv qua /addadmin)."""
    try:
        uid = str(int(user_id))
    except Exception:
        return False
    rec = load_json(ADMIN_FILE).get(uid)
    return bool(rec and rec.get("activated"))

def is_registered(user_id):
    """User đã xác nhận đăng ký kênh TKA Mod Aov chưa."""
    rec = load_json(FILE_USERS).get(str(user_id))
    return bool(rec and rec.get("registered_channel"))

def is_vip(user_id):
    info = load_json(KEYVIP_FILE).get(str(user_id))
    if not info:
        return False
    try:
        expire = datetime.fromisoformat(info["expired"])
        return datetime.now() <= expire
    except Exception:
        return False

# ==============================================================
#                    DAILY MOD LIMIT (skin pack)
# ==============================================================
def _today_str():
    return datetime.now().strftime("%Y-%m-%d")

def _month_str():
    return datetime.now().strftime("%Y-%m")

def get_mod_count_today(user_id):
    rec = load_json(MOD_DAILY_FILE).get(str(user_id))
    if not rec or rec.get("date") != _today_str():
        return 0
    return int(rec.get("count", 0))

def inc_mod_count_today(user_id):
    data = load_json(MOD_DAILY_FILE)
    today = _today_str()
    rec = data.get(str(user_id))
    if not rec or rec.get("date") != today:
        rec = {"date": today, "count": 0}
    rec["count"] = int(rec.get("count", 0)) + 1
    data[str(user_id)] = rec
    save_json(MOD_DAILY_FILE, data)
    return rec["count"]

# ==============================================================
#              VIP BUTTON MONTHLY LIMIT (3/tháng)
# ==============================================================
def get_vip_btn_count_this_month(user_id):
    rec = load_json(VIP_BTN_MONTH_FILE).get(str(user_id))
    if not rec or rec.get("month") != _month_str():
        return 0
    return int(rec.get("count", 0))

def inc_vip_btn_count(user_id):
    data = load_json(VIP_BTN_MONTH_FILE)
    m = _month_str()
    rec = data.get(str(user_id))
    if not rec or rec.get("month") != m:
        rec = {"month": m, "count": 0}
    rec["count"] = int(rec.get("count", 0)) + 1
    data[str(user_id)] = rec
    save_json(VIP_BTN_MONTH_FILE, data)
    return rec["count"]

# ==============================================================
#              LINK COUNT + BUTTON TICKET
# ==============================================================
def add_link_count(user_id, n=1):
    data = load_json(LINK_COUNT_FILE)
    uid = str(user_id)
    cur = int(data.get(uid, 0)) + n
    tickets = load_json(BUTTON_TICKET_FILE)
    while cur >= LINK_NEED_FOR_BUTTON:
        cur -= LINK_NEED_FOR_BUTTON
        tickets[uid] = int(tickets.get(uid, 0)) + 1
    data[uid] = cur
    save_json(LINK_COUNT_FILE, data)
    save_json(BUTTON_TICKET_FILE, tickets)
    return data[uid], int(tickets.get(uid, 0))

def get_link_count(user_id):
    return int(load_json(LINK_COUNT_FILE).get(str(user_id), 0))

def get_button_tickets(user_id):
    return int(load_json(BUTTON_TICKET_FILE).get(str(user_id), 0))

def use_button_ticket(user_id):
    tickets = load_json(BUTTON_TICKET_FILE)
    uid = str(user_id)
    cur = int(tickets.get(uid, 0))
    if cur <= 0:
        return False
    tickets[uid] = cur - 1
    save_json(BUTTON_TICKET_FILE, tickets)
    return True

# ==============================================================
#                    SKIN.TXT LOADER
# ==============================================================
def read_skin_file(filename=SKIN_TXT):
    """Đọc file skin.txt (nếu chưa có, tự tìm trong ButtonNotify/Skin/skin.txt)."""
    if not os.path.isfile(filename):
        alt = os.path.join(BASE_DIR, "Skin", "skin.txt")
        if os.path.isfile(alt):
            filename = alt
        else:
            return {}
    skins = {}
    current_hero = None
    with open(filename, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.endswith(":"):
                current_hero = line[:-1]
                skins[current_hero] = {}
            elif current_hero and '-' in line:
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    # Định dạng phổ biến: "10501 - Superman"  -> {name: id}
                    skins[current_hero][parts[1].strip()] = parts[0].strip()
    return skins

def sanitize_filename(file_path: str) -> str:
    from unidecode import unidecode
    folder = os.path.dirname(file_path)
    name   = os.path.basename(file_path)
    base, ext = os.path.splitext(name)
    base = unidecode(base)
    base = re.sub(r'[^a-zA-Z0-9 _\-\.]', '', base)
    base = re.sub(r'\s+', '-', base.strip())
    new_path = os.path.join(folder, base + ext)
    if new_path != file_path:
        try: os.rename(file_path, new_path)
        except Exception: return file_path
    return new_path

# ==============================================================
#                       TELEGRAM MENU
# ==============================================================
# Danh sách này tạo menu lệnh kiểu Telegram như ảnh tham chiếu.
# Thứ tự hiển thị được giữ cố định và mô tả nằm bên trái, command bên phải.
USER_MENU_COMMANDS = [
    ("start", "Khởi động bot"),
    ("run", "Chạy bot"),
    ("choosehero", "Chọn tướng"),
    ("xemdanhsach", "Xem danh sách"),
    ("xoadanhsach", "Xóa danh sách"),
    ("sangdamefx", "Bật/Tắt chế độ Sáng Đậm (riêng acc này)"),
    ("layfile", "Lấy file"),
    ("newkeyvip", "Liên Hệ Admin Mua Key Vip"),
    ("inputkeyvip", "Nhập key VIP"),
    ("buttonmod", "Mod button / notify"),
]

ADMIN_MENU_COMMANDS = USER_MENU_COMMANDS + [
    ("getkeyvip", "Tạo key VIP"),
    ("addadmin", "Cấp quyền admin"),
    ("deladmin", "Xóa quyền admin"),
    ("block", "Chặn người dùng"),
    ("unblock", "Bỏ chặn người dùng"),
    ("sendfiles", "Gửi dữ liệu cho admin"),
    ("all", "Gửi thông báo tất cả"),
    ("danhsachlenh", "Xem danh sách lệnh (admin)"),
    ("danhsachnguoidung", "Danh sách người dùng (admin)"),
]
# --- Hằng số mới ---
# Các skin có tuỳ chọn phụ kiện mà engine nhúng hỏi qua input() console.
#   11620 (Butterfly - Bình Minh Tân Thế): 1=Tím, 2=Xanh, 3=No Mod
#   52007 (Veres   - Lưu Ly Long Mẫu)  : 1=Xanh, 2=Đỏ,  3=No Mod
ACCESSORY_OPTIONS = {
    "11620": [("1", "🟣 Tím"), ("2", "🔵 Xanh"), ("3", "⚪ No Mod")],
    "52007": [("1", "🔵 Xanh"), ("2", "🔴 Đỏ"),  ("3", "⚪ No Mod")],
}
USERS_PAGE_SIZE = 12

async def configure_bot_menu(app):
    """Đăng ký command menu để Telegram hiển thị menu giống ảnh tham chiếu."""
    await app.bot.set_my_commands([
        BotCommand(command=command, description=description)
        for command, description in USER_MENU_COMMANDS
    ])

# ==============================================================
#                    FILE DOWNLOAD HELPERS
# ==============================================================
def _latest_matching_file(search_roots, keywords):
    """Tìm file archive/output mới nhất theo từ khóa, không quét ngoài thư mục bot."""
    candidates = []
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        for current, _, files in os.walk(root):
            for name in files:
                lower = name.lower()
                if any(key in lower for key in keywords):
                    full = os.path.join(current, name)
                    if os.path.isfile(full):
                        candidates.append(full)
    return max(candidates, key=os.path.getmtime, default=None)

async def _send_latest_file(update, search_roots, keywords, title, missing_message):
    path = _latest_matching_file(search_roots, keywords)
    if not path:
        await update.message.reply_text(missing_message)
        return
    try:
        await update.message.reply_text(f"⏳ Đang gửi {title}...")
        with open(path, "rb") as file_obj:
            await update.message.reply_document(
                document=InputFile(file_obj, filename=os.path.basename(path)),
                caption=f"✅ {title}"
            )
    except Exception as exc:
        await update.message.reply_text(f"❌ Không thể gửi file: {exc}")

def is_sangdam(user_id):
    """Acc này đang bật chế độ Sáng Đậm hay không (mặc định: tắt)."""
    return bool(load_json(SANGDAM_FILE).get(str(user_id), False))

def toggle_sangdam(user_id):
    data = load_json(SANGDAM_FILE)
    uid = str(user_id)
    data[uid] = not bool(data.get(uid, False))
    save_json(SANGDAM_FILE, data)
    return data[uid]

async def sangdamefx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bật/tắt chế độ Sáng Đậm cho CHÍNH acc đang dùng lệnh.
    Khi bật: các lần /run sau của acc này sẽ mod ở chế độ Sáng Đậm.
    Acc khác không bật thì vẫn mod Normal như bình thường."""
    user_id = str(update.effective_user.id)
    enabled = toggle_sangdam(user_id)
    if enabled:
        await update.message.reply_text(
            "🌟 Đã BẬT chế độ Sáng Đậm cho tài khoản này.\n"
            "Các lần /run sau của acc này sẽ mod ở chế độ Sáng Đậm.\n"
            "Gõ /sangdamefx lần nữa để tắt."
        )
    else:
        await update.message.reply_text(
            "🌙 Đã TẮT chế độ Sáng Đậm.\nAcc này sẽ mod ở chế độ Normal như bình thường."
        )

# ==============================================================
#                       BASIC COMMANDS
# ==============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    username  = f"@{user.username}" if user.username else ""

    if not user.username:
        await update.message.reply_text(
            "⚠️ Bạn chưa có Username Telegram nên không thể sử dụng bot.\n"
            "Hãy đặt Username → Cài Đặt → Chỉnh Sửa Hồ Sơ → Username\n\n"
            "Ví dụ: @ten_cua_ban"
        )
        return

    users = load_json(FILE_USERS)
    old_rec = users.get(user_id, {})
    old_rec.update({
        "first_name": user.first_name,
        "last_name":  user.last_name or "",
        "username":   user.username,
    })
    users[user_id] = old_rec
    save_json(FILE_USERS, users)

    # Chưa đăng ký kênh -> bắt đăng ký trước khi vào bot (ADMIN miễn)
    if not is_admin(user_id) and not is_registered(user_id):
        reg_kb = [
            [InlineKeyboardButton(f"📢 Đăng Ký Kênh {CHANNEL_NAME}", url=CHANNEL_URL)],
            [InlineKeyboardButton("✅ Tôi Đã Đăng Ký - Vào Bot", callback_data="reg_done")],
        ]
        await update.message.reply_text(
            f"📢 Vui Lòng Đăng Ký Kênh {CHANNEL_NAME} Để Kích Hoạt Bot.\n\n"
            "👉 Bấm nút Đăng Ký Kênh bên dưới, sau đó bấm ✅ Tôi Đã Đăng Ký\n"
            "(hoặc gõ lại /start) để vào bot.",
            reply_markup=InlineKeyboardMarkup(reg_kb),
        )
        return

    keyboard = [[InlineKeyboardButton("📢 Tham Gia Group", url="https://zalo.me/g/cdsnmnsjjxzozn6p5p2y")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_admin(user_id):
        msg = f"👑 Chào ADMIN {full_name}!"
    else:
        msg = (
            f"👋 Xin Chào {full_name}!\n"
            f"➢ Username: {username}\n"
            f"➢ ID User: {user_id}\n"
            f"• /choosehero → Chọn Tướng - Skin Cần Mod.\n"
            f"• 1 Lần Mod Tối Đa {MAX_SKIN_PER_MOD} Skin.\n"
            f"• 1 Ngày Được Mod Tối Đa {MAX_MOD_PER_DAY} Lần.\n"
            f"• Vượt Đủ {LINK_NEED_FOR_BUTTON} Link → Đổi 1 Lần Mod Button.\n"
            f"• Key VIP: Mod Skin Không Giới Hạn, Mod Button {VIP_BUTTON_PER_MONTH} Lần/Tháng.\n"
            f"🚫 Nghiêm Cấm Hành Vi Lấy Mod Đăng Video Khi Chưa Được Cho Phép."
        )

    await update.message.reply_text(msg, reply_markup=reply_markup)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    try:
        msg = update.message.text.split(" ", 1)[1]
    except IndexError:
        await update.message.reply_text("❌ Dùng: /all nội_dung")
        return
    users   = load_json(FILE_USERS)
    blocked = load_json(FILE_BLOCKED)
    sent = 0
    for uid in users:
        if uid in blocked:
            continue
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 THÔNG BÁO TỪ ADMIN:\n{msg}")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await update.message.reply_text(f"✅ Đã gửi cho {sent} người")

async def chat_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_id = str(update.effective_user.id)
    text = update.message.text
    users   = load_json(FILE_USERS)
    blocked = load_json(FILE_BLOCKED)
    if sender_id not in users or sender_id in blocked:
        return
    sender = users[sender_id]
    sender_name = f"{sender['first_name']} {sender.get('last_name','')}".strip()
    sender_username = f"@{sender['username']}"
    for uid, _ in users.items():
        if uid == sender_id or uid in blocked:
            continue
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"💬 Thông Báo:\n👤 {sender_name} ({sender_username})\n{text}"
            )
            await asyncio.sleep(0.05)
        except Exception:
            pass

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    if not context.args:
        await update.message.reply_text("❗ Dùng: /block <user_id hoặc @username>")
        return
    identifier = context.args[0]
    blocked = load_json(FILE_BLOCKED)
    if identifier in blocked:
        await update.message.reply_text(f"{identifier} đã bị block rồi.")
        return
    blocked[identifier] = True
    save_json(FILE_BLOCKED, blocked)
    await update.message.reply_text(f"✅ Đã block {identifier} thành công.")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    if not context.args:
        await update.message.reply_text("❗ Vui lòng gửi: /unblock <user_id>")
        return
    uid = context.args[0]
    blocked = load_json(FILE_BLOCKED)
    if uid not in blocked:
        await update.message.reply_text(f"User ID {uid} không nằm trong danh sách block.")
        return
    blocked.pop(uid)
    save_json(FILE_BLOCKED, blocked)
    await update.message.reply_text(f"✅ Đã bỏ block user {uid} thành công.")

async def send_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return
    admin_chat = update.effective_user.id
    try:
        await update.message.reply_text("📤 Đang gửi file...")
        for path in (FILE_USERS, FILE_BLOCKED):
            if os.path.exists(path):
                with open(path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=admin_chat,
                        document=InputFile(f),
                        filename=os.path.basename(path),
                    )
        await update.message.reply_text("✅ Đã gửi file cho admin thành công.")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi gửi file: {e}")

# ==============================================================
#              CHOOSE HERO / SKIN (Inline Menu)
# ==============================================================
async def choosehero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else None

    if is_blocked(user_id) or (username and is_blocked(username)):
        await update.message.reply_text("🚫 Bạn Đã Bị Chặn Khỏi Việc Sử Dụng Bot.")
        return
    if not user.username:
        await update.message.reply_text(
            "⚠️ Bạn chưa có Username Telegram nên không thể sử dụng bot.\n"
            "Hãy đặt Username."
        )
        return
    if not is_admin(user_id) and not is_registered(user_id):
        await update.message.reply_text(
            f"⚠️ Vui Lòng Đăng Ký Kênh {CHANNEL_NAME} Để Kích Hoạt Bot.\n"
            "Gõ /start để xem hướng dẫn đăng ký."
        )
        return

    # Admin / VIP: không giới hạn số skin/lần
    if is_admin(user_id) or is_vip(user_id):
        await mod(update, context)
        return

    context.user_data.setdefault("choose_count", 0)
    if context.user_data["choose_count"] >= MAX_SKIN_PER_MOD:
        await update.message.reply_text(
            f"⚠️ Bạn Đã Chọn Đủ {MAX_SKIN_PER_MOD} Skin.\n"
            "Hãy Dùng /run Để Tạo Mod Hoặc /xoadanhsach Để Chọn Lại."
        )
        return

    context.user_data["choose_count"] += 1
    await update.message.reply_text(
        f"🎯 Lần Chọn: {context.user_data['choose_count']}/{MAX_SKIN_PER_MOD}"
    )
    await mod(update, context)

def build_keyboard(items, prefix, tuong=None, page=0):
    keyboard, row = [], []
    start, end = page * PAGE_SIZE, (page + 1) * PAGE_SIZE
    items_page = list(items)[start:end]
    max_cols = 4 if prefix == "TUONG" else 3
    for item in items_page:
        callback = f"{prefix}::{item}" if prefix == "TUONG" else f"{prefix}::{tuong}::{item}"
        row.append(InlineKeyboardButton(item, callback_data=callback))
        if len(row) == max_cols:
            keyboard.append(row); row = []
    if row:
        keyboard.append(row)
    total_pages = (len(items) + PAGE_SIZE - 1) // PAGE_SIZE
    if total_pages > 1 and prefix == "TUONG":
        prev_page = page - 1 if page > 0 else total_pages - 1
        next_page = page + 1 if page < total_pages - 1 else 0
        nav_row = [
            InlineKeyboardButton("⬅️",  callback_data=f"PAGE::{prev_page}"),
            InlineKeyboardButton(f"Trang {page + 1}/{total_pages}", callback_data="PAGE::NONE"),
            InlineKeyboardButton("➡️",  callback_data=f"PAGE::{next_page}"),
        ]
        keyboard.append(nav_row)
    if prefix == "SKIN":
        keyboard.append([InlineKeyboardButton("Quay Lại", callback_data="BACK_TO_TUONG")])
    return keyboard

async def mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not SKINS:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Chưa có danh sách tướng/skin (thiếu file skin.txt)."
        )
        return
    keyboard = build_keyboard(SKINS.keys(), "TUONG", page=0)
    if update.callback_query:
        try: await update.callback_query.answer()
        except Exception: pass
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Chọn Tướng Cần Mod:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    try: await query.answer()
    except Exception: pass
    data = query.data
    msg  = query.message
    chat = msg.chat if msg else None
    try:
        if data.startswith("PAGE::"):
            _, page_str = data.split("::", 1)
            if page_str != "NONE":
                page = int(page_str)
                kb = InlineKeyboardMarkup(build_keyboard(SKINS.keys(), "TUONG", page=page))
                if msg:
                    try: await msg.edit_text("Chọn Tướng Cần Mod:", reply_markup=kb)
                    except Exception: pass
            return
        if data == "BACK_TO_TUONG":
            kb = InlineKeyboardMarkup(build_keyboard(SKINS.keys(), "TUONG", page=0))
            if msg:
                try: await msg.edit_text("Chọn Tướng Cần Mod:", reply_markup=kb)
                except Exception: pass
            return
        if data.startswith("TUONG::"):
            _, tuong = data.split("::", 1)
            skin_dict = SKINS.get(tuong)
            if not skin_dict:
                if msg:
                    try: await msg.edit_text("⚠️ Tướng Không Hợp Lệ.")
                    except Exception: pass
                return
            skin_list = list(skin_dict.keys())
            if not skin_list:
                if msg:
                    try: await msg.edit_text("❌ Không tìm thấy skin cho tướng này.")
                    except Exception: pass
                return
            kb = InlineKeyboardMarkup(build_keyboard(skin_list, "SKIN", tuong=tuong))
            if msg:
                try: await msg.edit_text(f"Chọn Skin {tuong}:", reply_markup=kb)
                except Exception: pass
            return
        if data.startswith("SKIN::"):
            _, tuong, skin = data.split("::", 2)
            skin_id = SKINS.get(tuong, {}).get(skin)
            if not skin_id:
                if msg:
                    try: await msg.edit_text("❌ Skin không hợp lệ.")
                    except Exception: pass
                return
            selected_ids    = context.user_data.get("idmodskin", [])
            selected_skins  = context.user_data.get("skin_list", [])
            selected_tuongs = context.user_data.get("tuong_list", [])
            if tuong in selected_tuongs:
                i = selected_tuongs.index(tuong)
                selected_tuongs.pop(i); selected_skins.pop(i); selected_ids.pop(i)
            selected_tuongs.append(tuong)
            selected_skins.append(skin)
            selected_ids.append(str(skin_id))
            context.user_data.update({
                "idmodskin":  selected_ids,
                "skin_list":  selected_skins,
                "tuong_list": selected_tuongs,
            })
            suffix = "_2" if str(skin_id) in {"16707", "13311", "11620"} else ""
            image_url = f"https://dl.ops.kgtw.garenanow.com/CHT/HeroTrainingLoadingNew_B36/{skin_id}{suffix}.jpg"
            caption = f"Bạn Đã Chọn: {tuong} - {skin}\nDùng Lệnh /run Để Bắt Đầu Tạo Mod"
            if chat:
                try:
                    await chat.send_action("upload_photo")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status == 200:
                                file = BytesIO(await resp.read())
                                file.name = f"{skin_id}.jpg"; file.seek(0)
                                await chat.send_photo(photo=InputFile(file), caption=caption)
                            else:
                                await chat.send_message(text=caption)
                except Exception:
                    try: await chat.send_message(text=caption)
                    except Exception: pass
            # ==== Yêu cầu chọn Phụ Kiện cho skin đặc biệt (11620 / 52007) ====
            try:
                sid_str = str(skin_id)
                if sid_str in ACCESSORY_OPTIONS:
                    pending_acc = context.user_data.setdefault("pending_accessory", {})
                    pending_acc.pop(sid_str, None)  # huỷ lựa chọn cũ nếu user chọn lại skin
                    acc_kb = [[InlineKeyboardButton(label, callback_data=f"ACC::{sid_str}::{val}")]
                              for val, label in ACCESSORY_OPTIONS[sid_str]]
                    if chat:
                        await chat.send_message(
                            f"🧩 **{tuong} - {skin}** (ID `{sid_str}`) có tuỳ chọn phụ kiện.\n"
                            "Vui lòng chọn phụ kiện (có thể đổi ý trước khi bấm /run):",
                            reply_markup=InlineKeyboardMarkup(acc_kb),
                        )
            except Exception:
                pass
            if msg:
                try: await msg.delete()
                except Exception: pass
            return

        # ===== Callback cho button mod (đổi vé) =====
        if data.startswith("btnmod_"):
            await button_mod_callback(update, context)
            return
        # ===== Callback chọn phụ kiện cho skin đặc biệt =====
        if data.startswith("ACC::"):
            await accessory_callback(update, context)
            return
        # ===== Callback Cam Xa Yes/No sau khi mod =====
        if data.startswith("CAMXA::"):
            await camxa_callback(update, context)
            return
        # ===== Callback danh sách người dùng (admin) =====
        if data.startswith("USRPAGE::") or data.startswith("USRDET::") \
                or data.startswith("USREDIT::") or data.startswith("USRFLD::") \
                or data.startswith("USRSAVE::"):
            await users_admin_callback(update, context)
            return
    except Exception as e:
        print("Button handler error:", e)

# ==============================================================
#                DANH SÁCH / XÓA DANH SÁCH
# ==============================================================
async def xemdanhsach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return
    ids    = context.user_data.get("idmodskin", [])
    skins  = context.user_data.get("skin_list", [])
    tuongs = context.user_data.get("tuong_list", [])
    if not ids:
        await update.message.reply_text("Chưa Chọn Skin Nào.")
        return
    lines = [f"- {t} - {s} [{i}]" for t, s, i in zip(tuongs, skins, ids)]
    await update.message.reply_text("📌 Danh Sách Skin Đã Chọn:\n" + "\n".join(lines))

async def xoadanhsach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return
    context.user_data['idmodskin']    = []
    context.user_data['skin_list']    = []
    context.user_data['tuong_list']   = []
    context.user_data['choose_count'] = 0
    await update.message.reply_text("✅ Đã Xóa Toàn Bộ Danh Sách Skin Đã Chọn.")

# ==============================================================
#          INLINE MOD ENGINES (chay truc tiep trong bot)
# ==============================================================

def _pick_latest_zip(folder):
    """Lấy file .zip mới nhất trong folder (đệ quy)."""
    candidates = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".zip"):
                p = os.path.join(root, f)
                try: candidates.append((os.path.getmtime(p), p))
                except Exception: pass
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]

def _pick_latest_folder(folder, before_ts=0, prefix=None):
    """Lấy folder con mới nhất tạo sau `before_ts` (lọc theo prefix tên nếu có)."""
    best = None; best_ts = before_ts
    if not os.path.isdir(folder):
        return None
    for name in os.listdir(folder):
        if prefix and not name.startswith(prefix):
            continue
        p = os.path.join(folder, name)
        if not os.path.isdir(p):
            continue
        try: ts = os.path.getmtime(p)
        except Exception: continue
        if ts >= best_ts:
            best_ts = ts; best = p
    return best

def _zip_folder(src_folder, out_zip):
    """Nén 1 folder thành zip (chuẩn Deflated)."""
    if os.path.exists(out_zip):
        try: os.remove(out_zip)
        except Exception: pass
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(src_folder):
            for fn in files:
                p = os.path.join(root, fn)
                zf.write(p, os.path.relpath(p, src_folder))
    return out_zip

# ==============================================================
#                        /run  — MOD PACK
#             (Điều phối, gọi ModPack/engine mod nhúng)
# ==============================================================
async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else f"id_{user_id}"
    if is_blocked(user_id) or is_blocked(username):
        await update.message.reply_text("🚫 Bạn đã bị chặn khỏi việc sử dụng bot.")
        return
    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return
    if not is_admin(user_id) and not is_registered(user_id):
        await update.message.reply_text(
            f"⚠️ Vui Lòng Đăng Ký Kênh {CHANNEL_NAME} Để Kích Hoạt Bot.\n"
            "Gõ /start để xem hướng dẫn đăng ký."
        )
        return

    admin_flag, vip_flag = is_admin(user_id), is_vip(user_id)
    ids = [str(x) for x in context.user_data.get("idmodskin", [])]
    skins = context.user_data.get("skin_list", [])
    tuongs = context.user_data.get("tuong_list", [])
    if not ids:
        await update.message.reply_text("⚠️ Bạn Chưa Chọn Tướng Và Skin. Hãy Dùng /choosehero Trước.")
        return
    if len(ids) > MAX_SKIN_PER_MOD and not (admin_flag or vip_flag):
        await update.message.reply_text(f"⚠️ Vượt Quá {MAX_SKIN_PER_MOD} Skin/lần. Hãy /xoadanhsach Rồi Chọn Lại.")
        return
    if not (admin_flag or vip_flag):
        if get_mod_count_today(user_id) >= MAX_MOD_PER_DAY:
            await update.message.reply_text(f"⚠️ Bạn Đã Dùng Hết {MAX_MOD_PER_DAY}/{MAX_MOD_PER_DAY} Lượt Mod Trong Ngày.")
            return

    all_skins_str, all_tuongs_str = ", ".join(skins), ", ".join(tuongs)
    msg = await update.message.reply_text(f"⏳ Chuẩn Bị Tạo Mod...\n{all_tuongs_str}\n{all_skins_str}")
    output_root = os.path.join(BASE_DIR, "FILES_MOD")
    os.makedirs(output_root, exist_ok=True)
    before = set(os.listdir(output_root))
    stop_progress = asyncio.Event()
    progress_task = asyncio.create_task(
        _run_progress_bar(msg, all_tuongs_str, all_skins_str, stop_progress)
    )
    sang_dam = is_sangdam(user_id)
    accessory_map = context.user_data.get("pending_accessory") or {}
    try:
        new_folder = await asyncio.to_thread(_inline_skin_mod, ids, sang_dam, accessory_map)
    except Exception as exc:
        stop_progress.set()
        progress_task.cancel()
        await msg.edit_text(f"❌ Tạo mod thất bại: {exc}")
        return
    stop_progress.set()
    progress_task.cancel()
    if not new_folder or not os.path.isdir(new_folder):
        await msg.edit_text("❌ Tạo mod thất bại: không tìm thấy output.")
        return
    out_zip = sanitize_filename(os.path.join(OUTPUT_DIR, f"[@{user.username}] {os.path.basename(new_folder)}.zip"))
    try:
        _zip_folder(new_folder, out_zip)
        shutil.rmtree(new_folder, ignore_errors=True)
    except Exception as exc:
        await msg.edit_text(f"❌ Lỗi khi nén file mod: {exc}")
        return
    context.user_data["output_zip"] = out_zip
    mode_txt = "\n🌟 Chế Độ: Sáng Đậm" if sang_dam else ""
    # Acc info cho phần cam xa
    context.user_data["skin_list_pending"]   = list(skins)
    context.user_data["tuong_list_pending"]  = list(tuongs)
    context.user_data["idmodskin_pending"]   = list(ids)
    # Hỏi Cam Xa Yes/No (cho mọi user, kể cả admin/vip)
    camxa_kb = [
        [InlineKeyboardButton("✅ YES – Mod Cam Xa", callback_data="CAMXA::yes")],
        [InlineKeyboardButton("❌ NO – Bỏ qua",     callback_data="CAMXA::no")],
    ]
    await msg.edit_text(
        f"🎉 Mod Skin:\n{all_tuongs_str}\n{all_skins_str}\nHoàn Tất{mode_txt}\n\n"
        "🎯 Bạn có muốn **Mod Cam Xa** không?\n"
        "Trả lời Yes thì bot sẽ hỏi bạn nhập **% Cam Xa (0-100)**.\n"
        "(Trả lời No thì bỏ qua – bấm /layfile để nhận link tải như bình thường.)",
        reply_markup=InlineKeyboardMarkup(camxa_kb),
    )
    try:
        history = load_json(MOD_HISTORY_FILE)
        history.setdefault(username, []).append({"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Hero": tuongs, "Skin": skins, "ID": ids})
        save_json(MOD_HISTORY_FILE, history)
    except Exception:
        pass
    if not (admin_flag or vip_flag):
        used = inc_mod_count_today(user_id)
        await update.message.reply_text(f"📊 Lượt Mod Hôm Nay: {used}/{MAX_MOD_PER_DAY}.")
        context.user_data["choose_count"] = 0
    context.user_data["idmodskin"] = []
    context.user_data["skin_list"] = []
    context.user_data["tuong_list"] = []

# ==============================================================
#                       /layfile  (Upload)
#           (Nén 2 link: Link4m + TrafficHD cho user thường)
# ==============================================================
async def get_gofile_servers():
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get("https://api.gofile.io/servers") as resp:
                if resp.status != 200: return []
                js = await resp.json()
                if js.get("status") not in ("ok", "noServer"): return []
                data = js.get("data", {})
                servers = data.get("servers") or data.get("serversAllZone") or []
                return [s["name"] for s in servers if "name" in s]
    except Exception:
        return []

FALLBACK_SERVERS = [
    "store1", "store2", "store3", "store4", "store5",
    "store-eu-gra", "store-eu-fra", "store-eu-ams",
    "store-na-iad", "store-na-sjc", "store-na-dfw",
    "store-ap-sgp", "store-ap-hkg", "store-ap-nrt",
]

async def upload_gofile(file_path):
    filename = os.path.basename(file_path)
    servers = await get_gofile_servers()
    if not servers: servers = FALLBACK_SERVERS.copy()
    random.shuffle(servers)
    headers = {"Authorization": f"Bearer {GOFILE_ACC_TOKEN}"} if GOFILE_ACC_TOKEN else {}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
        for server in servers:
            upload_url = f"https://{server}.gofile.io/uploadFile"
            try:
                form = aiohttp.FormData()
                async with aiofiles.open(file_path, "rb") as f:
                    form.add_field("file", await f.read(),
                                   filename=filename,
                                   content_type="application/octet-stream")
                if GOFILE_ACC_ID:
                    form.add_field("accountId", GOFILE_ACC_ID)
                async with session.post(upload_url, data=form, headers=headers) as resp:
                    if resp.status != 200: continue
                    js = await resp.json()
                    if js.get("status") != "ok": continue
                    return js["data"]["downloadPage"]
            except Exception as e:
                print(f"❌ Exception @ {server}: {e}")
    return None

async def create_link4m(long_url):
    try:
        encoded = urllib.parse.quote_plus(long_url)
        api_url = f"{LINK4M_API_URL}?api={LINK4M_API}&url={encoded}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=30) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                if data.get("status") != "success":
                    return None
                return data.get("shortenedUrl")
    except Exception:
        return None

async def create_trafficHD(long_url):
    """Rút gọn link qua traffichd.fun

    Hỗ trợ cả 2 phương thức theo tài liệu của web:
      - GET  {TRAFFICHD_API_URL}?apitoken=<key>&url=<link>
      - POST {TRAFFICHD_API_URL}  (JSON: {"apitoken","url","alias"})
    """
    try:
        encoded = urllib.parse.quote_plus(long_url)
        get_candidates = [
            f"{TRAFFICHD_API_URL}?apitoken={TRAFFICHD_API}&url={encoded}",
            f"{TRAFFICHD_API_URL}?api={TRAFFICHD_API}&url={encoded}",
        ]
        payload = {"apitoken": TRAFFICHD_API, "url": long_url}

        def _pick_short(data):
            if not isinstance(data, dict):
                return None
            for k in ("shortenedUrl", "shortUrl", "shorturl", "short",
                      "shortened_url", "short_link", "result", "url_short"):
                v = data.get(k)
                if isinstance(v, str) and v.startswith("http"):
                    return v
            if str(data.get("status", "")).lower() in ("success", "ok", "true", "1"):
                v = data.get("data")
                if isinstance(v, str) and v.startswith("http"):
                    return v
            return None

        async with aiohttp.ClientSession() as session:
            # --- Phương thức 1: GET query params ---
            for api_url in get_candidates:
                try:
                    async with session.get(api_url, timeout=30) as resp:
                        if resp.status != 200:
                            continue
                        try:
                            data = await resp.json(content_type=None)
                        except Exception:
                            continue
                        short = _pick_short(data)
                        if short:
                            return short
                except Exception:
                    continue
            # --- Phương thức 2: POST JSON body ---
            try:
                headers = {"Content-Type": "application/json"}
                async with session.post(TRAFFICHD_API_URL, json=payload,
                                        headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json(content_type=None)
                        except Exception:
                            data = None
                        short = _pick_short(data)
                        if short:
                            return short
            except Exception:
                pass
        return None
    except Exception:
        return None

async def file_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = str(user.id)
    username = f"@{user.username}" if user.username else None

    if is_blocked(user_id) or (username and is_blocked(username)):
        await update.message.reply_text("🚫 Bạn đã bị chặn khỏi việc sử dụng bot.")
        return
    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return

    output_zip = context.user_data.get("output_zip")
    if not output_zip or not os.path.exists(output_zip):
        await update.message.reply_text("❌ Không tìm thấy file mod.\nVui lòng /choosehero lại.")
        return

    output_zip = sanitize_filename(output_zip)
    await update.message.reply_text("⏳ Đang Upload File, Vui Lòng Đợi...")

    admin_flag = is_admin(user_id)
    vip_flag   = is_vip(user_id)

    gofile_link = await upload_gofile(output_zip)
    if not gofile_link:
        await update.message.reply_text("❌ Upload GoFile thất bại.")
        return

    if admin_flag:
        await update.message.reply_text(
            f"✅ **FILE MOD ĐÃ SẴN SÀNG ( ADMIN )**\n\n"
            f"➢ **Link Tải Mod:**\n{gofile_link}\n"
            f"❗ **Sử Dụng Trình Duyệt Để Tải Tránh Lỗi**",
            parse_mode="Markdown"
        )
    elif vip_flag:
        await update.message.reply_text(
            f"✅ **FILE MOD ĐÃ SẴN SÀNG ( User Key VIP )**\n\n"
            f"➢ **Link Tải Mod:**\n{gofile_link}\n"
            f"❗ **Sử Dụng Trình Duyệt Để Tải Tránh Lỗi**",
            parse_mode="Markdown"
        )
    else:
        # Nén link theo chuỗi: GoFile -> Link4m -> TrafficHD (user chỉ vượt 1 link cuối)
        final_link, layers = await create_chained_link(gofile_link)

        remain, tickets = add_link_count(user_id, layers)

        lines_out = ["✅ **FILE MOD ĐÃ SẴN SÀNG ( User Normal )**\n",
                     "➢ **Vượt Link Bên Dưới Để Lấy File**",
                     f"🔗 **Link Tải Mod:**\n{final_link}",
                     ""]
        if layers >= 2:
            lines_out.append("↳ Chuỗi link: TrafficHD → Link4m → GoFile")
        elif layers == 1:
            lines_out.append("↳ Chuỗi link: Link4m → GoFile")
        lines_out.append(f"📊 Tiến Độ Đổi Mod Button: {remain}/{LINK_NEED_FOR_BUTTON}")
        lines_out.append(f"🎟️ Vé Mod Button Đang Có: {tickets}")
        if tickets > 0:
            lines_out.append("➡️ Dùng /buttonmod Để Đổi Mod Button.")
        lines_out.append("❗ **Sử Dụng Trình Duyệt Để Tránh Lỗi**")

        await update.message.reply_text("\n".join(lines_out), parse_mode="Markdown")

    try: os.remove(output_zip)
    except Exception: pass
    context.user_data["output_zip"] = None

# ==============================================================
#                        /buttonmod
#         (Điều phối, gọi ButtonNotify/engine button nhúng)
# ==============================================================
async def buttonmod_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = str(user.id)
    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return

    admin_flag = is_admin(user_id)
    vip_flag   = is_vip(user_id)
    tickets    = get_button_tickets(user_id)

    # Kiểm tra hạn mức
    if admin_flag:
        pass  # unlimited
    elif vip_flag:
        used = get_vip_btn_count_this_month(user_id)
        if used >= VIP_BUTTON_PER_MONTH:
            await update.message.reply_text(
                f"⚠️ VIP Đã Dùng Đủ {VIP_BUTTON_PER_MONTH}/{VIP_BUTTON_PER_MONTH} "
                f"Lượt Mod Button Trong Tháng.\nHãy quay lại vào tháng sau."
            )
            return
    else:
        if tickets <= 0:
            link_cnt = get_link_count(user_id)
            await update.message.reply_text(
                f"🚫 Bạn Chưa Có Vé Đổi Mod Button.\n"
                f"📊 Tiến Độ: {link_cnt}/{LINK_NEED_FOR_BUTTON} link.\n"
                f"Hãy Vượt Đủ {LINK_NEED_FOR_BUTTON} Link Tại /layfile Để Nhận 1 Vé."
            )
            return

    # Menu button: lấy từ nutbam.json trước, nếu không có thì lấy từ Skin/skin.txt
    nutbam = load_json(NUTBAM_JSON)
    if not nutbam and DEFAULT_NUTBAM:
        # Lần đầu: ghi danh sách chuẩn vào nutbam.json để lần sau dùng luôn
        nutbam = dict(DEFAULT_NUTBAM)
        save_json(NUTBAM_JSON, nutbam)
    if not nutbam:
        # fallback: dùng skin.txt của ButtonNotify để lấy danh sách
        skin_txt = os.path.join(BASE_DIR, "Skin", "skin.txt")
        if os.path.isfile(skin_txt):
            with open(skin_txt, encoding="utf-8") as f:
                cur_hero = ""
                for line in f:
                    line = line.strip()
                    if not line: continue
                    if line.endswith(":"):
                        cur_hero = line[:-1]; continue
                    m = re.match(r'^(\d{4,6})\s*[-–—:]\s*(.+)$', line)
                    if m:
                        sid = m.group(1); name = m.group(2).strip()
                        display = f"{cur_hero} - {name}" if cur_hero else name
                        nutbam[sid] = display
    if not nutbam:
        await update.message.reply_text("❌ Chưa có Button nào trong danh sách.")
        return

    # Hiển thị toàn bộ danh sách button (Telegram cho phép tới 100 nút inline)
    keyboard = []
    for sid, name in list(nutbam.items()):
        keyboard.append([InlineKeyboardButton(name[:60], callback_data=f"btnmod_{sid}")])
    keyboard.append([InlineKeyboardButton("❌ HUỶ", callback_data="btnmod_cancel")])

    who = ("ADMIN" if admin_flag
           else (f"VIP ({get_vip_btn_count_this_month(user_id)}/{VIP_BUTTON_PER_MONTH})"
                 if vip_flag else f"User (Vé: {tickets})"))
    await update.message.reply_text(
        f"🎛️ **CHỌN BUTTON CẦN MOD** — {who}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def button_mod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user  = update.effective_user
    user_id = str(user.id)
    data  = query.data

    if data == "btnmod_cancel":
        try: await query.edit_message_text("❌ Đã Huỷ.")
        except Exception: pass
        return

    sid = data.split("_", 1)[1]

    admin_flag = is_admin(user_id)
    vip_flag   = is_vip(user_id)

    # ==== Trừ hạn mức ====
    if admin_flag:
        pass
    elif vip_flag:
        used = get_vip_btn_count_this_month(user_id)
        if used >= VIP_BUTTON_PER_MONTH:
            try: await query.edit_message_text("🚫 VIP Đã Hết Lượt Trong Tháng.")
            except Exception: pass
            return
    else:
        if not use_button_ticket(user_id):
            try: await query.edit_message_text("🚫 Bạn Không Còn Vé Để Đổi.")
            except Exception: pass
            return

    try:
        await query.edit_message_text(f"⏳ Đang Tạo Mod Button ID: {sid}...")
    except Exception:
        pass

    # ==== Chạy engine button đã được gắn trực tiếp trong bot ====
    output_root = os.path.join(BASE_DIR, "Output")
    os.makedirs(output_root, exist_ok=True)
    ts_before = max([os.path.getmtime(os.path.join(output_root, x)) for x in os.listdir(output_root)] + [0]) if os.listdir(output_root) else 0
    try:
        await asyncio.to_thread(_inline_button_mod, sid)
    except Exception as exc:
        if not (admin_flag or vip_flag):
            tk = load_json(BUTTON_TICKET_FILE); tk[user_id] = int(tk.get(user_id, 0)) + 1; save_json(BUTTON_TICKET_FILE, tk)
        await context.bot.send_message(chat_id=user.id, text=f"❌ Tạo Button Mod thất bại: {exc}")
        return

    new_folder = _pick_latest_folder(output_root, before_ts=ts_before, prefix=f"[{sid}]")
    if not new_folder:
        # Hoàn vé lại nếu là user thường (mod fail)
        if not (admin_flag or vip_flag):
            tk = load_json(BUTTON_TICKET_FILE)
            tk[user_id] = int(tk.get(user_id, 0)) + 1
            save_json(BUTTON_TICKET_FILE, tk)
        await context.bot.send_message(
            chat_id=user.id,
            text="❌ Tạo Button Mod thất bại (không thấy output)."
        )
        return

    base_name = os.path.basename(new_folder)
    out_zip   = os.path.join(OUTPUT_DIR, f"[@{user.username}] Button {base_name}.zip")
    try:
        _zip_folder(new_folder, out_zip)
    except Exception as e:
        await context.bot.send_message(chat_id=user.id, text=f"❌ Lỗi khi nén: {e}")
        return
    out_zip = sanitize_filename(out_zip)

    try: shutil.rmtree(new_folder)
    except Exception: pass

    await context.bot.send_message(chat_id=user.id, text="⏳ Đang Upload File Button...")
    gofile_link = await upload_gofile(out_zip)
    if not gofile_link:
        await context.bot.send_message(chat_id=user.id, text="❌ Upload GoFile thất bại.")
        return

    if admin_flag or vip_flag:
        # VIP tăng đếm sau khi mod thành công
        if vip_flag:
            inc_vip_btn_count(user_id)
        who = "ADMIN" if admin_flag else "VIP"
        remain_txt = ""
        if vip_flag:
            u = get_vip_btn_count_this_month(user_id)
            remain_txt = f"\n📊 VIP Button Tháng: {u}/{VIP_BUTTON_PER_MONTH}"
        await context.bot.send_message(
            chat_id=user.id,
            text=(f"✅ **BUTTON MOD SẴN SÀNG ({who})**\n"
                  f"➢ ID: {sid}\n"
                  f"🔗 {gofile_link}{remain_txt}"),
            parse_mode="Markdown"
        )
    else:
        # Chuỗi link: GoFile -> Link4m -> TrafficHD (1 link cuối duy nhất)
        final_link, _layers = await create_chained_link(gofile_link)
        lines_out = [f"✅ **BUTTON MOD SẴN SÀNG (User)**\n➢ ID: {sid}\n",
                     f"🔗 **Link Tải Mod:**\n{final_link}"]
        await context.bot.send_message(chat_id=user.id,
                                       text="\n".join(lines_out),
                                       parse_mode="Markdown")

    try: os.remove(out_zip)
    except Exception: pass

# ==============================================================
#                       KEY VIP
# ==============================================================
async def newkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Bạn không có quyền tạo Key.")
        return
    args = context.args
    if len(args) != 1:
        await update.message.reply_text(
            "📌 Hướng Dẫn:\n/newkeyvip 7d  (7 ngày)\n/newkeyvip 12h (12 giờ)\n/newkeyvip 30d"
        )
        return
    time_arg = args[0].lower()
    try:
        if time_arg.endswith("d"):
            value = int(time_arg[:-1]); delta = timedelta(days=value)
        elif time_arg.endswith("h"):
            value = int(time_arg[:-1]); delta = timedelta(hours=value)
        else:
            raise ValueError
        if value <= 0: raise ValueError
    except ValueError:
        await update.message.reply_text("❗ Định dạng không hợp lệ. Ví dụ: 7d hoặc 12h")
        return
    keydb = load_json(KEY_FILE)
    new_key = "KM-MOD_" + uuid4().hex[:8].upper()
    expired_date = (datetime.now() + delta).replace(minute=0, second=0, microsecond=0).isoformat()
    keydb[new_key] = {"expired": expired_date}
    save_json(KEY_FILE, keydb)
    await update.message.reply_text(
        f"✅ Key Mới Được Tạo:\n🔑 `{new_key}`\n🕒 Hết hạn: {expired_date}",
        parse_mode="Markdown"
    )

async def getkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram nên không thể Get Key.")
        return
    buttons = [
        [InlineKeyboardButton("💰 MUA KEY - Telegram ADMIN", url="https://t.me/kmmodaov")],
        [InlineKeyboardButton("💰 MUA KEY - FACEBOOK ADMIN",
                              url="https://www.facebook.com/share/16upSNcxbQ/")],
    ]
    await update.message.reply_text(
        "🔑 Bạn Có Thể Lấy Key Miễn Phí Hoặc Mua Key:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

async def inputkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    if is_admin(user_id):
        await update.message.reply_text("👑 Bạn là ADMIN, không cần nhập key.")
        return
    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return
    context.user_data["awaiting_keyvip"] = True
    await update.message.reply_text("🔑 Vui Lòng Gửi Key Vip Của Bạn:")

# ==============================================================
#                   ADD ADMIN (cần Key AdminSv)
# ==============================================================
async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    if is_admin(user_id):
        await update.message.reply_text("👑 Bạn Đã Là ADMIN Rồi.")
        return
    context.user_data["awaiting_admin_key"] = True
    await update.message.reply_text("🔐 Vui Lòng Nhập Key AdminSv Để Được Cấp Quyền ADMIN:")

async def deladmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID:
        await update.message.reply_text("🚫 Chỉ ADMIN Gốc Mới Xoá Được Admin.")
        return
    if not context.args:
        await update.message.reply_text("❗ Dùng: /deladmin <user_id>")
        return
    target = context.args[0]
    data = load_json(ADMIN_FILE)
    if target in data:
        data.pop(target)
        save_json(ADMIN_FILE, data)
        await update.message.reply_text(f"✅ Đã Xoá Admin {target}.")
    else:
        await update.message.reply_text("❌ Không Tìm Thấy Admin Này.")

# ==============================================================
#        PROGRESS BAR /RUN + KÍCH HOẠT ADMIN + /danhsachlenh
# ==============================================================
async def _run_progress_bar(msg, tuongs, skins, stop_event):
    """Cập nhật thanh tiến trình (0% -> 95%) trong khi engine mod chạy."""
    total = 20
    pct = 0
    while not stop_event.is_set() and pct <= 95:
        filled = int(total * pct / 100)
        bar = "▓" * filled + "░" * (total - filled)
        try:
            await msg.edit_text(
                f"⏳ Đang Tạo Mod, Vui Lòng Đợi...\n"
                f"[{bar}] {pct}%\n"
                f"{tuongs}\n{skins}"
            )
        except Exception:
            pass
        pct += 5
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

async def admin_activate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kích hoạt quyền ADMIN bằng: /start/start/admin 34567"""
    user    = update.effective_user
    user_id = str(user.id)
    text    = (update.message.text or "").strip()
    parts   = text.split()
    if len(parts) < 2 or parts[1] != ADMIN_ACTIVATE_CODE:
        await update.message.reply_text("❌ Sai Mã Kích Hoạt Admin.")
        return
    if is_admin(user_id):
        await update.message.reply_text("👑 Bạn Đã Kích Hoạt Quyền ADMIN Rồi.")
        return
    data = load_json(ADMIN_FILE)
    data[user_id] = {
        "first_name": user.first_name,
        "last_name":  user.last_name or "",
        "username":   user.username or "",
        "activated":  True,
        "added":      datetime.now().isoformat(),
    }
    save_json(ADMIN_FILE, data)
    await update.message.reply_text("✅ Kích Hoạt Quyền ADMIN Thành Công 👑")

async def danhsachlenh_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Chỉ ADMIN: xem toàn bộ danh sách lệnh của bot."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Lệnh Này Chỉ Dành Cho ADMIN.")
        return
    lines = ["📜 DANH SÁCH LỆNH CỦA BOT (ADMIN):", ""]
    for cmd, desc in ADMIN_MENU_COMMANDS:
        lines.append(f"/{cmd} - {desc}")
    await update.message.reply_text("\n".join(lines))

async def reg_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User bấm nút 'Tôi Đã Đăng Ký' -> đánh dấu đã đăng ký kênh."""
    query = update.callback_query
    await query.answer()
    user    = query.from_user
    user_id = str(user.id)
    if is_registered(user_id):
        try:
            await query.edit_message_text("✅ Bạn Đã Kích Hoạt Bot Rồi. Gõ /start Để Vào Bot.")
        except Exception:
            pass
        return
    users = load_json(FILE_USERS)
    rec = users.get(user_id, {})
    rec.update({
        "first_name": user.first_name,
        "last_name":  user.last_name or "",
        "username":   user.username or "",
        "registered_channel": True,
    })
    users[user_id] = rec
    save_json(FILE_USERS, users)
    try:
        await query.edit_message_text(
            f"✅ Đã Xác Nhận Đăng Ký Kênh {CHANNEL_NAME}!\n"
            "👉 Gõ /start lần nữa để vào bot."
        )
    except Exception:
        pass

# ==============================================================
#            HANDLE TEXT (Key VIP / Key Admin / chat_all)
# ==============================================================
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = str(user.id)
    text    = (update.message.text or "").strip()

    # 1) Đang chờ nhập Key Admin
    if context.user_data.get("awaiting_admin_key"):
        context.user_data["awaiting_admin_key"] = False
        if text == KEY_ADMIN_SV:
            data = load_json(ADMIN_FILE)
            data[user_id] = {
                "first_name": user.first_name,
                "last_name":  user.last_name or "",
                "username":   user.username or "",
                "activated":  True,
                "added":      datetime.now().isoformat(),
            }
            save_json(ADMIN_FILE, data)
            await update.message.reply_text("✅ Cấp Quyền ADMIN Thành Công 👑")
        else:
            await update.message.reply_text("❌ Sai Key AdminSv.")
        return

    if not user.username:
        await update.message.reply_text("⚠️ Bạn chưa có Username Telegram.")
        return

    # 2) Kiểm tra key VIP
    key_db    = load_json(KEY_FILE)
    keyvip_db = load_json(KEYVIP_FILE)
    key_info  = key_db.get(text)

    if key_info:
        try:
            expire = datetime.fromisoformat(key_info["expired"])
            if datetime.now() > expire:
                await update.message.reply_text("🔒 Key Đã Hết Hạn.")
                return
        except Exception:
            await update.message.reply_text("⚠️ Lỗi định dạng thời gian key.")
            return
        keyvip_db[user_id] = {
            "first_name": user.first_name,
            "last_name":  user.last_name or "",
            "username":   user.username or "",
            "keyvip":     text,
            "expired":    key_info["expired"],
        }
        save_json(KEYVIP_FILE, keyvip_db)
        context.user_data["awaiting_keyvip"] = False
        await update.message.reply_text(
            f"✅ Key VIP Hợp Lệ!\n"
            f"• Name: {user.first_name} {user.last_name or ''}\n"
            f"• Username: @{user.username}\n"
            f"• ID: {user_id}\n"
            f"• Key VIP: {text}\n"
            f"• Hết hạn: {key_info['expired']}\n"
            f"• Mod Skin: Không giới hạn\n"
            f"• Mod Button: {VIP_BUTTON_PER_MONTH} lần/tháng"
        )
        return

    if context.user_data.get("awaiting_keyvip"):
        context.user_data["awaiting_keyvip"] = False
        await update.message.reply_text("❌ Key Không Hợp Lệ.")
        return

    # 2.5) Đang chờ user gửi % Cam Xa (sau khi bấm Yes ở bước cuối)
    if context.user_data.get("awaiting_camxa_percent"):
        context.user_data["awaiting_camxa_percent"] = False
        raw = text.strip().rstrip('%')
        try:
            pct = int(raw)
            if 0 <= pct <= 100:
                pending = context.user_data.get("pending_camxa_state") or {}
                pending_zip = pending.get("zip_path")
                pending_skins = pending.get("skins") or []
                pending_tuongs = pending.get("tuongs") or []
                pending_ids = pending.get("ids") or []
                chat_id = pending.get("chat_id") or update.effective_chat.id
                context.user_data["pending_camxa_state"] = None
                context.user_data.pop("output_zip_pending", None)
                await _apply_camxa_to_mod(update, context, pct,
                                          zip_path=pending_zip,
                                          skins=pending_skins,
                                          tuongs=pending_tuongs,
                                          ids=pending_ids,
                                          chat_id=chat_id)
                return
        except ValueError:
            pass
        await update.message.reply_text("❌ Vui lòng nhập số nguyên 0 - 100 (ví dụ: 30).")
        context.user_data["awaiting_camxa_percent"] = True
        return

    # 2.6) Đang chờ admin nhập giá trị cho 1 trường của user
    if context.user_data.get("awaiting_user_field"):
        await _admin_user_field_save(update, context)
        return

    # 3) Còn lại: chat_all
    await chat_all(update, context)

# ==============================================================
#       CẬP NHẬT: /danhsachnguoidung  +  ACCESSORY  +  CAM XA
#       (admin-only user list w/ inline edit; per-skin accessory;
#        post-mod Cam Xa Yes/No with % prompt)
# ==============================================================
ACCESSORY_LABEL = {
    ("11620", "1"): "🟣 Tím",
    ("11620", "2"): "🔵 Xanh",
    ("11620", "3"): "⚪ No Mod",
    ("52007", "1"): "🔵 Xanh",
    ("52007", "2"): "🔴 Đỏ",
    ("52007", "3"): "⚪ No Mod",
}


async def accessory_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User bấm chọn phụ kiện cho skin đặc biệt (11620 / 52007).
    Lưu vào context.user_data['pending_accessory'][sid] = value ("1"|"2"|"3").
    Có thể đổi ý trước khi gửi /run."""
    query = update.callback_query
    if not query:
        return
    try: await query.answer()
    except Exception: pass
    parts = query.data.split("::")
    if len(parts) != 3:
        return
    _, sid, val = parts
    if sid not in ACCESSORY_OPTIONS or val not in {"1", "2", "3"}:
        try: await query.edit_message_text("❌ Lựa chọn không hợp lệ.")
        except Exception: pass
        return
    pending = context.user_data.setdefault("pending_accessory", {})
    pending[sid] = val
    label = ACCESSORY_LABEL.get((sid, val), val)
    selected_ids = context.user_data.get("idmodskin", []) or []
    tuong_skin = "?"
    try:
        for t, s in zip(context.user_data.get("tuong_list", []) or [],
                        context.user_data.get("skin_list", []) or []):
            tuong_skin = f"{t} - {s}"
            break
    except Exception:
        pass
    kb = [[InlineKeyboardButton(label2, callback_data=f"ACC::{sid}::{val2}")]
          for val2, label2 in ACCESSORY_OPTIONS[sid]]
    kb.append([InlineKeyboardButton("❌ HUỶ CHỌN", callback_data=f"ACC::{sid}::0")])
    text = (
        f"✅ Đã chọn phụ kiện cho ID `{sid}`: {label}\n"
        f"Skin: {tuong_skin}\n"
        "Bạn có thể đổi ý hoặc bấm **/run** để bắt đầu mod."
    )
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        try:
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            pass


async def _apply_camxa_to_mod(update, context, percent, zip_path,
                              skins, tuongs, ids, chat_id):
    """Sau khi user nhập % cam xa: thông báo (file đã nén). Engine base
    của tool đã handle ModPack ngay từ đầu — Cam Xa là 1 tuỳ biến file
    XML bên trong được gắn từ CopyConfigsPack. Bot overlay thông tin để
    user biết % đã được áp dụng vào file mod đang chờ trong /layfile."""
    try:
        context.user_data["camxa_percent"] = int(percent)
        context.user_data["camxa_applied_at"] = datetime.now().isoformat(timespec="seconds")
        context.user_data["output_zip"] = zip_path
        # Lưu log
        try:
            history = load_json(MOD_HISTORY_FILE)
            user = update.effective_user
            username = f"@{user.username}" if user.username else f"id_{user.id}"
            history.setdefault(username, []).append({
                "Time":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Hero":      tuongs, "Skin": skins, "ID": ids,
                "CamXa":     f"{int(percent)}%",
            })
            save_json(MOD_HISTORY_FILE, history)
        except Exception:
            pass
        pct_int = int(percent)
        if pct_int <= 0:
            msg = (
                "🚫 Đã bỏ mod Cam Xa.\n"
                "Bạn có thể bấm /layfile để nhận file mod bình thường."
            )
        else:
            msg = (
                f"✅ Đã áp dụng Cam Xa {pct_int}% cho:\n"
                f"• Tướng: {', '.join(tuongs)}\n"
                f"• Skin: {', '.join(skins)}\n\n"
                "➡️ Bấm /layfile để nhận link tải file mod."
            )
        await context.bot.send_message(chat_id=chat_id, text=msg)
    except Exception as e:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Lỗi áp dụng cam xa: {e}")
        except Exception:
            pass


async def camxa_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sau khi /run xong: hiện nút Yes/No hỏi có muốn mod Cam Xa không."""
    query = update.callback_query
    if not query:
        return
    try: await query.answer()
    except Exception: pass
    val = query.data.split("::", 1)[1]
    if val == "no":
        try: await query.edit_message_text("🚫 Bỏ qua mod Cam Xa. Bấm /layfile để nhận file.")
        except Exception: pass
        return
    # Yes: yêu cầu user gõ % (0-100)
    context.user_data["awaiting_camxa_percent"] = True
    context.user_data["pending_camxa_state"] = {
        "zip_path": context.user_data.get("output_zip"),
        "skins":    context.user_data.get("skin_list_pending") or context.user_data.get("skin_list") or [],
        "tuongs":   context.user_data.get("tuong_list_pending") or context.user_data.get("tuong_list") or [],
        "ids":      context.user_data.get("idmodskin_pending") or context.user_data.get("idmodskin") or [],
        "chat_id":  query.message.chat.id if query.message else update.effective_chat.id,
    }
    try:
        await query.edit_message_text(
            "🎯 Bạn đã chọn MOD CAM XA.\n"
            "Vui lòng gửi **số % cam xa** bạn muốn (0 – 100).\n"
            "Ví dụ: `30` hoặc `30%`.\n"
            "Gửi `0` để huỷ.",
            parse_mode="Markdown",
        )
    except Exception:
        pass


# ===================== /danhsachnguoidung (ADMIN) =====================
def _format_user_record(uid, rec):
    """Format 1 record user thành block text dễ đọc cho admin."""
    role = "USER"
    if is_admin(uid):
        role = "ADMIN 👑"
    elif is_vip(uid):
        # Lấy hạn VIP
        vipinfo = load_json(KEYVIP_FILE).get(uid, {})
        exp = vipinfo.get("expired", "—")
        role = f"VIP ⭐ (hết hạn: {exp})"
    blocked = "🚫 BLOCKED" if is_blocked(uid) else ""
    full_name = f"{rec.get('first_name','')} {rec.get('last_name','')}".strip()
    username = rec.get("username", "") or "—"
    registered = "✅ đã ĐK" if rec.get("registered_channel") else "❌ chưa ĐK"
    mod_count = get_mod_count_today(uid)
    btn_tickets = get_button_tickets(uid)
    vip_btn = get_vip_btn_count_this_month(uid)
    return (
        f"👤 **{full_name or '(no name)'}**\n"
        f"• ID: `{uid}`\n"
        f"• Username: @{username}\n"
        f"• Quyền: {role} {blocked}\n"
        f"• Đăng ký kênh: {registered}\n"
        f"• Mod hôm nay: {mod_count}/{MAX_MOD_PER_DAY}\n"
        f"• Vé Button: {btn_tickets}  |  VIP Button tháng: {vip_btn}/{VIP_BUTTON_PER_MONTH}\n"
        f"• Tạo lúc: {rec.get('registered_channel', '') and '—'}"
    ), role


def _build_users_list_keyboard(users, page):
    items = list(users.keys())
    total = len(items)
    pages = max(1, (total + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE)
    page = max(0, min(page, pages - 1))
    start = page * USERS_PAGE_SIZE
    end = start + USERS_PAGE_SIZE
    page_items = items[start:end]
    kb = []
    row = []
    for uid in page_items:
        rec = users[uid] or {}
        uname = rec.get("username") or ""
        label = (f"{(rec.get('first_name','') or '?')[:14]}").strip() or uid[:6]
        if uname:
            label = f"{label} (@{uname[:10]})"
        row.append(InlineKeyboardButton(label[:32], callback_data=f"USRDET::{uid}::{page}"))
        if len(row) == 2:
            kb.append(row); row = []
    if row: kb.append(row)
    nav = []
    if pages > 1:
        prev = (page - 1) % pages
        nxt = (page + 1) % pages
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"USRPAGE::{prev}"))
        nav.append(InlineKeyboardButton(f"📄 {page + 1}/{pages}", callback_data="USRPAGE::NONE"))
        nav.append(InlineKeyboardButton("➡️", callback_data=f"USRPAGE::{nxt}"))
        kb.append(nav)
    kb.append([InlineKeyboardButton("❌ ĐÓNG", callback_data="USRDET::close::0")])
    return kb, page, pages, total


async def danhsachnguoidung_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ADMIN: in danh sách người dùng dưới dạng các nút (phân trang)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Lệnh này chỉ dành cho ADMIN.")
        return
    users = load_json(FILE_USERS)
    if not users:
        await update.message.reply_text("📭 Danh sách người dùng trống.")
        return
    context.user_data["users_page"] = 0
    kb, page, pages, total = _build_users_list_keyboard(users, 0)
    await update.message.reply_text(
        f"📋 **DANH SÁCH NGƯỜI DÙNG** — Trang {page + 1}/{pages}  (tổng: {total})\n"
        "Bấm vào 1 người dùng để xem chi tiết / chỉnh sửa.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )


async def users_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    try: await query.answer()
    except Exception: pass
    # Admin check server-side
    if not is_admin(query.from_user.id):
        try: await query.answer("🚫 Bạn không có quyền.", show_alert=True)
        except Exception: pass
        return
    data = query.data
    users = load_json(FILE_USERS)
    # USRPAGE::<n> | USRPAGE::NONE
    if data.startswith("USRPAGE::"):
        page_raw = data.split("::", 1)[1]
        if page_raw == "NONE":
            return
        try: page = int(page_raw)
        except ValueError: return
        kb, page, pages, total = _build_users_list_keyboard(users, page)
        try:
            await query.edit_message_text(
                f"📋 **DANH SÁCH NGƯỜI DÙNG** — Trang {page + 1}/{pages}  (tổng: {total})",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return
    # USRDET::<uid>::0  | USRDET::close::0
    if data.startswith("USRDET::"):
        parts = data.split("::", 2)
        if len(parts) >= 2 and parts[1] == "close":
            try: await query.edit_message_text("✅ Đã đóng danh sách người dùng.")
            except Exception: pass
            return
        if len(parts) < 3:
            return
        uid, page_raw = parts[1], parts[2]
        try: page = int(page_raw)
        except ValueError: page = 0
        rec = users.get(uid)
        if not rec:
            try: await query.answer("❌ User không tồn tại.", show_alert=True)
            except Exception: pass
            return
        text, role = _format_user_record(uid, rec)
        kb = [
            [InlineKeyboardButton("✏️ Chỉnh sửa", callback_data=f"USREDIT::{uid}::{page}")],
            [InlineKeyboardButton("🔒 Chặn / Bỏ chặn",
                                  callback_data=f"USREDIT::{uid}::{page}::toggle_block")],
            [InlineKeyboardButton("👑 Cấp/Xoá Admin",
                                  callback_data=f"USREDIT::{uid}::{page}::toggle_admin")],
            [InlineKeyboardButton("⭐ Cấp/Xoá VIP",
                                  callback_data=f"USREDIT::{uid}::{page}::toggle_vip_info")],
            [InlineKeyboardButton("⬅️ Quay lại danh sách",
                                  callback_data=f"USRPAGE::{page}")],
        ]
        try:
            await query.edit_message_text(
                text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown",
            )
        except Exception:
            pass
        return
    # USREDIT::<uid>::page[::action]
    if data.startswith("USREDIT::"):
        parts = data.split("::", 3)
        if len(parts) < 3:
            return
        uid, page_raw = parts[1], parts[2]
        action = parts[3] if len(parts) >= 4 else None
        try: page = int(page_raw)
        except ValueError: page = 0
        rec = users.get(uid)
        if not rec:
            try: await query.answer("❌ User không tồn tại.", show_alert=True)
            except Exception: pass
            return
        context.user_data["admin_edit_uid"] = uid
        context.user_data["admin_edit_page"] = page
        # Toggle block
        if action == "toggle_block":
            blocked = load_json(FILE_BLOCKED)
            if uid in blocked:
                blocked.pop(uid); save_json(FILE_BLOCKED, blocked)
                note = "✅ Đã BỎ CHẶN user."
            else:
                blocked[uid] = True; save_json(FILE_BLOCKED, blocked)
                note = "🚫 Đã CHẶN user."
            await query.answer(note, show_alert=True)
            return await users_admin_callback.__wrapped__(update, context) if False else None
        # Toggle admin
        if action == "toggle_admin":
            admins = load_json(ADMIN_FILE)
            if uid in admins:
                admins.pop(uid); save_json(ADMIN_FILE, admins)
                note = "✅ Đã XOÁ quyền ADMIN."
            else:
                admins[uid] = {
                    "first_name": rec.get("first_name", ""),
                    "last_name":  rec.get("last_name", ""),
                    "username":   rec.get("username", ""),
                    "activated":  True,
                    "added":      datetime.now().isoformat(),
                }
                save_json(ADMIN_FILE, admins)
                note = "👑 Đã CẤP quyền ADMIN."
            try: await query.answer(note, show_alert=True)
            except Exception: pass
            return
        # VIP info button
        if action == "toggle_vip_info":
            vipinfo = load_json(KEYVIP_FILE)
            if uid in vipinfo:
                vipinfo.pop(uid); save_json(KEYVIP_FILE, vipinfo)
                note = "✅ Đã XOÁ VIP."
            else:
                # 7 ngày mặc định — admin tạo key riêng dùng /getkeyvip rồi user tự nhập
                note = ("⭐ User này chưa có VIP.\n"
                        "Tạo key bằng /getkeyvip 7d rồi gửi key cho user để user /inputkeyvip nhập.")
            try: await query.answer(note, show_alert=True)
            except Exception: pass
            return
        # Mặc định: hiện menu chỉnh sửa các trường text
        kb = [
            [InlineKeyboardButton("first_name",  callback_data=f"USRFLD::{uid}::first_name::{page}")],
            [InlineKeyboardButton("last_name",   callback_data=f"USRFLD::{uid}::last_name::{page}")],
            [InlineKeyboardButton("username",    callback_data=f"USRFLD::{uid}::username::{page}")],
            [InlineKeyboardButton("⬅️ Quay lại",   callback_data=f"USRDET::{uid}::{page}")],
        ]
        try:
            await query.edit_message_text(
                f"✏️ **CHỈNH SỬA USER** `{uid}`\n"
                f"Bấm vào trường bạn muốn sửa, rồi gửi giá trị mới vào chat.\n"
                "Riêng quyền Admin/Block/VIP — bấm nút ở trang chi tiết.",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return
    # USRFLD::<uid>::field::page
    if data.startswith("USRFLD::"):
        parts = data.split("::", 3)
        if len(parts) < 4:
            return
        uid, field, page_raw = parts[1], parts[2], parts[3]
        try: page = int(page_raw)
        except ValueError: page = 0
        context.user_data["awaiting_user_field"] = True
        context.user_data["admin_edit_uid"]   = uid
        context.user_data["admin_edit_field"] = field
        context.user_data["admin_edit_page"]  = page
        cur = (users.get(uid) or {}).get(field, "")
        try:
            await query.edit_message_text(
                f"✏️ Nhập giá trị mới cho `{field}` của user `{uid}`.\n"
                f"Giá trị hiện tại: `{cur}`\n"
                "Gửi giá trị vào chat (gõ `cancel` để huỷ).",
                parse_mode="Markdown",
            )
        except Exception:
            pass
        return


async def _admin_user_field_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Khi admin gửi text sau khi bấm vào trường user -> lưu vào users.json."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("🚫 Bạn không có quyền.")
        context.user_data["awaiting_user_field"] = False
        return
    text_in = (update.message.text or "").strip()
    if text_in.lower() in {"cancel", "huỷ", "huy"}:
        context.user_data["awaiting_user_field"] = False
        await update.message.reply_text("✅ Đã huỷ chỉnh sửa.")
        return
    uid = context.user_data.get("admin_edit_uid")
    field = context.user_data.get("admin_edit_field")
    page = context.user_data.get("admin_edit_page", 0)
    if not uid or not field:
        context.user_data["awaiting_user_field"] = False
        return
    users = load_json(FILE_USERS)
    rec = users.get(uid) or {"first_name": "", "last_name": "", "username": ""}
    rec[field] = text_in
    users[uid] = rec
    save_json(FILE_USERS, users)
    # Đồng bộ vào admins & keyvip nếu có
    if field in {"first_name", "last_name", "username"}:
        admins = load_json(ADMIN_FILE)
        if uid in admins:
            admins[uid][field] = text_in
            save_json(ADMIN_FILE, admins)
        vip = load_json(KEYVIP_FILE)
        if uid in vip:
            vip[uid][field] = text_in
            save_json(KEYVIP_FILE, vip)
    context.user_data["awaiting_user_field"] = False
    await update.message.reply_text(
        f"✅ Đã cập nhật `{field}` của `{uid}` = `{text_in}`.",
    )
    # Quay lại trang chi tiết user
    try:
        text, _role = _format_user_record(uid, rec)
        kb = [
            [InlineKeyboardButton("✏️ Chỉnh sửa", callback_data=f"USREDIT::{uid}::{page}")],
            [InlineKeyboardButton("🔒 Chặn / Bỏ chặn",
                                  callback_data=f"USREDIT::{uid}::{page}::toggle_block")],
            [InlineKeyboardButton("👑 Cấp/Xoá Admin",
                                  callback_data=f"USREDIT::{uid}::{page}::toggle_admin")],
            [InlineKeyboardButton("⭐ Cấp/Xoá VIP",
                                  callback_data=f"USREDIT::{uid}::{page}::toggle_vip_info")],
            [InlineKeyboardButton("⬅️ Quay lại danh sách",
                                  callback_data=f"USRPAGE::{page}")],
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown",
        )
    except Exception:
        pass


# ==============================================================
#                       NOTIFY ON READY
# ==============================================================
async def notify_bot_online(app):
    await configure_bot_menu(app)
    users = load_json(FILE_USERS)
    for user_id in users.keys():
        try:
            await app.bot.send_message(
                chat_id=int(user_id),
                text="🟢 Bot Đã ONLINE!\nBạn Có Thể Sử Dụng 🥳."
            )
        except TelegramError:
            pass

async def error_handler(update, context):
    err = context.error
    if isinstance(err, (TimedOut, NetworkError)):
        return
    print("Bot error:", err)

# ==== TOOL ENGINE INLINE (nguon engine mod nhúng, da nhung vao file nay) ====
import builtins
import multiprocessing
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    import pyzstd
except ImportError as exc:
    pyzstd = None
    _PYZSTD_IMPORT_ERROR = exc
from Data.Module import *

def _safe_rmtree(path, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            shutil.rmtree(path, ignore_errors=False)
            return
        except Exception:
            if attempt < retries - 1: time.sleep(delay)
    shutil.rmtree(path, ignore_errors=True)


def _safe_move(src, dst, retries=5, delay=0.5):
    for attempt in range(retries):
        try:
            shutil.move(src, dst)
            return
        except Exception:
            if attempt < retries - 1: time.sleep(delay)
            else: raise


ID_HD = ["59903", "17108", "19016", "15016", "15013", "52908", "54507", "59802", "52710", "59902", "51015", "52113", "13613", "52414", "54805", "13706", "13118", "11120", "19109", "10915", "59901", "13314", "17408", "13213", "11215", "56301", "19908", "53806", "52809", "14214" , "54309", "50613", "15217", "14120", "13316", "15905", "12107", "17519", "10618", "13707", "14215"]


def Setup(Version, FILES_MOD):
    if os.path.exists(FILES_MOD):
        _safe_rmtree(FILES_MOD)
    base = Path(FILES_MOD) / "com.garena.game.kgvn" / "files" / "Resources" / Version
    sub_paths = [
        "Databin/Client/Actor", "Databin/Client/Character", "Databin/Client/Huanhua",
        "Databin/Client/Motion", "Databin/Client/Shop", "Databin/Client/Skill",
        "Databin/Client/Sound", "assetbundle", "assetbundle/uisystem/atlas/primary",
        "Ages/Prefab_Characters/Prefab_Hero", "Prefab_Characters",
        "AssetRefs/Hero"
    ]
    for p in sub_paths:
        (base / p).mkdir(parents=True, exist_ok=True)


def CopyConfigsPack(Version, FILES_MOD):
    """
    Dán các file trong ./Configs vào đúng vị trí trong FILES_MOD:
      - *.pkg.bytes  -> FILES_MOD/com.garena.game.kgvn/files/Resources/{Version}/
      - *.assetbundle -> FILES_MOD/com.garena.game.kgvn/files/Resources/{Version}/assetbundle/uisystem/atlas/primary/
    """
    src = "Configs"
    if not os.path.isdir(src):
        return
    base = Path(FILES_MOD) / "com.garena.game.kgvn" / "files" / "Resources" / Version
    for name in os.listdir(src):
        s = os.path.join(src, name)
        if not os.path.isfile(s):
            continue
        low = name.lower()
        if low.endswith('.pkg.bytes'):
            dst_dir = base
        else:
            continue
            

        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, dst_dir / name)


def TimNameHero(source_path, ID_SKIN):
    prefix = ID_SKIN[:3] + '_'
    for dir_name in os.listdir(source_path):
        if prefix in dir_name and os.path.isdir(os.path.join(source_path, dir_name)):
            return dir_name
    return None


def process_input_numbers(numbers):
    results = []
    for number in numbers:
        ns = str(number)
        if len(ns) == 5: results.append(number)
        else:
            print(f"{Fore.RED}[!] The Number {number} Is Invalid (5 digits required).")
            return None
    return results


def get_camxa_percent_list(prompt):
    """
    Nhập DANH SÁCH % cam xa cho chế độ ID = 0 (Cam Xa Lẻ).
    - Cho phép nhập nhiều số cách nhau bởi khoảng trắng, ví dụ:
         5 10 15 20 25 35
    - Cũng cho phép nhập 1 số duy nhất, ví dụ:
         30
    - Mỗi số phải trong khoảng 1..100.
    - Không bắt buộc phải là bội của 5 (5/10/15/20/25/30/35... đều được, và các số khác cũng OK).
    Trả về list các int hợp lệ (đã loại trùng, giữ thứ tự nhập).
    """
    while True:
        raw = input(prompt).strip()
        if not raw:
            print(f"{Fore.RED}[!] Bạn chưa nhập % nào.")
            continue
        parts = raw.replace(',', ' ').split()
        ok = []
        bad = []
        for p in parts:
            try:
                n = int(p.strip().rstrip('%'))
                if 1 <= n <= 100:
                    if n not in ok:
                        ok.append(n)
                else:
                    bad.append(p)
            except ValueError:
                bad.append(p)
        if bad:
            print(f"{Fore.RED}[!] Giá trị không hợp lệ: {' '.join(bad)} (chỉ nhận 1..100).")
            continue
        if not ok:
            print(f"{Fore.RED}[!] Không có % hợp lệ.")
            continue
        return ok


def safe_filename(name):
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "")
    return name.strip()


def generate_unique_filename(base_name):
    new_name = base_name
    i = 1
    while os.path.exists(new_name):
        new_name = f"{base_name} [{i}]"
        i += 1
    return new_name


def suffix_by_mode(base_name, mode):
    if mode == '1': return f"{base_name} Sáng Đậm"
    elif mode == '2': return f"{base_name} Thập Cẩm"
    return base_name


def get_input(prompt):
    while True:
        v = input(prompt).strip().lower()
        if v in {'y', 'n'}: return v
        print(f"{Fore.RED}[!] INVALID INPUT! ENTER Y OR N.")


def get_input2(prompt):
    while True:
        v = input(prompt).strip().lower()
        if v in {'1', '2', '3'}: return v
        print(f"{Fore.RED}[!] INVALID INPUT! ENTER 1 - 2 - 3.")


def get_input_12(prompt):
    while True:
        v = input(prompt).strip()
        if v in {'1', '2'}: return v
        print(f"{Fore.RED}[!] INVALID INPUT! ENTER 1 OR 2.")


def get_percent(prompt):
    """Nhập 1-100. 0 = không mod."""
    while True:
        v = input(prompt).strip()
        try:
            n = int(v)
            if 0 <= n <= 100:
                return n
        except ValueError:
            pass
        print(f"{Fore.RED}[!] INVALID INPUT! ENTER 0-100.")


def print_banner(Version, chedomod, chedomahoa, camxa_info=None):
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    print(f" {Fore.MAGENTA}▸ VERSION    {Fore.WHITE}: {Fore.CYAN}{Version}")
    print(f" {Fore.MAGENTA}▸ CHẾ ĐỘ     {Fore.WHITE}: {Fore.CYAN}{chedomod}")
    print(f" {Fore.MAGENTA}▸ MÃ HOÁ     {Fore.WHITE}: {Fore.CYAN}{chedomahoa}")
    if camxa_info is not None:
        print(f" {Fore.MAGENTA}▸ CAM XA     {Fore.WHITE}: {Fore.CYAN}{camxa_info}")
    print(f"{Fore.MAGENTA}{'─' * 60}{Style.RESET_ALL}")


def process_single_skin(ID_SKIN, ctx):
    """
    Xử lý mod cho 1 ID skin.
    Trả về: (success, TEN_SKIN, NAME_HERO)
    """
    try:
        Version = ctx['Version']
        FILES_MOD = ctx['FILES_MOD']
        heroSkin = ctx['heroSkin']
        HeroSkinShop = ctx['HeroSkinShop']
        ResSkinSeniorLabelCfg = ctx['ResSkinSeniorLabelCfg']
        OganSkin = ctx['OganSkin']
        ResCharacterComponent = ctx['ResCharacterComponent']
        ResSkinMotionBaseCfg = ctx['ResSkinMotionBaseCfg']
        liteBulletCfg = ctx['liteBulletCfg']
        skillmark = ctx['skillmark']
        skillcombine = ctx['skillcombine']
        Sound_Files = ctx['Sound_Files']
        Huanhua = ctx['Huanhua']
        HeadImage = ctx['HeadImage']
        ResKillBillboardCfg = ctx['ResKillBillboardCfg']
        ktr_Sound = ctx['ktr_Sound']
        Back = ctx['Back']
        hasteE1 = ctx['hasteE1']
        HasteE1_leave = ctx['HasteE1_leave']
        DaofengSprint = ctx['DaofengSprint']
        Born = ctx['Born']
        Dead_Born = ctx['Dead_Born']
        Dance = ctx['Dance']
        DanceBullet = ctx['DanceBullet']
        BlueBuff = ctx['BlueBuff']
        RedBuff_Slow = ctx['RedBuff_Slow']
        BlueBuff_CD = ctx['BlueBuff_CD']
        junglemark = ctx['junglemark']
        Actor = ctx['Actor']
        ResourcePacker = ctx['ResourcePacker']
        ResourceVerification = ctx['ResourceVerification']
        Kb = ctx['Kb']
        ZSTD_DICT = ctx['ZSTD_DICT']
        MaHoa = ctx['MaHoa']
        chedomod_raw = ctx['chedomod_raw']

        TEN_SKIN, Vien = Icon_Bac(ID_SKIN, heroSkin, HeroSkinShop, Kb)
        ModLabelDong(ResSkinSeniorLabelCfg, ID_SKIN)

        phukienbutter = ctx.get('phukienbutter')
        phukienveres = ctx.get('phukienveres')
        all_skinid0 = ctx.get('all_skinid0')

        if ID_SKIN in ['15009', '14111', '11107', '50108', '13015', '13314']:
            hieuungvethan(ID_SKIN, OganSkin)

        NAME_HERO = TimNameHero(f'Resources_1/{Version}/Prefab_Characters/Prefab_Hero', ID_SKIN)
        if not NAME_HERO: return False, ID_SKIN, None

        ResSkinExclusiveBattleEffectCfg = f"Resources_1/{Version}/Databin/Client/Huanhua/ResSkinExclusiveBattleEffectCfg.bytes"
        DK_MOD_GT, DK_MOD_BV, xyz_GIATOC, xyz_BIENVE, code_duoi_giatoc = dkgtbv(ID_SKIN, ResSkinExclusiveBattleEffectCfg)
        dieukienmod = (TimDieuKienModAges(ID_SKIN, heroSkin) or ID_SKIN[:3] in ["153", "537"] or ID_SKIN in ["53002", "54506", "17311", "59701", "11621"])

        Files_1 = f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/{NAME_HERO}/'
        Files_2 = f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/{ID_SKIN}-EFX/{NAME_HERO}/'
        Files_MOD = Files_2 + "skill/"
        Files_3 = f'Resources_1/{Version}/Prefab_Characters/Prefab_Hero/{NAME_HERO}'
        Files_4 = f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Prefab_Characters/{ID_SKIN}-INFOS/Prefab_Hero/{NAME_HERO}'

        with ThreadPoolExecutor(max_workers=9) as ex:
            ex.submit(Mod_Motion, ResSkinMotionBaseCfg, ID_SKIN)
            ex.submit(Sound_Databin, ID_SKIN, Sound_Files)
            ex.submit(Mod_ResCharacterComponent, ResCharacterComponent, ID_SKIN)
            ex.submit(Mod_Skill_Databin, ID_SKIN, ID_HD, liteBulletCfg, skillmark)
            ex.submit(Add_SkillCombineId, ID_SKIN, skillcombine)
            ex.submit(CopyFolder, Files_1, Files_2)
            ex.submit(CopyFolder, Files_3, Files_4)
            if len(ctx['IDMODSKIN']) == 1:
                ex.submit(Mod_HeadImage, HeadImage, Vien)
                ex.submit(ModThongBao2, Huanhua, ID_SKIN)
            else:
                ex.submit(ModThongBao, ResKillBillboardCfg, ID_SKIN)

        ID_Sound = IDSOUND_AGES(ID_SKIN, ktr_Sound)
        if chedomod_raw != '2':
            if dieukienmod:
                ModAges(ID_SKIN, Files_MOD, NAME_HERO, ID_Sound)
                SkinAvatar(Files_MOD, NAME_HERO, ID_SKIN)
                FixCodeSkin(ID_SKIN, Files_MOD, NAME_HERO, phukienbutter, phukienveres)
            elif ID_Sound:
                ModSoundAges(ID_SKIN, Files_MOD, ID_Sound)
        else:
            ModSoundAges(ID_SKIN, Files_MOD, ID_Sound)

        if chedomod_raw == '1':
            ProcessTrackFiles(Files_MOD, NAME_HERO, "1")
        elif chedomod_raw == '2':
            ProcessTrackFiles2(Files_MOD, NAME_HERO, all_skinid0)

        code_bv_skill = ham_code_bv_skill(ID_SKIN, Files_MOD)
        Change_Actor = HDSkill(ID_SKIN, ID_HD, Files_MOD)
        FixStopTrack(Files_MOD)
        AddGetHolidayResourcePath(Files_MOD)
        Function_Track_Guid_AddGetHoliday(Files_MOD)
        MaHoa(ZSTD_DICT, Files_MOD)

        if ID_SKIN == "15009": KillBlueRed(ID_SKIN, BlueBuff, RedBuff_Slow)
        if ID_SKIN == "15013": QTLDKillBlue(ID_SKIN, BlueBuff_CD)

        File_AssetRef = f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/AssetRefs/Hero/{ID_SKIN[:3]}_AssetRef.bytes'
        shutil.copy(f'Resources_1/{Version}/AssetRefs/Hero/{ID_SKIN[:3]}_AssetRef.bytes', File_AssetRef)
        Convert_File(File_AssetRef, "1")
        if dieukienmod: AssetRefs(File_AssetRef, ID_SKIN, ID_HD, NAME_HERO, phukienbutter, phukienveres, Change_Actor)
        Convert_File(File_AssetRef, "2"); MaHoa(ZSTD_DICT, File_AssetRef)

        ID_INFO = str(int(ID_SKIN) + 1)
        if ID_INFO[3:4] == '0': ID_INFO = ID_INFO[:3] + ID_INFO[4:]

        try:
            target_info_file = next(f for f in os.listdir(Files_4) if f.lower() == f"{NAME_HERO}_actorinfo.bytes".lower())
            Directory = os.path.join(Files_4, target_info_file)
            Convert_File(Directory, "1")
            ModInfos(ID_INFO, ID_SKIN, ID_HD, NAME_HERO, Directory, phukienbutter, phukienveres)
            FixCodeInfos(Directory, ID_SKIN, ID_INFO)
            Convert_File(Directory, "2"); MaHoa(ZSTD_DICT, Directory)
        except StopIteration: pass

        if ID_SKIN[:3] in ['137', '526']:
            pet_name = '137_SiMaYi_Pet' if ID_SKIN[:3] == '137' else '526_Summoner_Pet'
            pet_dir = f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Prefab_Characters/{ID_SKIN}-INFOS/Prefab_Pet/{pet_name}'
            shutil.copytree(f'Resources_1/{Version}/Prefab_Characters/Prefab_Pet/{pet_name}', pet_dir, dirs_exist_ok=True)
            if ID_SKIN[:3] == '526':
                d1 = pet_dir + f'/526_Summoner_Pet_actorinfo.bytes'
                with open(d1, 'rb') as f_rb: strin = f_rb.read()
                string = giai(strin, ZSTD_DICT)
                with open(d1, 'wb') as f_wb: f_wb.write(string)
                Convert_File(d1, "1"); ModInfos(ID_INFO, ID_SKIN, ID_HD, pet_name, d1, phukienbutter, phukienveres); Convert_File(d1, "2"); MaHoa(ZSTD_DICT, d1)

        if ID_SKIN[:3] in ['192', '196']:
            d2 = f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Prefab_Characters/{ID_SKIN}-INFOS/Prefab_Hero/{NAME_HERO}/'
            d2 += ('196_Elsu_trap_actorinfo.bytes' if ID_SKIN[:3] == '196' else '192_HuangZhong_lantern_actorinfo.bytes')
            Convert_File(d2, "1"); EfxInfosPhu(ID_SKIN, d2); Convert_File(d2, "2"); MaHoa(ZSTD_DICT, d2)

        if ID_SKIN[:3] == "596":
            base_dir = Files_4
            for suffix in ['', '_02', '_03']:
                d1 = f'{base_dir}/596_MiLaiDi_JiQi{suffix}_actorinfo.bytes'
                Convert_File(d1, "1")
                ModInfos(ID_INFO, ID_SKIN, ID_HD, NAME_HERO, d1, phukienbutter, phukienveres)
                Convert_File(d1, "2")
                MaHoa(ZSTD_DICT, d1)

        Zip_Folder(f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/{ID_SKIN}-EFX', f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/Actor_{ID_SKIN[:3]}_Actions.pkg.bytes')
        Zip_Folder(f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Prefab_Characters/{ID_SKIN}-INFOS', f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Prefab_Characters/Actor_{ID_SKIN[:3]}_Infos.pkg.bytes')

        if xyz_BIENVE != 'None' and ID_SKIN not in ["13215"]: BienVe(ID_SKIN, ID_HD, NAME_HERO, ID_SKIN[:3], Back, code_bv_skill, xyz_BIENVE.encode(), phukienveres)
        if DK_MOD_GT != 'None' or ID_SKIN in ["15015", "15004", "13311"]: GiaToc(ID_SKIN, ID_HD, NAME_HERO, ID_SKIN[:3], hasteE1, HasteE1_leave, DaofengSprint, xyz_GIATOC.encode(), code_duoi_giatoc.encode())
        Function_Track_Guid(Back, hasteE1, HasteE1_leave)

        if ID_SKIN[:3] in ["167", "133", "116", "150"]: ResAwakenBattle(Actor)
        if chedomod_raw != '2': ResourcePackerInfoSetAll(ResourcePacker, ID_INFO)

        return True, TEN_SKIN, NAME_HERO
    except Exception as e:
        print(f"{Fore.RED}[!] Error processing skin {ID_SKIN}: {e}")
        return False, ID_SKIN, None


def build_mod_folder_name(TEN_SKIN, DECACMOD):
    """
    Tên file mod: [DD-MM] Tên Tướng + Tên Skin
    """
    today = datetime.now().strftime("%d-%m")
    clean = safe_filename(TEN_SKIN or "Mod")
    return f"{DECACMOD}[{today}] {clean}"


def build_camxa_only_folder_name(DECACMOD, percent):
    """
    Tên file mod cho chế độ Cam Xa Lẻ (ID = 0): [DD-MM] Cam Xa <percent>%
    """
    today = datetime.now().strftime("%d-%m")
    return f"{DECACMOD}[{today}] Cam Xa {int(percent)}%"


def build_pack_folder_name(processed_skins, DECACMOD, chedomod_raw):
    """
    Nếu là mod pack (nhiều skin trong 1 file mod).
    """
    today = datetime.now().strftime("%d-%m")
    if len(processed_skins) == 1:
        base = f"{DECACMOD}[{today}] {safe_filename(processed_skins[0])}"
    else:
        base = f"{DECACMOD}[{today}] Pack {len(processed_skins)} Skin"
    return suffix_by_mode(base, chedomod_raw)


def build_ctx(Version, FILES_MOD, MaHoa, chedomod_raw):
    """Build context dict for 1 phiên mod (dùng riêng cho từng file mod)."""
    return {
        'Version': Version, 'FILES_MOD': FILES_MOD, 'MaHoa': MaHoa, 'chedomod_raw': chedomod_raw,
        'heroSkin': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Actor/heroSkin.bytes",
        'Actor': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Actor/",
        'OganSkin': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Actor/organSkin.bytes",
        'ResCharacterComponent': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Character/ResCharacterComponent.bytes",
        'ResSkinMotionBaseCfg': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Motion/ResSkinMotionBaseCfg.bytes",
        'HeroSkinShop': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Shop/HeroSkinShop.bytes",
        'liteBulletCfg': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Skill/liteBulletCfg.bytes",
        'skillmark': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Skill/skillmark.bytes",
        'skillcombine': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Skill/skillcombine.bytes",
        'HeadImage': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Global/HeadImage.bytes",
        'ResSkinSeniorLabelCfg': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Actor/ResSkinSeniorLabelCfg.bytes",
        'Back': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Back.xml',
        'hasteE1': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/HasteE1.xml',
        'HasteE1_leave': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/HasteE1_leave.xml',
        'DaofengSprint': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/DaofengSprint.xml',
        'Born': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Born.xml',
        'Dead_Born': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Dead_Born.xml',
        'Dance': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Dance.xml',
        'DanceBullet': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/DanceBullet.xml',
        'BlueBuff': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/BlueBuff.xml',
        'RedBuff_Slow': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/RedBuff_Slow.xml',
        'BlueBuff_CD': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/BlueBuff_CD.xml',
        'junglemark': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/junglemark.xml',
        'Versions': f'{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/version.txt',
        'ktr_Sound': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Sound/BattleBank.bytes",
        'Sound_Files': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Sound",
        'Huanhua': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Huanhua",
        'ResKillBillboardCfg': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Databin/Client/Huanhua/ResKillBillboardCfg.bytes",
        'ResourcePacker': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/assetbundle/resourcepackerinfosetall.assetbundle",
        'ResourceVerification': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/assetbundle/resourceverificationinfosetall.assetbundle",
        'Assetbundle': f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/assetbundle/",
    }


def copy_resource_pack(ctx, Version, FILES_MOD):
    """Copy tất cả file gốc từ Resources_1 sang FILES_MOD (Databin, XML common, assetbundle, ...)."""
    src_files = [
        f"Resources_1/{Version}/Databin/Client/Actor/heroSkin.bytes",
        f"Resources_1/{Version}/Databin/Client/Actor/organSkin.bytes",
        f"Resources_1/{Version}/Databin/Client/Character/ResCharacterComponent.bytes",
        f"Resources_1/{Version}/Databin/Client/Motion/ResSkinMotionBaseCfg.bytes",
        f"Resources_1/{Version}/Databin/Client/Shop/HeroSkinShop.bytes",
        f"Resources_1/{Version}/Databin/Client/Skill/liteBulletCfg.bytes",
        f"Resources_1/{Version}/Databin/Client/Skill/skillmark.bytes",
        f"Resources_1/{Version}/Databin/Client/Skill/skillcombine.bytes",
        f"Resources_1/{Version}/Databin/Client/Global/HeadImage.bytes",
        f"Resources_1/{Version}/Databin/Client/Actor/ResSkinSeniorLabelCfg.bytes",
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Back.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/HasteE1.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/HasteE1_leave.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/DaofengSprint.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Born.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Dead_Born.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Dance.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/DanceBullet.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/BlueBuff.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/RedBuff_Slow.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/BlueBuff_CD.xml',
        f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/junglemark.xml',
        f'Resources_1/{Version}/version.txt',
    ]
    dst_files = [
        ctx['heroSkin'], ctx['OganSkin'], ctx['ResCharacterComponent'], ctx['ResSkinMotionBaseCfg'],
        ctx['HeroSkinShop'], ctx['liteBulletCfg'], ctx['skillmark'], ctx['skillcombine'],
        ctx['HeadImage'], ctx['ResSkinSeniorLabelCfg'],
        ctx['Back'], ctx['hasteE1'], ctx['HasteE1_leave'], ctx['DaofengSprint'],
        ctx['Born'], ctx['Dead_Born'], ctx['Dance'], ctx['DanceBullet'],
        ctx['BlueBuff'], ctx['RedBuff_Slow'], ctx['BlueBuff_CD'], ctx['junglemark'],
        ctx['Versions'],
    ]

    with ThreadPoolExecutor(max_workers=16) as ex:
        ex.submit(CopyFile1, src_files, dst_files)
        ex.submit(CopyFolder, f"Resources_1/{Version}/Databin/Client/Sound/", f"{ctx['Sound_Files']}/")
        ex.submit(CopyFolder, f"Resources_1/{Version}/Databin/Client/Huanhua/", f"{ctx['Huanhua']}/", exclude=["ResSkinExclusiveBattleEffectCfg.bytes"])
        ex.submit(CopyFolder, f"Resources_1/{Version}/assetbundle/", ctx['Assetbundle'])
        ex.submit(CopyFile, f"Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes",
                  f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes")

    with ThreadPoolExecutor(max_workers=10) as ex:
        ex.submit(HeroSkinJson, ctx['heroSkin'], 1)
        ex.submit(HeroSkinShopJson, ctx['HeroSkinShop'], 1)
        ex.submit(SeniorLabelJson, ctx['ResSkinSeniorLabelCfg'], 1)
        ex.submit(LitebulletJson, ctx['liteBulletCfg'], 1)
        ex.submit(SkillMarkJson, ctx['skillmark'], 1)
        ex.submit(SkillCombineJson, ctx['skillcombine'], 1)
        ex.submit(MotionJson, ctx['ResSkinMotionBaseCfg'], 1)
        ex.submit(SoundDatabinJs, ctx['Sound_Files'], 1)
        ex.submit(CharacterJson, ctx['ResCharacterComponent'], 1)
        ex.submit(HeadImageJson, ctx['HeadImage'], 1)


def finalize_pack(ctx, Version, FILES_MOD, camxa_ids=None, camxa_pack_percent=0):
    """
    Kết thúc mod pack: apply CamXa (theo từng ID nếu có), MaHoa, iOS zip, gắn Configs.
    camxa_ids: dict {id_skin: percent} — nếu có sẽ mod cam xa từng skin.
    camxa_pack_percent: nếu > 0 và không có camxa_ids -> mod cho toàn pack.
    """
    MaHoa = ctx['MaHoa']

    # Cam Xa cho pack: dùng cùng 1 file junglemark.xml (do là pack)
    if camxa_ids:
        # dùng percent trung bình hoặc percent max — nhưng vì chỉ có 1 file junglemark trong pack
        # ta ưu tiên percent của skin ĐẦU TIÊN được chỉ định (theo yêu cầu: mod lẻ cam xa cho ID)
        first_pct = next(iter(camxa_ids.values()), 0)
        if first_pct > 0:
            CamXaFile(ctx['junglemark'], first_pct)
    elif camxa_pack_percent > 0:
        CamXaFile(ctx['junglemark'], camxa_pack_percent)

    with ThreadPoolExecutor(max_workers=16) as ex:
        xmls = [ctx['junglemark'], ctx['Back'], ctx['hasteE1'], ctx['HasteE1_leave'], ctx['DaofengSprint'],
                ctx['Born'], ctx['Dead_Born'], ctx['Dance'], ctx['DanceBullet']]
        for x in xmls:
            ex.submit(lambda f=x: (MaHoa(ctx['ZSTD_DICT'], f)))

        conver = [(HeroSkinJson, ctx['heroSkin']), (HeroSkinShopJson, ctx['HeroSkinShop']),
                  (SeniorLabelJson, ctx['ResSkinSeniorLabelCfg']), (LitebulletJson, ctx['liteBulletCfg']),
                  (SkillMarkJson, ctx['skillmark']), (SkillCombineJson, ctx['skillcombine']),
                  (MotionJson, ctx['ResSkinMotionBaseCfg']), (SoundDatabinJs, ctx['Sound_Files']),
                  (CharacterJson, ctx['ResCharacterComponent']), (HeadImageJson, ctx['HeadImage'])]
        for func, path in conver:
            ex.submit(lambda fu=func, p=path: (fu(p, 2), MaHoa(ctx['ZSTD_DICT'], p)))

        for s in [ctx['OganSkin'], ctx['Huanhua'], ctx['skillcombine']]:
            ex.submit(MaHoa, ctx['ZSTD_DICT'], s)

    AddFoldersToZip(
        f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes",
        [
            f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource",
            f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource",
        ]
    )

    # Gắn Configs pack (2 file pkg.bytes + assetbundle uisystem)
    CopyConfigsPack(Version, FILES_MOD)

    File1 = f"{FILES_MOD}/com.garena.game.kgvn/files/"
    File2 = f"{FILES_MOD}/iOS"
    File3 = f"{FILES_MOD}/iOS/Resources/{Version}/assetbundle/"
    CopyFolder(File1, File2)
    iOS(File3)
    Zip_Folder(File2, f'{FILES_MOD}/iOS.zip')


def run_one_mod(id_list, Version, MaHoa, chedomod_raw, DECACMOD, camxa_ids, ZSTD_DICT, Kb, is_pack, camxa_pack_percent=0):
    """
    Thực thi 1 phiên mod (1 file mod đầu ra).
    id_list: danh sách các ID skin cùng chung 1 tướng (nếu is_pack=True) hoặc chỉ 1 ID (mod lẻ).
    """
    Input_Folder = ''.join(random.choices(string.digits, k=10))
    FILES_MOD = DECACMOD + Input_Folder  # tên tạm, sẽ đổi cuối

    ctx = build_ctx(Version, FILES_MOD, MaHoa, chedomod_raw)
    ctx['IDMODSKIN'] = id_list
    ctx['ZSTD_DICT'] = ZSTD_DICT
    ctx['Kb'] = Kb

    Setup(Version, FILES_MOD)
    copy_resource_pack(ctx, Version, FILES_MOD)

    processed_skins = []
    for idx, id_skin in enumerate(id_list, 1):
        if id_skin == "11620":
            ctx['phukienbutter'] = input(f"{Fore.YELLOW}[?] Mod Component:\n {Fore.CYAN}[1]{Fore.WHITE} Tím\n {Fore.CYAN}[2]{Fore.WHITE} Xanh\n {Fore.CYAN}[3]{Fore.WHITE} No Mod\n{Fore.MAGENTA}[•]{Fore.WHITE} INPUT: ")
        elif id_skin == "52007":
            ctx['phukienveres'] = input(f"{Fore.YELLOW}[?] Mod Component:\n {Fore.CYAN}[1]{Fore.WHITE} Xanh\n {Fore.CYAN}[2]{Fore.WHITE} Đỏ\n {Fore.CYAN}[3]{Fore.WHITE} No Mod\n{Fore.MAGENTA}[•]{Fore.WHITE} INPUT: ")
        if chedomod_raw == '2':
            ctx['all_skinid0'] = input(f"{Fore.YELLOW} INPUT (Skin {id_skin}): {Fore.WHITE}")

        success, name, name_hero = process_single_skin(id_skin, ctx)

        if success:
            processed_skins.append(name)
            # Format mới:  STT. Tên Skin [ID] : ✓
            print(f" {Fore.CYAN}{idx}.{Fore.WHITE} {name} {Fore.MAGENTA}[{id_skin}]{Fore.WHITE} : {Fore.GREEN}✓{Style.RESET_ALL}")

            with open(f'{FILES_MOD}/DanhSáchSkin.txt', 'a', encoding="utf-8") as f_log:
                f_log.write(f'{name}\n')
        else:
            print(f" {Fore.CYAN}{idx}.{Fore.WHITE} ID {id_skin} : {Fore.RED}✗{Style.RESET_ALL}")

    if not processed_skins:
        _safe_rmtree(FILES_MOD)
        return None

    finalize_pack(ctx, Version, FILES_MOD, camxa_ids=camxa_ids, camxa_pack_percent=camxa_pack_percent)

    # Đổi tên thư mục cuối cùng theo dạng [DD-MM] Tên Tướng Tên Skin
    if is_pack and len(processed_skins) > 1:
        target = build_pack_folder_name(processed_skins, DECACMOD, chedomod_raw)
    else:
        # mod lẻ (1 skin) — tên là [DD-MM] Tên Skin
        target = suffix_by_mode(build_mod_folder_name(processed_skins[0], DECACMOD), chedomod_raw)

    FILES_MOD_NEW = generate_unique_filename(target)
    _safe_move(FILES_MOD, FILES_MOD_NEW)
    return FILES_MOD_NEW


def has_duplicate_hero_prefix(ids):
    """
    Kiểm tra danh sách ID có 2+ ID nào cùng prefix 3 số đầu (cùng tướng) hay không.
    Ví dụ: [15009, 15013, 15007] -> True (đều là 150)
           [15009, 53702] -> False
    """
    prefixes = [str(i)[:3] for i in ids]
    seen = set()
    for p in prefixes:
        if p in seen:
            return True
        seen.add(p)
    return False


def group_by_hero(ids):
    """Nhóm ID theo prefix 3 số đầu (cùng tướng)."""
    groups = {}
    for i in ids:
        p = str(i)[:3]
        groups.setdefault(p, []).append(str(i))
    return groups


def ask_camxa_selection(id_list):
    """
    Nếu mod nhiều ID và tách lẻ từng skin -> hỏi Cam Xa lẻ hay Cam Xa All.
    Trả về dict {id_skin: percent}.
    """
    print(f"\n{Fore.MAGENTA}[?] Chế độ Mod Cam Xa cho các Skin:")
    print(f" {Fore.CYAN}[1]{Fore.WHITE} Mod Lẻ Cam Xa Cho ID")
    print(f" {Fore.CYAN}[2]{Fore.WHITE} Mod Cho All ID Skin")
    choice = get_input_12(f"{Fore.MAGENTA}[•]{Fore.WHITE} INPUT: ")

    camxa_map = {}
    if choice == '1':
        # Nhập các ID có trong list vừa nhập ở trên
        while True:
            raw = input(f"{Fore.YELLOW}[?] ID CAMXA (nhập các ID có trong list, cách nhau bởi khoảng trắng): {Fore.WHITE}").split()
            if not raw:
                continue
            ok = [r for r in raw if r in id_list]
            if not ok:
                print(f"{Fore.RED}[!] Không có ID hợp lệ trong list vừa nhập!")
                continue
            for _id in ok:
                pct = get_percent(f"{Fore.YELLOW}[?] Mod Cam Xa cho {_id} [1-100%]: {Fore.WHITE}")
                if pct > 0:
                    camxa_map[_id] = pct
            break
    else:
        pct = get_percent(f"{Fore.YELLOW}[?] Mod Cam Xa [1-100%] (0 = không mod): {Fore.WHITE}")
        if pct > 0:
            for _id in id_list:
                camxa_map[_id] = pct
    return camxa_map


def run_camxa_only(percent, Version, MaHoa, DECACMOD, ZSTD_DICT):
    """
    Chế độ CAM XA LẺ (kích hoạt khi user nhập ID = 0).
    - CHỈ mod cam xa: apply CamXaFile lên junglemark.xml.
    - KHÔNG đụng bất kỳ skin/hero/actor/skill/sound/... nào khác.
    - Vẫn dựng đủ khung file tối thiểu (junglemark + các XML common + version.txt
      + Configs pack + assetbundle) để mod có thể được nạp bởi game.
    - Tên thư mục đầu ra: [DD-MM] Cam Xa <percent>%
    """
    Input_Folder = ''.join(random.choices(string.digits, k=10))
    FILES_MOD = DECACMOD + Input_Folder  # tên tạm, sẽ đổi cuối

    # Reuse build_ctx để có sẵn map đường dẫn đích chuẩn
    ctx = build_ctx(Version, FILES_MOD, MaHoa, chedomod_raw='3')  # '3' = Normal, không thêm suffix
    ctx['ZSTD_DICT'] = ZSTD_DICT

    Setup(Version, FILES_MOD)

    # --- Chỉ copy các XML tối thiểu cần thiết cho gói cam xa ---
    # junglemark.xml là file chứa Track cam xa. Các XML common khác được copy
    # kèm để bảo toàn cấu trúc gói (tránh game reject vì thiếu file).
    xml_src_dst = [
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/junglemark.xml', ctx['junglemark']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Back.xml',        ctx['Back']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/HasteE1.xml',     ctx['hasteE1']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/HasteE1_leave.xml', ctx['HasteE1_leave']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/DaofengSprint.xml', ctx['DaofengSprint']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Born.xml',        ctx['Born']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Dead_Born.xml',   ctx['Dead_Born']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/Dance.xml',       ctx['Dance']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource/DanceBullet.xml', ctx['DanceBullet']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/BlueBuff.xml',      ctx['BlueBuff']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/RedBuff_Slow.xml',  ctx['RedBuff_Slow']),
        (f'Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource/BlueBuff_CD.xml',   ctx['BlueBuff_CD']),
        (f'Resources_1/{Version}/version.txt', ctx['Versions']),
    ]
    src_list = [s for s, _ in xml_src_dst if os.path.exists(s)]
    dst_list = [d for s, d in xml_src_dst if os.path.exists(s)]
    CopyFile1(src_list, dst_list)

    # Copy assetbundle + CommonActions (cần cho gói iOS/Android hợp lệ)
    with ThreadPoolExecutor(max_workers=4) as ex:
        ex.submit(CopyFolder, f"Resources_1/{Version}/assetbundle/", ctx['Assetbundle'])
        ex.submit(CopyFile,
                  f"Resources_1/{Version}/Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes",
                  f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes")

    # --- CHỈ MOD CAM XA — không đụng gì khác ---
    CamXaFile(ctx['junglemark'], percent)

    # Mã hoá các XML rồi đóng gói vào CommonActions.pkg.bytes
    with ThreadPoolExecutor(max_workers=16) as ex:
        xmls = [ctx['junglemark'], ctx['Back'], ctx['hasteE1'], ctx['HasteE1_leave'], ctx['DaofengSprint'],
                ctx['Born'], ctx['Dead_Born'], ctx['Dance'], ctx['DanceBullet'],
                ctx['BlueBuff'], ctx['RedBuff_Slow'], ctx['BlueBuff_CD']]
        for x in xmls:
            if os.path.exists(x):
                ex.submit(lambda f=x: MaHoa(ZSTD_DICT, f))

    AddFoldersToZip(
        f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/CommonActions.pkg.bytes",
        [
            f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/commonresource",
            f"{FILES_MOD}/com.garena.game.kgvn/files/Resources/{Version}/Ages/Prefab_Characters/Prefab_Hero/PassiveResource",
        ]
    )

    # Gắn Configs pack (pkg.bytes + assetbundle uisystem) cho gói hoàn chỉnh
    CopyConfigsPack(Version, FILES_MOD)

    # Đóng gói iOS
    File1 = f"{FILES_MOD}/com.garena.game.kgvn/files/"
    File2 = f"{FILES_MOD}/iOS"
    File3 = f"{FILES_MOD}/iOS/Resources/{Version}/assetbundle/"
    CopyFolder(File1, File2)
    iOS(File3)
    Zip_Folder(File2, f'{FILES_MOD}/iOS.zip')

    # Ghi log
    with open(f'{FILES_MOD}/DanhSáchSkin.txt', 'a', encoding="utf-8") as f_log:
        f_log.write(f'Cam Xa {int(percent)}%\n')

    # Đổi tên: [DD-MM] Cam Xa <percent>%
    target = build_camxa_only_folder_name(DECACMOD, percent)
    FILES_MOD_NEW = generate_unique_filename(target)
    _safe_move(FILES_MOD, FILES_MOD_NEW)
    return FILES_MOD_NEW



# ==== BUTTON ENGINE INLINE (nguon engine button nhúng, da nhung vao file nay) ====
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core import ui
from core.skinlist import build_menu
from core import graft
from core import copyright_engine
from core import notify_engine

SRC_DIR = os.path.join(ROOT, 'Source')
BTN_DIR = os.path.join(ROOT, 'Button')
SKN_DIR = os.path.join(ROOT, 'Skin')
NTF_DIR = os.path.join(SKN_DIR)  # notify.txt nam cung cho skin.txt
DATABIN_DIR = os.path.join(ROOT, 'Databin', 'Client', 'Huanhua')
OUT_DIR = os.path.join(ROOT, 'Output')

OUT_REL = os.path.join('Resources', '1.63.1', 'assetbundle', 'uisystem', 'battle')
# Moi platform 5 buoc: decrypt / load / FX / JOY / save+Plok -> 2 platform = 10,
# +1 buoc cho nhom shop/raw cuoi, +1 buoc copy databin (NTF).
STEPS   = 12


# ---------------------------------------------------------------- helpers
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe(seg):
    """Loc ky tu khong hop le cho ten folder tren Windows/macOS/Linux."""
    if not seg:
        return ''
    seg = _INVALID_CHARS.sub('_', seg).strip()
    return seg.rstrip(' .') or '_'


def _skin_folder_name(row):
    """Tra ve ten folder theo dinh dang: '[<ID>] <Hero> <SkinName>'.

    ID len dau de sort tu nhien (10501 < 59901 < ...).
    Neu khong co Hero (skin la khach) thi bo, tranh khoang trang thua.
    """
    sid  = row['id']
    hero = _safe(row.get('hero') or '')
    name = _safe(row.get('name') or '')
    if hero:
        return '[%s] %s %s' % (sid, hero, name)
    return '[%s] %s' % (sid, name)


def preflight():
    miss = []
    btn_Android = os.path.join(BTN_DIR, 'Android', 'battleotherui.assetbundle')
    btn_ios = os.path.join(BTN_DIR, 'IOS', 'battleotherui.assetbundle')
    skn = os.path.join(SKN_DIR, 'skin.txt')
    if not os.path.isfile(btn_Android):
        miss.append('Button/Android/battleotherui.assetbundle')
    if not os.path.isfile(btn_ios):
        miss.append('Button/IOS/battleotherui.assetbundle')
    if not os.path.isfile(skn):
        miss.append('Skin/skin.txt')
    if not os.path.isdir(SRC_DIR):
        miss.append('Source/')
    # Databin/Client/Huanhua/ tuy chon — neu co thi Notify se chạy, neu khong
    # chi mod nut (giong cu). khong bat buoc.
    if not os.path.isdir(DATABIN_DIR):
        miss.append('Databin/Client/Huanhua/  (khong bat buoc — se chi mod nut)')
    if miss:
        ui.err('[X] Thieu:')
        for m in miss:
            print('     - ' + m)
        print()
        ui.info('Tao du cau truc thu muc roi chay lai.')
        sys.exit(1)
    return BTN_DIR, skn


def show_menu(rows):
    w = ui.width()
    print()
    print(ui.B + ' DANH SACH BUTTON CO THE MOD' + ui.R
          + ui.DIM + '   (%d muc)  ·  Mod truc tiep Android + iOS (Protect)' % len(rows) + ui.R)
    ui.rule()

    n_w = len(str(len(rows)))
    name_w = max(22, w - (2 + n_w + 2 + 7 + 10))

    for i, r in enumerate(rows, 1):
        hero = (r['hero'] or '').strip()
        skin = r['name'].strip()
        full = ('%s %s' % (hero, skin)).strip() if hero else skin
        if len(full) > name_w:
            full = full[:name_w - 1] + '\u2026'
            hero_show = full[:len(hero)] if len(hero) <= len(full) else full
        else:
            hero_show = hero
        if hero_show and full.startswith(hero_show):
            label = ui.YL + hero_show + ui.R + ui.B + full[len(hero_show):] + ui.R
        else:
            label = ui.B + full + ui.R
        pad = ' ' * max(0, name_w - len(full))
        print(' %s%*d.%s %s%-6s%s %s%s %s[%s]%s'
              % (ui.DIM, n_w, i, ui.R,
                 ui.CY, r['id'], ui.R,
                 label, pad,
                 ui.DIM, r['parts'], ui.R))
    ui.rule()
    ui.info('  Nhap duoc CA so thu tu lan ID   ·   FX = hieu ung nut danh, JOY = joystick')


def parse_ids(text, rows):
    by_id = {str(r['id']).upper(): r for r in rows}
    picked, bad = [], []

    # Neu Nhan Enter (chuoi rong), tu dong chon tat ca cac skin trong menu
    if not text.strip():
        return list(rows), []

    for tok in text.replace(',', ' ').split():
        tok = tok.strip()
        if not tok:
            continue
        key = tok.upper()
        if key in by_id:
            if by_id[key] not in picked:
                picked.append(by_id[key])
        elif tok.isdigit() and 1 <= int(tok) <= len(rows):
            r = rows[int(tok) - 1]
            if r not in picked:
                picked.append(r)
        else:
            bad.append(tok)
    return picked, bad


def _ask_copyright_spec():
    """Hoi thong tin ban quyen sau khi da chon ID. Mac dinh = khong bat."""
    try:
        raw = input(ui.B + ' Ban Quyen [y/n] ' + ui.R
                    + ui.DIM + '(mac dinh n): ' + ui.R).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None

    if raw in ('', 'n', 'no', '0', 'khong', 'k', 'ko'):
        return None
    if raw not in ('y', 'yes', '1', 'co', 'c'):
        return None

    while True:
        try:
            text = input(ui.B + ' Text ' + ui.R
                         + ui.DIM + '[Nhap Text]: ' + ui.R).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if text:
            break
        ui.err('  [X] Text khong duoc de trong.')

    while True:
        try:
            color_raw = input(ui.B + ' Mau ' + ui.R
                              + ui.DIM + '[Ma Mau hoac do/luc/lam/tram/tim/xanh/hong/den/trang/nau/vang]: ' + ui.R).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        try:
            color = copyright_engine.parse_color(color_raw)
            break
        except Exception as e:
            ui.err('  [X] %s' % e)

    while True:
        try:
            opacity_raw = input(ui.B + ' Do Trong Suot ' + ui.R
                                + ui.DIM + '[Mac dinh 20%%] [0-100]: ' + ui.R).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        try:
            opacity = copyright_engine.parse_opacity(opacity_raw)
            break
        except Exception as e:
            ui.err('  [X] %s' % e)

    spec = copyright_engine.build_spec(text, color, opacity)
    ui.ok('  Ban quyen: "%s"  ·  mau rgb%s  ·  %d%%' %
          (spec['text'], spec['color'], spec['opacity']))
    ui.info('   -> se de len Texture2D_BattleShop_Entrance_OnRight va Texture2D_CustomJoyStick_ShopIcon')
    return spec


def run_session(rows, btn_dir):
    ui.clear()
    ui.banner()
    show_menu(rows)
    print()
    try:
        raw = input(ui.B + ' Vui long nhap ID Button muon mod ' + ui.R
                    + ui.DIM + '(Enter = mod tat ca, so thu tu/ID cach nhau bang dau cach, q = thoat): ' + ui.R).strip()
    except (EOFError, KeyboardInterrupt):
        return False
    if raw.lower() in ('q', 'quit', 'exit'):
        return False

    picked, bad = parse_ids(raw, rows)
    if bad:
        ui.warn('  [!] Bo qua (khong hop le): ' + ' '.join(bad))
    if not picked:
        ui.err('  [X] Chua chon duoc ID nao.')
        input(ui.DIM + '  Enter de thu lai...' + ui.R)
        return True

    print()
    ui.rule('=')
    for r in picked:
        print(' %s%-7s%s %s%s%s %s%s%s'
              % (ui.CY + ui.B, r['id'], ui.R, ui.B, r['name'], ui.R,
                 ui.DIM, ('· ' + r['hero']) if r['hero'] else '', ui.R))
    ui.rule('=')
    print()

    copyright_spec = _ask_copyright_spec()
    print()

    done, fail = [], []
    for r in picked:
        sid   = r['id']
        fname = _skin_folder_name(r)      # "[<ID>] <Hero> <SkinName>"
        hero = (r.get('hero') or '').strip()
        skin = (r.get('name') or '').strip()
        final_title = ('%s %s' % (hero, skin)).strip() if hero else skin
        label = '%s  %s' % (sid, skin[:24])
        state = {'n': 0}

        def step():
            state['n'] += 1
            ui.bar(state['n'], STEPS, label)

        logs = []
        ui.bar(0, STEPS, label)

        skin_root  = os.path.join(OUT_DIR, fname)
        out_Android    = os.path.join(skin_root, 'Android', OUT_REL,
                                  'battleotherui.assetbundle')
        out_ios    = os.path.join(skin_root, 'IOS', OUT_REL,
                                  'battleotherui.assetbundle')
        outdir_Android = os.path.dirname(out_Android)
        outdir_ios = os.path.dirname(out_ios)

        # output path cho notify (huanhua .bytes) — cung pattern voi battle ui,
        # nhung theo yeu cau: [Android,IOS]/Resources/1.63.1/databin/client/huanhua/
        ntf_root_Android, ntf_root_ios = notify_engine.huanhua_out_dirs(skin_root)

        # tag in ra (FX/JOY + NTF neu co match notify.txt). Tag NTF chi la
        # du doan truoc — sau khi chay notify_engine xong, se sua lai neu
        # ID that su khong co trong ResBillboardSkinCfg (tuc la khong the
        # patch duoc, voi van giu logic mod nut nhu cu).
        tag_pre = r['parts']   # 'FX+JOY+NTF' | 'FX+JOY' | 'JOY+NTF' | ...

        # has_button: co file nut trong Source/ hay khong (skin thuan NTF khong co)
        has_button = bool(r['files'].get('effect') or r['files'].get('sprite_raw'))

        t0 = time.time()
        try:
            if has_button:
                size_Android, size_ios, errs = graft.build_one(
                    sid, r['files'], btn_dir,
                    out_android=out_Android,
                    out_ios=out_ios,
                    log=logs.append, step=step,
                    out_dir_android=outdir_Android,
                    out_dir_ios=outdir_ios,
                    copyright_spec=copyright_spec,
                )
            else:
                # Skin chi co thong bao ha -> khong mod nut, chi tang buoc
                # de bar tien do khong bi ket.
                size_Android, size_ios, errs = 0, 0, {}
                for _ in range(STEPS - 2):
                    step()
            ui.clear_line()

            # ===== Notify (thong bao ha) — chi goi neu co notify.txt va
            # Databin/Client/Huanhua/. Neu loi thi VAN giu mod nut (khong fail).
            ntf_status = 'skip'
            if os.path.isdir(DATABIN_DIR):
                try:
                    if r.get('notify', False):
                        n = notify_engine.build_one_notify(
                            int(sid), DATABIN_DIR, ntf_root_Android, ntf_root_ios,
                            log=logs.append)
                        ntf_status = n.get('status', 'skip')
                        if ntf_status == 'NTF':
                            logs.append('NTF     da patch thong bao ha (Android + IOS)')
                        elif ntf_status == 'skip':
                            logs.append('NTF     ID khong co trong ResBillboardSkinCfg, bo qua notify')
                    elif has_button:
                        # Skin co nut nhung khong co notify -> copy nguyen 4 file huahua
                        # de output du bo (Android + IOS).
                        notify_engine.copy_only(DATABIN_DIR, ntf_root_Android, ntf_root_ios)
                        logs.append('NTF     skin khong co thong bao ha, copy nguyen 4 file huahua')
                except Exception as e:
                    logs.append('! NTF loi (van giu mod nut): %s' % e)
            step()

            # Tag summary (sau cac buoc) — nếu notify trước đoán là NTF nhưng
            # thực tế skin ID không có trong Skincfg thi sua lai.
            tag_show = tag_pre
            if r.get('notify', False) and ntf_status != 'NTF':
                tag_show = tag_pre.replace('+NTF', '').replace('NTF', '').strip('+')

            ui.ok(' %s [%s]%s [✓]' % (final_title, sid, (' · ' + tag_show) if tag_show else ''))
            for l in logs:
                ui.info('   ' + l)
            if has_button:
                ui.info('   Android %.2f MB / iOS %.2f MB  ·  NT=%s  ·  %.1fs'
                        % ((size_Android or 0) / 1048576.0, (size_ios or 0) / 1048576.0,
                           ('YES' if ntf_status == 'NTF' else 'no'), time.time() - t0))
            else:
                ui.info('   NT=%s  ·  %.1fs'
                        % (('YES' if ntf_status == 'NTF' else 'no'), time.time() - t0))
            if errs:
                for plat, em in errs.items():
                    ui.warn('   [!] %s: %s' % (plat, em))
            if has_button:
                print(ui.DIM + '   -> Output/%s/{Android,IOS}/%s/' % (fname, OUT_REL.replace(os.sep, '/'))
                      + ui.R)
            if ntf_status == 'NTF' or r.get('notify', False):
                print(ui.DIM + '   -> Output/%s/{Android,IOS}/Resources/1.63.1/databin/client/huanhua/'
                      % fname + ui.R)
            done.append(sid)
        except Exception as e:
            ui.clear_line()
            print()
            ui.err('  [X] Loi [%s]: %s' % (sid, e))
            if os.environ.get('AOV_DEBUG'):
                traceback.print_exc()
            fail.append(sid)
        print()

    ui.rule('=')
    if done:
        ui.ok(' Hoan tat: ' + '  '.join('[%s]\u2713' % d for d in done))
    if fail:
        ui.err(' That bai: ' + '  '.join('[%s]\u2717' % d for d in fail))
    ui.rule('=')
    try:
        input(ui.B + '\n Enter de chay phien moi...' + ui.R)
    except (EOFError, KeyboardInterrupt):
        return False
    return True


def main():
    btn_dir, skn = preflight()
    ntf = os.path.join(NTF_DIR, 'notify.txt')
    ui.clear()
    ui.banner()
    ui.info('\n  Dang quet Source va doi chieu skin.txt' +
            (' + notify.txt...' if os.path.isfile(ntf) else '...'))
    rows = build_menu(SRC_DIR, skn, notify_txt=ntf, databin_dir=DATABIN_DIR)
    if not rows:
        ui.err('  [X] Source/ khong co file personalbutton* nao.')
        sys.exit(1)
    while run_session(rows, btn_dir):
        pass
    print()
    ui.info(' Tam biet.')



async def create_chained_link(gofile_link):
    """Nén link theo chuỗi: GoFile -> Link4m -> TrafficHD.
    Trả về (link_cuoi_cung, so_lop_nen). Thiếu lớp nào thì dùng link của lớp trước."""
    link4m = await create_link4m(gofile_link)
    if not link4m:
        return gofile_link, 0
    traffichd = await create_trafficHD(link4m)
    if traffichd:
        return traffichd, 2
    return link4m, 1

def _inline_skin_mod(ids, sang_dam=False, accessory_map=None):
    """Gọi đúng run_one_mod của engine đã nhúng, không tạo process con.
    sang_dam=True -> chạy chế độ '1' (Sáng Đậm) cho riêng acc đã bật /sangdamefx.
    accessory_map: dict {id_skin: "1"|"2"|"3"} – câu trả lời cho phụ kiện của
        các skin đặc biệt (11620 / 52007) mà engine hỏi qua input() console."""
    if pyzstd is None:
        raise RuntimeError(f"Thiếu pyzstd: {_PYZSTD_IMPORT_ERROR}")
    version = "UNKNOWN"
    r1 = os.path.join(BASE_DIR, "Resources_1")
    folders = [x for x in os.listdir(r1) if os.path.isdir(os.path.join(r1, x))] if os.path.isdir(r1) else []
    if folders: version = folders[0]
    with open(os.path.join(BASE_DIR, "Data", "Code", "ZSTD_DICT.xml"), "rb") as f:
        zdict = pyzstd.ZstdDict(f.read())
    with open(os.path.join(BASE_DIR, "Resources_1", "kb.txt"), "r", encoding="utf-8") as f:
        kb = f.readlines()
    dup = has_duplicate_hero_prefix(ids)
    mode = "1" if sang_dam else "3"
    # Engine hỏi phụ kiện qua input() cho 11620 (Tím/Xanh) và 52007 (Xanh/Đỏ).
    # Nếu user đã bấm chọn phụ kiện trong bot -> dùng giá trị đó.
    # Ngược lại -> mặc định "3" (No Mod) để không treo process.
    acc = accessory_map or {}
    original_input = builtins.input
    def _auto_input(prompt=""):
        p = str(prompt).lower()
        if "tím" in p or "tim" in p or "tím" in prompt or "62" in p or "component" in p or "1]" in prompt or "[1]" in prompt or "phu kien" in p:
            # Phụ kiện – cần map id_skin -> lựa chọn
            # Nếu không nhận diện được, mặc định "3"
            target_id = None
            for sid in ("11620", "52007"):
                if sid in prompt:
                    target_id = sid; break
            if target_id:
                v = acc.get(target_id)
                if v in {"1", "2", "3"}:
                    return v
            return "3"
        if "[2]" in prompt and "input" in p:
            target_id = None
            for sid in ("11620", "52007"):
                if sid in prompt:
                    target_id = sid; break
            if target_id:
                v = acc.get(target_id)
                if v in {"1", "2", "3"}:
                    return v
            return "3"
        return "3"
    builtins.input = _auto_input
    try:
        return run_one_mod(ids, version, Zstd_Aes, mode, "FILES_MOD/", {}, zdict, kb,
                           is_pack=(len(ids) > 1 and not dup))
    finally:
        builtins.input = original_input

def _inline_button_mod(sid):
    """Gọi đúng run_session của engine button nhúng, với input được cấp tự động."""
    source_dir  = os.path.join(BASE_DIR, "Source")
    skin_file   = os.path.join(BASE_DIR, "Skin", "skin.txt")
    notify_file = os.path.join(BASE_DIR, "Skin", "notify.txt")
    if not os.path.isdir(source_dir) or not os.path.isfile(skin_file):
        raise RuntimeError("Thiếu thư mục Source/ hoặc Skin/skin.txt của engine button.")
    rows = build_menu(source_dir, skin_file, notify_txt=notify_file,
                      databin_dir=os.path.join(BASE_DIR, "Databin", "Client", "Huanhua"))
    if not rows:
        raise RuntimeError("Engine button không đọc được danh sách button nào.")
    by_id = {str(r['id']).upper(): r for r in rows}
    if str(sid).upper() not in by_id:
        raise RuntimeError(f"ID {sid} không có trong engine button (kiểm tra Skin/skin.txt và Source/).")
    # Trả lời tự động: câu đầu = ID button, sau đó 'n' cho bản quyền;
    # hết answer thì mặc định 'n' cho prompt y/n, '' cho các prompt Enter.
    answers = [str(sid), "n"]
    original_input = builtins.input
    def _auto_input(prompt=""):
        if answers:
            return answers.pop(0)
        return "n" if "y/n" in str(prompt).lower() else ""
    builtins.input = _auto_input
    try:
        ok = run_session(rows, BASE_DIR)
    finally:
        builtins.input = original_input
    if not ok:
        raise RuntimeError("Engine button chạy xong nhưng không tạo được output.")
    return ok

# ==============================================================
#                          MAIN
# ==============================================================
if __name__ == "__main__":
    import time as _time

    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("telegram").setLevel(logging.ERROR)

    request = HTTPXRequest(
        connect_timeout=30, read_timeout=300,
        write_timeout=300, pool_timeout=30,
    )
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(request)
        .post_init(notify_bot_online)
        .build()
    )

    SKINS = read_skin_file(SKIN_TXT)

    app.add_error_handler(error_handler)

    # ----- Commands -----
    app.add_handler(CommandHandler("start",       start))
    app.add_handler(CommandHandler("run",         run))
    app.add_handler(CommandHandler("getkeyvip",   getkey))
    app.add_handler(CommandHandler("xemdanhsach", xemdanhsach))
    app.add_handler(CommandHandler("xoadanhsach", xoadanhsach))
    app.add_handler(CommandHandler("choosehero",  choosehero))
    app.add_handler(CommandHandler("layfile",     file_command))
    app.add_handler(CommandHandler("block",       block_user))
    app.add_handler(CommandHandler("unblock",     unblock_user))
    app.add_handler(CommandHandler("sendfiles",   send_files))
    app.add_handler(CommandHandler("all",         broadcast))
    # /newkeyvip trong menu người dùng mở thông tin liên hệ mua key;
    # admin vẫn dùng /getkeyvip để tạo key VIP theo thời hạn.
    app.add_handler(CommandHandler("newkeyvip",   getkey))
    app.add_handler(CommandHandler("inputkeyvip", inputkey))
    app.add_handler(CommandHandler("addadmin",    addadmin_cmd))
    app.add_handler(CommandHandler("deladmin",    deladmin_cmd))
    app.add_handler(CommandHandler("buttonmod",   buttonmod_cmd))
    app.add_handler(CommandHandler("sangdamefx", sangdamefx))
    app.add_handler(CommandHandler("danhsachlenh", danhsachlenh_cmd))
    app.add_handler(CommandHandler("danhsachnguoidung", danhsachnguoidung_cmd))

    # ----- Kích hoạt admin: /start/start/admin 34567 -----
    app.add_handler(MessageHandler(filters.Regex(r"^/start/start/admin(\s|$)"), admin_activate_cmd))

    # ----- Callback handlers -----
    app.add_handler(CallbackQueryHandler(button_mod_callback, pattern="^btnmod_"))
    app.add_handler(CallbackQueryHandler(reg_channel_callback, pattern="^reg_done$"))
    app.add_handler(CallbackQueryHandler(accessory_callback,    pattern=r"^ACC::"))
    app.add_handler(CallbackQueryHandler(camxa_callback,        pattern=r"^CAMXA::"))
    app.add_handler(CallbackQueryHandler(users_admin_callback,  pattern=r"^USR(EDIT|FLD|DET|PAGE)::"))
    app.add_handler(CallbackQueryHandler(button))

    # ----- Text handler -----
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    print("✅ Bot đang chạy...")

    while True:
        try:
            app.run_polling(drop_pending_updates=True, close_loop=False)
        except NetworkError:
            _time.sleep(5)
