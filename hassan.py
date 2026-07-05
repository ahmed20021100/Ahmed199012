import os
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HASSAN_7 = os.environ.get("HASSAN_7")

if not HASSAN_7:
    logger.error("HASSAN_7 غير موجود")
    exit(1)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters
    logger.info("تم تحميل المكتبات")
except Exception as e:
    logger.error(f"خطأ في التحميل: {e}")
    exit(1)


 # المنصات
PLATFORMS = {
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "twitter": "Twitter",
    "reddit": "Reddit",
    "pinterest": "Pinterest",
    "vimeo": "Vimeo",
    "dailymotion": "Dailymotion",
    "twitch": "Twitch",
    "google": "اي رابط"
}

def get_buttons():
    buttons = []
    row = []
    emojis = {
        "youtube": "🎬", "tiktok": "🎵", "instagram": "📸",
        "facebook": "📘", "twitter": "🐦", "reddit": "🤖",
        "pintere
s "vimeo": "🎥", "dailymotion": "🎞️",
        "twitch": "🎮", "google": "🌐"
    }
    for key, name in PLATFORMS.items():
        btn = InlineKeyboardButton(f"{emojis.get(key, '')} {name}", callback_data=f"p_{key}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "اختر المنصة:",
        reply_markup=InlineKeyboardMarkup(get_buttons())

     )

async def select_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("p_", "")
    context.user_data['platform'] = key
    name = PLATFORMS.get(key, "")
    await query.edit_message_text(
        f"تم اختيار: {name}\nارسل الرابط:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="b")]])
    )

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(
)context.user_data.pop('platform', None)
    await query.edit_message_text(
        "اختر المنصة:",
        reply_markup=InlineKeyboardMarkup(get_buttons())
    )

def detect_platform(url):
    patterns = {
        "youtube": r'youtube\.com|youtu\.be',
        "tiktok": r'tiktok\.com',
        "instagram": r'instagram\.com',
        "facebook": r'facebook\.com',
        "twitter": r'twitter\.com|x\.com',
        "reddit": r'reddit\.com',
        "pinterest": r'pinterest\.com',
        "vimeo": r'vimeo\.com',
        "dailymotion": r'dailymotion\.com',
        "twitch": r'twitch\.tv'

     }
    for key, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return key
    return "google"

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    platform = context.user_data.get('platform')
    if not platform:
        await update.message.reply_text("اختر المنصة اولا")
        return
    detected = detect_platform(url)
    if detected != platform and platform != "google":
        await update.message.reply_text(f"الرابط من {detected} وليس {platform}")
        return
    await u
pmessage.reply_text(f"جاري تحميل الفيديو...")

def main():
    app = Application.builder().token(HASSAN_7).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_platform, pattern="^p_"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^b$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    logger.info("البوت جاهز")
    app.run_polling()

if __name__ == "__main__":
    main()
