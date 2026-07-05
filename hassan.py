import os
import logging


# ========== إعدادات التس
ج=logging.INFO)
logger = logging.getLogger(__name__)

# ========== توكن البوت ==========

HASSAN_7 = os.environ.get("HASSAN_7")

if not HASSAN_7:
    logger.error("❌ HASSAN_7 غير
 t(1)

logger.info("✅ تم تحميل التوكن بنجاح")

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters
    logger.info("✅ تم تحم
ي    logger.info("📌 تأكد من تثبيت python-telegram-bot")
    exit(1)

# ========== منصات التحميل ==========
PLATFORMS = {
    "youtube": {"name": "🎬 YouTube"},
    "tiktok": {"name": "🎵 TikTok"},
    "instagram": {"name": "📸 Instagram"},

    "facebook": {"name": "📘 Facebook"},
    "twitter": {"name": "🐦 Twitter/X"},
    "reddit": {"name": "🤖 Reddit"},
    "pinterest": {"name": "📌 Pinterest"},
    "vimeo": {"name": "🎥 Vimeo"},
    "dailymotion": {"name": "🎞️ Dailymotio
n
    "google_chrome": {"name": "🌐 أي رابط"}
}

# ========== إنشاء الأزرار ==========
def get_platform_buttons():
    buttons = []
    row = []
    for key, platform in PLATFORMS.items():
        row.append(InlineKeyboardButton(
            platform["name"],
            callback_data=f"platform_{key}"

        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons

# ========== أمر /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        welcome = """
🎬 **بوت تحميل الف
ياختر المنصة من الأزرار أدناه:
"""
        keyboard = get_platform_buttons()
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"✅ تم إرسال القائمة للمستخدم {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ خطأ في start: {e}")

# ========== اختيار المنصة ==========
async def platform_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        platform_key = query.data.replace("platform_", "")
        platform_name = PLATFORMS.get(platform_key, {}).
get("name", "غير معروف")
        
        context.user_data['selected_platform'] = platform_key
        
        msg = f"✅ تم اختيار: {platform_name}\n\n📤 أرسل رابط الفيديو الآن."
        
        keyboard = [[InlineKeyboardButton("🔙 عودة", callback_data="back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

        
        logger.info(f"✅ المستخدم اختار: {platform_name}")
    except Exception as e:
        logger.error(f"❌ خطأ في platform_selection: {e}")

# ========== العودة للقائمة ==========
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        
        c
oer_data.pop('selected_platform', None)
        
        welcome = "🎬 اختر المنصة التي تريد التحميل منها:"
        keyboard = get_platform_buttons()
        await query.edit_message_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"❌ خطأ في back: {e}")

# ========== معالجة الروابط ==========
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        url = update.message.text.strip()
        selected = context.user_data.get('selected_platform')
        
        if not selected:
            keyboard = get_platform_buttons()
            await update.message.reply_text(
                "❌ الرجاء اختيار المنصة أولاً!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        platform_name = PLATFORMS.get
(, {}).get("name", "غير معروف")
        
        await update.message.reply_text(
            f"⏳ جاري معالجة الرابط من {platform_name}...\n\n"
            f"📌 الرابط: {url[:50]}..."
        )
        
        logger.info(f"✅ المستخدم أرسل رابط: {url[:50]}... من {platform_name}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في handle_url: {e}")
        await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى.")

# ========== التشغيل الرئيسي ==========
def main():
    try:
        logger.info("🚀 بدء تشغيل البوت...")
        
        app = Application.builder().token(HASSAN_7).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(platform_selection, pattern="^platform_"))
        app.add_handler(CallbackQueryHandler(back, pattern="^back$"))
        app.add_handler(MessageHandle
r(filters.TEXT & ~filters.COMMAND, handle_url))
        
        logger.info("✅ البوت جاهز للاستخدام!")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح: {e}")
        exit(1)

if __name__ == "__main__":
    main()
