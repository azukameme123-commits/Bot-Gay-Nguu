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
  - Nén 2 link: Link4m + TrafficHD
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
TRAFFICHD_API_URL = "https://trafficHD.co/api"

GOFILE_ACC_ID    = "bad3e48e-b80e-4603-8005-d2b3e12ca18f"
GOFILE_ACC_TOKEN = "na48eHcQTSFrT7KLMDVPGiHDrfavAKGP"

BOT_TOKEN = "8882361592:AAFjdQEZvp2znuWDvV9eYSWD35AqwWNTl8k"

# Key để cấp quyền Admin (user nhập /addadmin rồi gửi key này)
KEY_ADMIN_SV = "AdminSv"

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
SKIN_TXT           = "Data/Json/skin.txt"     # dùng cho /choosehero
NUTBAM_JSON        = "Data/Json/nutbam.json"  # danh sách button có thể mod

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
    try:
        return int(user_id) in get_admins()
    except Exception:
        return False

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
    ("sangdamefx", "Sáng đậm hiệu ứng"),
    ("layfile", "Lấy file"),
    ("fixreset", "Lấy File Anti Reset Mod"),
    ("resources", "Lấy File Resources Mới Nhất"),
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
]

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

async def sangdamefx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gửi file hiệu ứng nếu gói mod có sẵn file tương ứng."""
    await _send_latest_file(
        update,
        [MODPACK_DIR, BUTTONNOTIFY_DIR, OUTPUT_DIR],
        ("effect", "fx", "dame", "hiệu", "hieu"),
        "file sáng đậm hiệu ứng",
        "❌ Chưa tìm thấy file hiệu ứng. Hãy kiểm tra lại thư mục ModPack/Output."
    )

async def fixreset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gửi file anti-reset nếu có trong gói mod."""
    await _send_latest_file(
        update,
        [MODPACK_DIR, OUTPUT_DIR],
        ("anti", "fix", "reset", "resource"),
        "File Anti Reset Mod",
        "❌ Chưa tìm thấy File Anti Reset Mod trong thư mục ModPack/Output."
    )

async def resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gửi resource pack mới nhất nếu có."""
    await _send_latest_file(
        update,
        [MODPACK_DIR, BUTTONNOTIFY_DIR, OUTPUT_DIR],
        ("resource", "res", "resources"),
        "File Resources Mới Nhất",
        "❌ Chưa tìm thấy Resources. Hãy đặt file resources vào ModPack hoặc Output."
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
    users[user_id] = {
        "first_name": user.first_name,
        "last_name":  user.last_name or "",
        "username":   user.username,
    }
    save_json(FILE_USERS, users)

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
            if msg:
                try: await msg.delete()
                except Exception: pass
            return

        # ===== Callback cho button mod (đổi vé) =====
        if data.startswith("btnmod_"):
            await button_mod_callback(update, context)
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

def _pick_latest_folder(folder, before_ts=0):
    """Lấy folder con mới nhất tạo sau `before_ts`."""
    best = None; best_ts = before_ts
    if not os.path.isdir(folder):
        return None
    for name in os.listdir(folder):
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
    await msg.edit_text("⏳ Đang mod trực tiếp bằng engine đã gắn trong bot, vui lòng đợi...")
    output_root = os.path.join(BASE_DIR, "FILES_MOD")
    os.makedirs(output_root, exist_ok=True)
    before = set(os.listdir(output_root))
    try:
        new_folder = await asyncio.to_thread(_inline_skin_mod, ids)
    except Exception as exc:
        await msg.edit_text(f"❌ Tạo mod thất bại: {exc}")
        return
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
    await msg.edit_text(f"🎉 Mod Skin:\n{all_tuongs_str}\n{all_skins_str}\nHoàn Tất\n\n➡️ Dùng /layfile Để Nhận Link Tải File Mod 📁.")
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
    try:
        encoded = urllib.parse.quote_plus(long_url)
        candidates = [
            f"{TRAFFICHD_API_URL}?api={TRAFFICHD_API}&url={encoded}",
            f"https://trafficHD.co/api?api={TRAFFICHD_API}&url={encoded}",
        ]
        async with aiohttp.ClientSession() as session:
            for api_url in candidates:
                try:
                    async with session.get(api_url, timeout=30) as resp:
                        if resp.status != 200: continue
                        try:
                            data = await resp.json(content_type=None)
                        except Exception:
                            continue
                        if str(data.get("status", "")).lower() == "success":
                            return (data.get("shortenedUrl") or data.get("shortUrl")
                                    or data.get("short"))
                except Exception:
                    continue
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
        link4m    = await create_link4m(gofile_link)
        traffichd = await create_trafficHD(gofile_link)

        if not link4m and not traffichd:
            await update.message.reply_text("❌ Tạo Link Rút Gọn Thất Bại.")
            return

        gained = (1 if link4m else 0) + (1 if traffichd else 0)
        remain, tickets = add_link_count(user_id, gained)

        lines_out = ["✅ **FILE MOD ĐÃ SẴN SÀNG ( User Normal )**\n",
                     "➢ **Vượt Đủ 2 Link Bên Dưới Để Lấy File**"]
        if link4m:    lines_out.append(f"🔗 **Link 1 (Link4m):**\n{link4m}")
        if traffichd: lines_out.append(f"🔗 **Link 2 (TrafficHD):**\n{traffichd}")
        lines_out.append("")
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

    # Chỉ hiển thị 40 button đầu để nhẹ; user có nhiều thì tự chọn qua trang
    keyboard = []
    for sid, name in list(nutbam.items())[:40]:
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

    new_folder = _pick_latest_folder(output_root, before_ts=ts_before)
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
        link4m    = await create_link4m(gofile_link)
        traffichd = await create_trafficHD(gofile_link)
        lines_out = [f"✅ **BUTTON MOD SẴN SÀNG (User)**\n➢ ID: {sid}\n"]
        if link4m:    lines_out.append(f"🔗 **Link 1 (Link4m):**\n{link4m}")
        if traffichd: lines_out.append(f"🔗 **Link 2 (TrafficHD):**\n{traffichd}")
        if not link4m and not traffichd:
            lines_out.append(f"🔗 {gofile_link}")
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

    # 3) Còn lại: chat_all
    await chat_all(update, context)

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
        if low.endswith(".pkg.bytes"):
            dst_dir = base
        elif low.endswith(".assetbundle"):
            dst_dir = base / "assetbundle" / "uisystem" / "atlas" / "primary"
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
    by_id = {r['id']: r for r in rows}
    picked, bad = [], []
    
    # Neu Nhan Enter (chuoi rong), tu dong chon tat ca cac skin trong menu
    if not text.strip():
        return list(rows), []

    for tok in text.replace(',', ' ').split():
        tok = tok.strip()
        if not tok:
            continue
        if tok.isdigit() and tok in by_id:
            if by_id[tok] not in picked:
                picked.append(by_id[tok])
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



def _inline_skin_mod(ids):
    """Gọi đúng run_one_mod của engine đã nhúng, không tạo process con."""
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
    return run_one_mod(ids, version, Zstd_Aes, "3", "FILES_MOD/", {}, zdict, kb, is_pack=(len(ids) > 1 and not dup))

def _inline_button_mod(sid):
    """Gọi đúng run_session của engine button nhúng, với input được cấp tự động."""
    source_dir = os.path.join(BASE_DIR, "Source")
    skin_file = os.path.join(BASE_DIR, "Skin", "skin.txt")
    notify_file = os.path.join(BASE_DIR, "Skin", "notify.txt")
    rows = build_menu(source_dir, skin_file, notify_txt=notify_file, databin_dir=os.path.join(BASE_DIR, "Databin", "Client", "Huanhua"))
    answers = iter([str(sid), "n", ""])
    original_input = builtins.input
    builtins.input = lambda prompt="": next(answers)
    try:
        return run_session(rows, BASE_DIR)
    finally:
        builtins.input = original_input

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
    app.add_handler(CommandHandler("fixreset",    fixreset))
    app.add_handler(CommandHandler("resources",   resources))

    # ----- Callback handlers -----
    app.add_handler(CallbackQueryHandler(button_mod_callback, pattern="^btnmod_"))
    app.add_handler(CallbackQueryHandler(button))

    # ----- Text handler -----
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    print("✅ Bot đang chạy...")

    while True:
        try:
            app.run_polling(drop_pending_updates=True, close_loop=False)
        except NetworkError:
            _time.sleep(5)
