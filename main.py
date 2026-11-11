import json
import os
import random
import re
import time
from html import escape
from typing import Any, Dict

from telegram import ChatType, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# Konfigurasi
BOT_TOKEN = os.getenv("BOT_TOKEN", "ISI_TOKEN_KAMU")
OWNER_ID = 1056686795
BOT_NAME = "Adik Kecil"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILTER_FILE = os.path.join(BASE_DIR, "filters.json")
CONFESS_FILE = os.path.join(BASE_DIR, "confess_settings.json")


def load_json(file_path: str) -> Dict[str, Any]:
    """Muat data JSON; kembalikan objek kosong bila file belum ada/rusak."""
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}

    return data if isinstance(data, dict) else {}


def save_json(file_path: str, data: Dict[str, Any]) -> None:
    """Simpan data JSON dengan format yang mudah dibaca."""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


filters_db = load_json(FILTER_FILE)
confess_settings = load_json(CONFESS_FILE)
confess_cooldown: Dict[int, float] = {}
start_time = time.time()


def parse_variables(text: str, user, chat) -> str:
    username = f"@{user.username}" if user.username else user.first_name or ""
    first_name = escape(user.first_name or "")

    variables = {
        "{first}": first_name,
        "{fullname}": escape(user.full_name or ""),
        "{username}": escape(username),
        "{mention}": f"<a href='tg://user?id={user.id}'>{first_name}</a>",
        "{id}": str(user.id),
        "{chatname}": escape(chat.title or chat.first_name or ""),
        "{time}": time.strftime("%H:%M:%S"),
    }

    for key, value in variables.items():
        text = text.replace(key, value)
    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None or update.message is None:
        return

    text = (
        f"👋✨ Hai <b>{escape(user.full_name)}</b>!\n\n"
        f"Aku adalah bot <b>{escape(BOT_NAME)}</b> 🤖💖\n"
        "Yang akan membuat grupmu semakin ramai 🔥😆\n\n"
        "Ketik /waymenu untuk melihat semua fitur ku 📌✨"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def waymenu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    text = f"""<b>🤖 MENU BOT {escape(BOT_NAME)}</b>

🔥 FUN SYSTEM
🔹 /ship (reply orang)
🔹 /confess isi pesan (private)
🔹 /setconfess -100xxxxxxxx (owner only)
🔹 /setcooldown angka (private owner only)

⚙ FILTER SYSTEM
🔹 /filter trigger&gt;reply
🔹 /stop trigger
🔹 /filterlist

📊 INFO
🔹 /ping
"""
    await update.message.reply_text(text, parse_mode="HTML")


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        uptime = int(time.time() - start_time)
        await update.message.reply_text(f"🏓 Bot aktif {uptime} detik 🔥")


async def set_confess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if user is None or user.id != OWNER_ID or chat is None:
        return
    if chat.type != ChatType.PRIVATE:
        if update.message:
            await update.message.reply_text("Gunakan di private chat bot.")
        return
    if not context.args:
        if update.message:
            await update.message.reply_text("Format:\n/setconfess -100xxxxxxxx")
        return

    confess_settings["target_group"] = context.args[0].strip()
    confess_settings.setdefault("cooldown", 60)
    save_json(CONFESS_FILE, confess_settings)
    if update.message:
        await update.message.reply_text("✅ Grup target confess berhasil diset.")


async def set_cooldown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if user is None or user.id != OWNER_ID or chat is None or chat.type != ChatType.PRIVATE:
        return
    if not context.args:
        if update.message:
            await update.message.reply_text("Format:\n/setcooldown 60")
        return

    try:
        delay = int(context.args[0])
        if delay < 0:
            raise ValueError
    except ValueError:
        if update.message:
            await update.message.reply_text("Cooldown harus berupa angka nol atau lebih.")
        return

    confess_settings["cooldown"] = delay
    save_json(CONFESS_FILE, confess_settings)
    if update.message:
        await update.message.reply_text(f"✅ Cooldown diatur ke {delay} detik")


async def confess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.message
    if chat is None or chat.type != ChatType.PRIVATE or user is None or message is None:
        return
    if "target_group" not in confess_settings:
        await message.reply_text("Owner belum set target grup.")
        return
    if not context.args:
        await message.reply_text("Format:\n/confess isi pesan")
        return

    delay = max(0, int(confess_settings.get("cooldown", 60)))
    now = time.time()
    remaining = delay - (now - confess_cooldown.get(user.id, 0))
    if remaining > 0:
        await message.reply_text(f"⏳ Tunggu {int(remaining)} detik lagi.")
        return

    text = (
        "💌 <b>CONFESS ANONIM</b>\n\n"
        f"{escape(' '.join(context.args))}\n\n"
        "👤 <i>Pengirim dirahasiakan</i>"
    )
    await context.bot.send_message(
        chat_id=confess_settings["target_group"],
        text=text,
        parse_mode="HTML",
    )
    confess_cooldown[user.id] = now
    await message.reply_text(f"✅ Confess terkirim!\nBisa kirim lagi dalam {delay} detik ⏳")


async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    user = update.effective_user
    if message is None or user is None:
        return
    replied = message.reply_to_message
    if replied is None:
        await message.reply_text("Reply seseorang lalu ketik /ship 😏")
        return
    if replied.from_user is None:
        await message.reply_text("User yang di-reply tidak valid.")
        return

    percent = random.randint(1, 100)
    text = (
        "💘 <b>HASIL SHIP</b>\n\n"
        f"{escape(user.first_name)} ❤️ {escape(replied.from_user.first_name)}\n\n"
        f"{percent}%"
    )
    await message.reply_text(text, parse_mode="HTML")


async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat = update.effective_chat
    if message is None or message.text is None or chat is None:
        return

    _, separator, data = message.text.partition(" ")
    if not separator or ">" not in data:
        await message.reply_text("Format: /filter trigger>balasan")
        return
    trigger, reply = data.split(">", 1)
    trigger, reply = trigger.strip(), reply.strip()
    if not trigger or not reply:
        await message.reply_text("Trigger dan balasan tidak boleh kosong.")
        return

    chat_id = str(chat.id)
    filters_db.setdefault(chat_id, {})[trigger.lower()] = {"reply": reply}
    save_json(FILTER_FILE, filters_db)
    await message.reply_text("✅ Filter ditambahkan")


async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.message
    if chat is None or message is None or not context.args:
        return

    chat_id = str(chat.id)
    trigger = context.args[0].lower()
    if chat_id in filters_db and trigger in filters_db[chat_id]:
        del filters_db[chat_id][trigger]
        if not filters_db[chat_id]:
            del filters_db[chat_id]
        save_json(FILTER_FILE, filters_db)
        await message.reply_text("❌ Filter dihapus")
    else:
        await message.reply_text("Filter tidak ditemukan.")


async def filter_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.message
    if chat is None or message is None:
        return

    chat_filters = filters_db.get(str(chat.id), {})
    if not chat_filters:
        await message.reply_text("Tidak ada filter.")
        return

    triggers = "\n".join(f"• {escape(trigger)}" for trigger in chat_filters)
    await message.reply_text(f"📌 <b>Daftar Filter:</b>\n\n{triggers}", parse_mode="HTML")


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    chat = update.effective_chat
    user = update.effective_user
    if message is None or message.text is None or chat is None or user is None:
        return

    for trigger, data in filters_db.get(str(chat.id), {}).items():
        try:
            matched = re.search(trigger, message.text, re.IGNORECASE)
        except re.error:
            continue
        if matched:
            reply = parse_variables(data.get("reply", ""), user, chat)
            await message.reply_text(reply, parse_mode="HTML")
            break


def main() -> None:
    if not BOT_TOKEN or BOT_TOKEN == "ISI_TOKEN_KAMU":
        raise RuntimeError("Atur BOT_TOKEN sebagai environment variable sebelum menjalankan bot.")

    app = Application.builder().token(BOT_TOKEN).build()
    handlers = [
        ("start", start),
        ("waymenu", waymenu),
        ("ping", ping),
        ("setconfess", set_confess),
        ("confess", confess),
        ("setcooldown", set_cooldown),
        ("ship", ship),
        ("filter", add_filter),
        ("stop", stop_filter),
        ("filterlist", filter_list),
    ]
    for command, callback in handlers:
        app.add_handler(CommandHandler(command, callback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    print("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
