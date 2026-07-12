import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import os
import tempfile
import shutil
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
application = Application.builder().token(TOKEN).build()

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
            heights.add(h)
        if f.get("vcodec") in (None, "none") and f.get("acodec") not in (None, "none"):
            has_audio_only = True

    if not heights:
        return None

    sorted_heights = sorted(heights, reverse=True)
    
    if len(sorted_heights) > 1:
        medium_idx = len(sorted_heights) // 2
        medium_height = sorted_heights[medium_idx]
        medium_label = f"RECOMMENDED - {medium_height}p"
    else:
        medium_height = sorted_heights[0]
        medium_label = f"RECOMMENDED - {medium_height}p"

    options = [
        {
            "label": medium_label,
            "format": f"bestvideo[height<={medium_height}][ext=mp4]+bestaudio[ext=m4a]/best",
            "is_recommended": True
        }
    ]

    # Show only top 2 qualities (instead of 6)
    for h in sorted_heights[:2]:
        label = f"{h}p"
        if h == medium_height:
            continue
        options.append({
            "label": label,
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
        "socket_timeout": 30,  # 30 second timeout
        "http_chunk_size": 10485760,  # 10MB chunks
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
    MAX_TELEGRAM_MB = 2000
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    is_valid = size_mb <= MAX_TELEGRAM_MB
    return is_valid, size_mb

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Google Chrome", callback_data="chrome")],
    ]
    await update.message.reply_text(
        "Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chrome_selected(query, context):
    await query.message.edit_text(
        "Send me any video link and I will download it for you!\n\n"
        "Examples:\n"
        "- Google Drive\n"
        "- YouTube\n"
        "- TikTok\n"
        "- Instagram\n"
        "- Any other video link"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if not text.startswith("http"):
        await update.message.reply_text("Please send a valid URL starting with http or https")
        return

    checking_msg = await update.message.reply_text("Checking available qualities...")

    options = get_available_qualities(text)
    if not options:
        await checking_msg.edit_text(
            "No qualities available\n\n"
            "The video might be:\n"
            "- Protected or private\n"
            "- Invalid URL\n"
            "- No video content found\n\n"
            "Try another video"
        )
        return

    context.user_data[user_id] = {"url": text, "options": options}

    keyboard = [
        [InlineKeyboardButton(opt["label"], callback_data=f"q_{i}")]
        for i, opt in enumerate(options[:3])
    ]
    await checking_msg.edit_text(
        "Select quality:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # If there are more than 3 options, send them in a separate message
    if len(options) > 3:
        keyboard2 = [
            [InlineKeyboardButton(opt["label"], callback_data=f"q_{i}")]
            for i, opt in enumerate(options[3:], start=3)
        ]
        await update.message.reply_text(
            "More options:",
            reply_markup=InlineKeyboardMarkup(keyboard2)
        )

async def quality_chosen(query, context, user_id):
    user_info = context.user_data.get(user_id)
    if not user_info:
        await query.message.reply_text("Request expired. Send the URL again")
        return

    try:
        idx = int(query.data.split("_", 1)[1])
        option = user_info["options"][idx]
    except (ValueError, IndexError):
        await query.message.reply_text("Invalid option. Try again.")
        return

    url = user_info["url"]
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
                f"Max allowed: 2000 MB\n\n"
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
        context.user_data.pop(user_id, None)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)

    await query.answer()

    if query.data == "chrome":
        await chrome_selected(query, context)
    elif query.data.startswith("q_"):
        await quality_chosen(query, context, user_id)

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

def main():
    print("Bot running...")
    application.run_polling()

if __name__ == "__main__":
    main()
