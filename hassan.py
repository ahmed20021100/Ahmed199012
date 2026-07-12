import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import json
import os
import tempfile
import shutil

import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 1025310531

MAX_TELEGRAM_MB = 2000
MAX_QUALITY_HEIGHT = 4000  # Allow all qualities

PLATFORMS = {
    "tiktok": "tiktok",
    "instagram": "instagram",
    "twitter": "twitter",
    "facebook": "facebook",
    "reddit": "reddit",
    "pinterest": "pinterest",
    "snapchat": "snapchat",
    "vimeo": "vimeo",
    "likee": "likee",
    "other": "other",
}

user_data = {}
user_activity = {}
command_usage = {}
user_selected_platform = {}

user_pending_link = {}

def load_data():
    global user_data, user_activity, command_usage
    try:
        with open('user_data.json', 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    except:
        user_data = {}

    try:
        with open('user_activity.json', 'r', encoding='utf-8') as f:
            user_activity = json.load(f)
    except:
        user_activity = {}

    try:
        with open('command_usage.json', 'r', encoding='utf-8') as f:
            command_usage = json.load(f)
    except:
        command_usage = {}

def save_data():
    with open('user_data.json', 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)
    with open('user_activity.json', 'w', encoding='utf-8') as f:
        json.dump(user_activity, f, ensure_ascii=False, indent=2)
    with open('command_usage.json', 'w', encoding='utf-8') as f:
        json.dump(command_usage, f, ensure_ascii=False, indent=2)

load_data()

logging.basicConfig(level=logging.INFO)

application = Application.builder().token(TOKEN).build()

def log_user_activity(user_id, command):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_activity[str(user_id)] = now
    if command not in command_usage:
        command_usage[command] = 0
    command_usage[command] += 1
    save_data()

def get_platforms_keyboard():
    labels = {
        "tiktok": u"TikTok",
        "instagram": u"Instagram",
        "twitter": u"Twitter/X",
        "facebook": u"Facebook",
        "reddit": u"Reddit",
        "pinterest": u"Pinterest",
        "snapchat": u"Snapchat",
        "vimeo": u"Vimeo",
        "likee": u"Likee",
        "other": u"Other",
    }
    keyboard = [
        [InlineKeyboardButton(labels[key], callback_data=key)]
        for key in PLATFORMS.keys()
    ]
    return InlineKeyboardMarkup(keyboard)

def get_available_qualities(url: str):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        logging.error(f"Error checking qualities: {e}")
        return None

    formats = info.get("formats") or []

    heights = set()
    has_audio_only = False
    for f in formats:
        if f.get("vcodec") not in (None, "none") and f.get("height"):
            h = int(f["height"])
            if h <= MAX_QUALITY_HEIGHT:
                heights.add(h)
        if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none"):
            has_audio_only = True

    if not heights:
        return None

    options = [{"label": "Best Quality (up to 720p)", "format": f"bestvideo[height<={MAX_QUALITY_HEIGHT}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"}]

    filtered_heights = sorted([h for h in heights if h <= MAX_QUALITY_HEIGHT], reverse=True)[:4]
    for h in filtered_heights:
        options.append({
            "label": f"{h}p",
            "format": f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]",
        })

    if has_audio_only:
        options.append({"label": "Audio Only (MP3)", "format": "bestaudio/best", "audio_only": True})

    return options

def download_video(url: str, output_dir: str, format_spec: str = "best[ext=mp4]/best", audio_only: bool = False):
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    ydl_opts = {
        "outtmpl": output_template,
        "format": format_spec,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if audio_only:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }]
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                filename = os.path.splitext(filename)[0] + ".mp3"
            if os.path.exists(filename):
                return filename
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
    return None

def check_file_size(file_path: str) -> tuple:
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    is_valid = size_mb <= MAX_TELEGRAM_MB
    return is_valid, size_mb

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if str(user_id) not in user_data:
        user_data[str(user_id)] = {
            'first_name': user.first_name,
            'last_name': user.last_name or '',
            'username': user.username or '',
            'user_id': user_id,
            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'is_bot': user.is_bot,
            'language_code': user.language_code or ''
        }
        save_data()

    log_user_activity(str(user_id), "/start")

    await update.message.reply_text(
        "Hello! Select a platform to download from:",
        reply_markup=get_platforms_keyboard()
    )

async def start_callback(query, context):
    await query.message.edit_text(
        "Select Platform:",
        reply_markup=get_platforms_keyboard()
    )

async def stats_callback(message, context):
    total_users = len(user_data)

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    active_today = sum(1 for u in user_activity.values() if u.startswith(today))
    active_week = sum(1 for u in user_activity.values() if u >= week_ago)
    active_month = sum(1 for u in user_activity.values() if u >= month_ago)

    stats_text = f"Total Users: {total_users}\n"
    stats_text += f"Active Today: {active_today}\n"
    stats_text += f"Active Week: {active_week}\n"
    stats_text += f"Active Month: {active_month}\n\n"

    sorted_commands = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    stats_text += "Top Platforms:\n"
    for cmd, count in sorted_commands:
        stats_text += f"`{cmd}`: {count} times\n"

    await message.reply_text(stats_text)

async def users_callback(message, context):
    users_list = list(user_data.values())
    users_list.reverse()
    users_list = users_list[:10]

    text = "Last 10 Users:\n\n"
    for i, user in enumerate(users_list, 1):
        name = user.get('first_name', 'Unknown')
        username = user.get('username', '')
        added = user.get('added_date', '')
        user_id_display = user.get('user_id', '')

        text += f"{i}. {name}\n"
        if username:
            text += f"   @{username}\n"
        text += f"   {added}\n"
        text += f"   ID: {user_id_display}\n\n"

    await message.reply_text(text)

async def export_callback(message, context):
    data = {
        'users': user_data,
        'activity': user_activity,
        'commands': command_usage,
        'export_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_users': len(user_data)
    }

    with open('export_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open('export_data.json', 'rb') as f:
        await context.bot.send_document(
            chat_id=message.chat.id,
            document=f,
            filename=f'users_export_{datetime.now().strftime("%Y%m%d")}.json',
            caption="User Data Export"
        )

    os.remove('export_data.json')

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)

    await query.answer()

    log_user_activity(user_id, query.data)

    if query.data in PLATFORMS:
        user_selected_platform[user_id] = query.data
        await query.message.reply_text(
            f"Selected: {query.data}\n\n"
            "Send me the video URL"
        )

    elif query.data.startswith("q_"):
        await quality_chosen(query, context, user_id)

    elif query.data == "home":
        await start_callback(query, context)

    elif query.data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.message.reply_text("Admin only")
            return

        admin_keyboard = [
            [InlineKeyboardButton("Stats", callback_data="admin_stats")],
            [InlineKeyboardButton("Users", callback_data="admin_users")],
            [InlineKeyboardButton("Export", callback_data="admin_export")],
            [InlineKeyboardButton("Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("Back", callback_data="home")]
        ]

        await query.message.edit_text(
            "Admin Panel\n\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
        )

    elif query.data == "admin_stats":
        await stats_callback(query.message, context)

    elif query.data == "admin_users":
        await users_callback(query.message, context)

    elif query.data == "admin_export":
        await export_callback(query.message, context)

    elif query.data == "admin_settings":
        settings_text = (
            "Bot Settings\n\n"
            f"Max File Size: {MAX_TELEGRAM_MB} MB\n"
            f"Max Quality: {MAX_QUALITY_HEIGHT}p\n\n"
            "Edit the variables in the code to change settings"
        )
        await query.message.reply_text(settings_text)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if not text.startswith("http"):
        await update.message.reply_text("Please send a valid URL starting with http or https")
        return

    if user_id not in user_selected_platform:
        await update.message.reply_text(
            "Select a platform first:",
            reply_markup=get_platforms_keyboard()
        )
        return

    checking_msg = await update.message.reply_text("Checking available qualities...")

    options = get_available_qualities(text)
    if not options:
        await checking_msg.edit_text(
            f"No qualities available up to {MAX_QUALITY_HEIGHT}p\n\n"
            "The video might be:\n"
            f"- Only available in qualities higher than {MAX_QUALITY_HEIGHT}p\n"
            "- Protected or private\n"
            "- Invalid URL\n\n"
            "Try another video"
        )
        return

    user_pending_link[user_id] = {"url": text, "options": options}

    keyboard = [
        [InlineKeyboardButton(opt["label"], callback_data=f"q_{i}")]
        for i, opt in enumerate(options)
    ]
    await checking_msg.edit_text(
        f"Select quality:\n\nMax: {MAX_QUALITY_HEIGHT}p and {MAX_TELEGRAM_MB} MB",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quality_chosen(query, context, user_id):
    pending = user_pending_link.get(user_id)
    if not pending:
        await query.message.reply_text("Request expired. Send the URL again")
        return

    try:
        idx = int(query.data.split("_", 1)[1])
        option = pending["options"][idx]
    except (ValueError, IndexError):
        await query.message.reply_text("Invalid option. Try again.")
        return

    url = pending["url"]
    audio_only = option.get("audio_only", False)

    status_msg = await query.message.reply_text("Downloading...")
    tmp_dir = tempfile.mkdtemp(prefix="vid_")

    try:
        file_path = download_video(url, tmp_dir, format_spec=option["format"], audio_only=audio_only)

        if file_path is None:
            await status_msg.edit_text(
                "Could not download with this quality\n"
                "Try a lower quality or check the URL."
            )
            return

        is_valid, size_mb = check_file_size(file_path)
        if not is_valid:
            await status_msg.edit_text(
                f"File size: {size_mb:.1f} MB\n\n"
                f"Max allowed: {MAX_TELEGRAM_MB} MB\n\n"
                "Try a lower quality or shorter video"
            )
            return

        await status_msg.edit_text("Downloaded. Sending...")
        if audio_only:
            with open(file_path, "rb") as audio_file:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=audio_file)
        else:
            with open(file_path, "rb") as video_file:
                await context.bot.send_video(chat_id=query.message.chat_id, video=video_file)
        await status_msg.delete()

    except Exception as e:
        logging.error(f"Error: {e}")
        await status_msg.edit_text(f"Error: {e}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        user_pending_link.pop(user_id, None)

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

def main():
    print("Bot running...")
    application.run_polling()

if __name__ == "__main__":
    main()
