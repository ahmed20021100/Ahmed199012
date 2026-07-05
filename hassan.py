import os
import logging
import tempfile
import shutil
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import yt_dlp

# ---------------------------------------------------------------------------
# إعدادات عامة
# ---------------------------------------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# التوكن يُقرأ من متغير البيئة فقط - لا تكتبه هنا أبداً
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "لم يتم العثور على BOT_TOKEN في متغيرات البيئة. "
        "أضفه من إعدادات Railway (Variables) أو ملف .env محلياً."
    )

# حد أقصى لحجم الفيديو الذي يرسله تيليجرام (بالميجابايت) للبوتات العادية
MAX_TELEGRAM_MB = 50

# قائمة المنصات (10 منصات + خيار عام رقم 11)
PLATFORMS = {
    "youtube": "▶️ يوتيوب (YouTube)",
    "tiktok": "🎵 تيك توك (TikTok)",
    "instagram": "📸 انستغرام (Instagram)",
    "twitter": "🐦 تويتر / X",
    "facebook": "📘 فيسبوك (Facebook)",
    "reddit": "👽 ريديت (Reddit)",
    "pinterest": "📌 بينتريست (Pinterest)",
    "snapchat": "👻 سناب شات (Snapchat)",
    "vimeo": "🎬 فيميو (Vimeo)",
    "likee": "💫 لايكي (Likee)",
    "other": "🌐 رابط آخر (أي موقع / Google Chrome)",
}

# نتذكر أي منصة اختار كل مستخدم مؤقتاً (بالذاكرة، بسيط بدون قاعدة بيانات)
user_selected_platform: dict[int, str] = {}


# ---------------------------------------------------------------------------
# أوامر البوت
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(label, callback_data=key)]
        for key, label in PLATFORMS.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "أهلاً بيك! اختر المنصة الي تريد تحمل منها الفيديو:",
        reply_markup=reply_markup,
    )


async def platform_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    platform_key = query.data
    user_id = query.from_user.id
    user_selected_platform[user_id] = platform_key

    label = PLATFORMS.get(platform_key, "هذه المنصة")
    await query.edit_message_text(
        f"تمام، اخترت: {label}\n\n"
        "الحين ابعثلي رابط الفيديو وراح أسحبه لك."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if not text.startswith("http"):
        await update.message.reply_text("ابعث رابط صحيح يبدأ بـ http أو https 🙏")
        return

    platform = user_selected_platform.get(user_id, "other")
    status_msg = await update.message.reply_text("⏳ جاري تحميل الفيديو...")

    tmp_dir = tempfile.mkdtemp(prefix="vid_")
    try:
        file_path = download_video(text, tmp_dir)

        if file_path is None:
            await status_msg.edit_text(
                "ما قدرت أحمل الفيديو 😕\n"
                "تأكد إن الرابط صحيح، أو إن المحتوى مو خاص/محمي بحساب مغلق."
            )
            return

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_TELEGRAM_MB:
            await status_msg.edit_text(
                f"الفيديو حجمه {size_mb:.1f} MB وهذا أكبر من حد تيليجرام "
                f"للبوتات العادية ({MAX_TELEGRAM_MB} MB). جرب رابط بجودة أقل."
            )
            return

        await status_msg.edit_text("✅ تم التحميل، جاري الإرسال...")
        with open(file_path, "rb") as video_file:
            await update.message.reply_video(video=video_file)
        await status_msg.delete()

    except Exception as exc:  # noqa: BLE001
        logger.exception("خطأ أثناء تحميل الفيديو")
        await status_msg.edit_text(f"صار خطأ: {exc}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# منطق التحميل عبر yt-dlp
# ---------------------------------------------------------------------------

def download_video(url: str, output_dir: str) -> str | None:
    """
    يحمل الفيديو من الرابط المعطى باستخدام yt-dlp ويرجع مسار الملف.
    yt-dlp يدعم تلقائياً أغلب المنصات (يوتيوب، تيك توك، تويتر، فيسبوك،
    ريديت، بينتريست، فيميو ...). انستغرام وسناب شات أحياناً يحتاجون
    كوكيز حساب مسجّل دخول للمحتوى الخاص - راجع تعليمات yt-dlp للكوكيز
    إذا واجهت مشاكل بمحتوى معين.
    """
    output_template = str(Path(output_dir) / "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": MAX_TELEGRAM_MB * 1024 * 1024 * 2,  # هامش قبل الفحص اليدوي
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if os.path.exists(filename):
            return filename
        return None


# ---------------------------------------------------------------------------
# نقطة التشغيل
# ---------------------------------------------------------------------------

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(platform_chosen))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    logger.info("البوت شغال...")
    application.run_polling()


if __name__ == "__main__":
    main()
