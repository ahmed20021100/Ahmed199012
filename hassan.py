import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HASSAN_7 = os.environ.get("HASSAN_7")

if not HASSAN_7:
    logger.error("HASSAN_7 غير موجود")
    exit(1)

logger.info("تم تحميل التوكن")

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    logger.info("تم تحميل المكتبات")
except Exception as e:
    logger.error(f"خطأ في التحميل: {e}")
    exit(1)

# أمر start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ البوت شغال! مرحباً بك.")

# تشغيل البوت
try:
    app = Application.builder().token(HASSAN_7).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("✅ البوت جاهز!")
    app.run_polling()
except Exception as e:
    logger.error(f"خطأ: {e}")
    exit(1)
