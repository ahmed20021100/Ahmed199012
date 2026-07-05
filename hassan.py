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


 # ========== المنصات ==========
PLATFORMS = {
    "youtube": "🎬 YouTube",
    "tiktok": "🎵 TikTok",
    "instagram": "📸 Instagram",
    "facebook": "📘 Facebook",
    "twitter": "🐦 Twitter/X",
    "reddit": "🤖 Reddit",
    "pinterest": "📌 Pinterest",
    "vimeo": "🎥 Vimeo",
    "dailymotion": "🎞️ Dailymotion",
    "twitch": "🎮 Twitch",
    "google": "🌐 أي رابط"
}

# ========== الأزرار ==========
def get_buttons():
    buttons = []
    row = []
    for key, name in PLATFORMS.items():
        row.append(I
nck_data=f"plat_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons

# ========== كشف المنصة ==========
def detect_platform(url):
    patterns = {
        "youtube": r'(youtube\.com|youtu\.be)',
        "tiktok": r'(tiktok\.com)',
        "instagram": r'(instagram\.com)',
        "facebook": r'(facebook\.com)',
        "twitter": r'(twitter\.com|x\.com)',
        "reddit": r'(reddit\.com)',
        "pinterest": r'(pinterest\.com)',
        "vimeo": r'(vimeo\.com)',

         "dailymotion": r'(dailymotion\.com)',
        "twitch": r'(twitch\.tv)'
    }
    for key, pattern in patterns.items():
        if re.search(pattern, url, re.IGNORECASE):
            return key
    return "google"

# ========== /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_buttons()
    await update.message.reply_text(
        "🎬 **بوت تحميل الفيديوهات**\n\nاختر المنصة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== اختيار منصة ==========
async def select_platform
(_TYPE):
    query = update.callback_query
    await query.answer()
    
    key = query.data.replace("plat_", "")
    context.user_data['platform'] = key
    name = PLATFORMS.get(key, "غير معروف")
    
    await query.edit_message_text(
        f"✅ تم اختيار: {name}\n\n📤 أرسل الرابط الآن:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]])
    )

# ========== رجوع ==========
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop('platform', None)
    await query.edit_message_text(

         "🎬 **اختر المنصة:**",
        reply_markup=InlineKeyboardMarkup(get_buttons())
    )

# ========== معالجة الرابط ==========
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    platform = context.user_data.get('platform')
    
    if not platform:
        await update.message.reply_text(
            "❌ اختر المنصة أولاً!",
            reply_markup=InlineKeyboardMarkup(get_buttons())
        )
        return
    
    detected = detect_platform(url)
    platform_name = PLATFORMS.get(platform, "غير معروف")
    
    if detected != platform and platform != "google":
RMS.get(detected, "غير معروف")

         await update.message.reply_text(
            f"⚠️ الرابط من {detected_name} وليس {platform_name}\n\n"
            f"📌 اختر المنصة الصحيحة أو استخدم 'أي رابط'"
        )
        return
    
    await update.message.reply_text(
        f"⏳ جاري تحميل الفيديو من {platform_name}...\n\n"
        f"🔗 الرابط: {url[:60]}..."
    )

# ========== تشغيل ==========
def main():
    app = Application.builder().token(HASSAN_7).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_platform, pattern="^plat_"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back$"))
    app.add_handler(MessageHandle
r_url))
    
    logger.info("✅ البوت جاهز!")
    app.run_polling()

if __name__ == "__main__":
    main()
