import random
import re
import time
from typing import Any, Dict, Optional

from telegram import ChatType, Update
from telegram.ext import ContextTypes

from config import BOT_NAME, CONFESS_FILE, FILTER_FILE, OWNER_ID
from database import confess_cooldown, confess_settings, filters_db, save_json


def parse_variables(text: str, user, chat) -> str:
    if not text:
        return ""

    username = f"@{user.username}" if getattr(user, "username", None) else getattr(user, "first_name", "")

    variables: Dict[str, str] = {
        "{first}": getattr(user, "first_name", "") or "",
        "{fullname}": getattr(user, "full_name", "") or "",
        "{username}": username,
        "{mention}": (
            f"<a href='tg://user?id={user.id}'>{getattr(user, 'first_name', '')}</a>"
            if getattr(user, "id", None) is not None
            else ""
        ),
        "{id}": str(getattr(user, "id", "")),
        "{chatname}": getattr(chat, "title", "") or getattr(chat, "first_name", "") or "",
        "{time}": time.strftime("%H:%M:%S"),
    }

    for key, value in variables.items():
        text = text.replace(key, value)

    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user is None:
        return

    text = (
        f"👋✨ Hai <b>{user.full_name}</b>!\n\n"
        f"Aku adalah bot <b>{BOT_NAME}</b> 🤖💖\n"
        "Yang akan membuat grupmu semakin ramai 🔥😆\n\n"
        "Ketik /waymenu untuk melihat semua fitur ku 📌✨"
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def waymenu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = f"""
<b>🤖 MENU BOT {BOT_NAME}</b>

🔥 FUN SYSTEM
🔹 /ship (reply orang)
🔹 /confess isi pesan (private)
🔹 /setconfess -100xxxxxxxx (owner only)
🔹 /setcooldown angka (private owner only)

⚙ FILTER SYSTEM
🔹 /filter trigger>reply
🔹 /stop trigger
🔹 /filterlist

📊 INFO
🔹 /ping
"""
    await update.message.reply_text(text, parse_mode="HTML")


start_time = time.time()


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uptime = int(time.time() - start_time)
    await update.message.reply_text(f"🏓 Bot aktif {uptime} detik 🔥")


async def set_confess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_user.id != OWNER_ID:
        return

    if update.effective_chat.type != ChatType.PRIVATE:
        await update.message.reply_text("Gunakan di private chat bot.")
        return

    if not context.args:
        await update.message.reply_text("Format:\n/setconfess -100xxxxxxxx")
        return

    group_id = context.args[0].strip()
    confess_settings["target_group"] = group_id
    confess_settings["cooldown"] = 60
    save_json(CONFESS_FILE, confess_settings)

    await update.message.reply_text("✅ Grup target confess berhasil diset.")


async def set_cooldown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.effective_user.id != OWNER_ID:
        return

    if update.effective_chat.type != ChatType.PRIVATE:
        return

    if not context.args:
        await update.message.reply_text("Format:\n/setcooldown 60")
        return

    try:
        delay = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Cooldown harus berupa angka.")
        return

    confess_settings["cooldown"] = delay
    save_json(CONFESS_FILE, confess_settings)

    await update.message.reply_text(f"✅ Cooldown diatur ke {delay} detik")


async def confess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type != ChatType.PRIVATE:
        return

    if "target_group" not in confess_settings:
        await update.message.reply_text("Owner belum set target grup.")
        return

    if not context.args:
        await update.message.reply_text("Format:\n/confess isi pesan")
        return

    user_id = update.effective_user.id
    delay = confess_settings.get("cooldown", 60)
    now = time.time()

    if user_id in confess_cooldown:
        remaining = delay - (now - confess_cooldown[user_id])
        if remaining > 0:
            await update.message.reply_text(f"⏳ Tunggu {int(remaining)} detik lagi.")
            return

    confess_cooldown[user_id] = now
    message_text = " ".join(context.args)

    text = (
        "💌 <b>CONFESS ANONIM</b>\n\n"
        f"{message_text}\n\n"
        "👤 <i>Pengirim dirahasiakan</i>"
    )

    await context.bot.send_message(
        chat_id=confess_settings["target_group"],
        text=text,
        parse_mode="HTML",
    )

    await update.message.reply_text(f"✅ Confess terkirim!\nBisa kirim lagi dalam {delay} detik ⏳")


async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Reply seseorang lalu ketik /ship 😏")
        return

    if update.message.reply_to_message.from_user is None:
        await update.message.reply_text("User yang di-reply tidak valid.")
        return

    user1 = update.effective_user
    user2 = update.message.reply_to_message.from_user
    percent = random.randint(1, 100)

    text = (
        f"💘 <b>HASIL SHIP</b>\n\n"
        f"{user1.first_name} ❤️ {user2.first_name}\n\n"
        f"{percent}%"
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or ">" not in update.message.text:
        return

    message = update.message.text.split(" ", 1)
    if len(message) < 2:
        return

    data = message[1]
    trigger, reply = data.split(">", 1)

    chat_id = str(update.effective_chat.id)
    filters_db.setdefault(chat_id, {})
    filters_db[chat_id][trigger.strip().lower()] = {"reply": reply.strip()}

    save_json(FILTER_FILE, filters_db)
    await update.message.reply_text("✅ Filter ditambahkan")


async def stop_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        return

    trigger = context.args[0].lower()
    chat_id = str(update.effective_chat.id)

    if chat_id in filters_db and trigger in filters_db[chat_id]:
        del filters_db[chat_id][trigger]
        save_json(FILTER_FILE, filters_db)
        await update.message.reply_text("❌ Filter dihapus")


async def filter_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)

    if chat_id not in filters_db:
        await update.message.reply_text("Tidak ada filter.")
        return

    text = "📌 <b>Daftar Filter:</b>\n\n"
    for trigger in filters_db[chat_id]:
        text += f"• {trigger}\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    text = update.message.text

    if chat_id not in filters_db:
        return

    for trigger, data in filters_db[chat_id].items():
        if re.search(trigger, text, re.IGNORECASE):
            reply = parse_variables(
                data["reply"],
                update.effective_user,
                update.effective_chat,
            )
            await update.message.reply_text(reply, parse_mode="HTML")
            break
