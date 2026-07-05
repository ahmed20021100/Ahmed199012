import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta
import json
import os
import tempfile
import shutil
import random
import threading
import time
import re
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")


 # ===== معرف الأدمن =====
ADMIN_ID = 1025310531

# ===== المنصات المدعومة =====
PLATFORMS = {
    "tiktok": "🎵 تيك توك (TikTok)",
    "instagram": "📸 انستغرام (Instagram)",
    "twitter": "🐦 تويتر / X",
    "facebook": "📘 فيسبوك (Facebook)",
    "reddit": "👽 ريديت (Reddit)",
    "pinterest": "📌 بينتريست (Pinterest)",
    "snapchat": "👻 سناب شات (Snapchat)",
    "vimeo": "🎬 فيميو (Vi
mيكي (Likee)",
    "youtube": "▶️ يوتيوب (YouTube)",
    "other": "🌐 رابط آخر (أي موقع)"
}

MAX_TELEGRAM_MB = 50

# ===== بيانات المستخدمين =====
user_data = {}
user_activity = {}
command_usage = {}
user_selected_platform = {}
user_pending_link = {}
user_queues = {}

# ===== رسائل ترحيبية =====
WELCOME_MESSAGES = [
    "🎬 أهلاً بك! جاهز لتحميل فيديوهاتك؟",
    "📹 مرحباً! اختر المنصة وابعث الرابط",
    "🎥 أهلاً! أنا هنا لأساعدك في تحميل الفيديوهات",

     "✨ مرحباً! جرب البوت الآن واحصل على فيديوهاتك بجودة عالية",
    "🚀 أهلاً بك! معي تقدر تحمل فيديوهات من كل المنصات"
]

# ===== تحميل البيانات =====
def load_data():
    global user_data, user_activity, command_usage
    try:
        with open('user_data.json', 'r', encoding='utf-8') as f:
            user_data = json.load(f)
    except:
        user_data = {}

    try:
        with open('user_activity.json', 'r', encoding='utf-8') as f:
           
 = {}

    try:
        with open('command_usage.json', 'r', encoding='utf-8') as f:
            command_usage = json.load(f)
    except:
        command_usage = {}

def save_data():
    try:
        with open('user_data.json', 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        with open('user_activity.json', 'w', encoding='utf-8') as f:
            json.dump(user_activity, f, ensure_ascii=False, indent=2)
        with open('command_usage.json', 'w', encoding='utf-8') as f:

             json.dump(command_usage, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"خطأ في حفظ البيانات: {e}")

load_data()

# ===== Auto Save =====
def auto_save():
    while True:
        time.sleep(300)  # كل 5 دقائق
        save_data()

# ===== تنظيف الملفات القديمة =====
def cleanup_old_files(directory: str, max_age_minutes: int = 30):
    """يحذف الملفات الأقدم من المدة المحددة"""
    try:
        now = time.time()
        for filename in os.listdir(directory):
            filepath 
=path):
                file_age = (now - os.path.getctime(filepath)) / 60
                if file_age > max_age_minutes:
                    os.remove(filepath)
                    logging.info(f"تم حذف ملف قديم: {filename}")
    except Exception as e:
        logging.error(f"خطأ في تنظيف الملفات: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

application = Application.builder().token(TOKEN).build()

# ===== دوال مساعدة =====
def detect_platform(url: str) -> str:
    """يكتشف المنصة من الرابط تلقائياً"""
    url_lower = url.lower()

     if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
        return "tiktok"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "facebook.com" in url_lower or "fb.com" in url_lower or "fb.watch" in url_lower:
        return "facebook"
    elif "reddit.com" in url_lower or "redd.it" in url_lower:
        return "reddit"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "pinterest"
    elif "snapchat.com" in url_lower:
        re
t"vimeo"
    elif "likee.com" in url_lower or "likee.video" in url_lower:
        return "likee"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    else:
        return "other"

def log_user_activity(user_id, command):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_activity[str(user_id)] = now
    if command not in command_usage:
        command_usage[command] = 0
    command_usage[command] += 1
    save_data()

def get_platforms_keyboard():
    keyboard = [
        [InlineKeyboardButton(label, callback_data=key)]
        for key, label in PLATFORMS.items()
    ]
    # إضافة زر للمطور
    keyboard.append([InlineKeyboardButton("⚙️ لوحة التحكم", callback_data="admin_panel")])

     return InlineKeyboardMarkup(keyboard)

def get_available_qualities(url: str):
    """
    يفحص الرابط ويرجع قائمة جودات فيديو متاحة
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return None
    except Exception as e:
        logging.error(f"خطأ في فحص الجودات: {e}")
        return None

    formats = info.get("formats") or []
    
    # نجمع الارتفاعات المتوفرة
    heights = set()
    has_audio_only = False
    has_video_only = False
    qualities 
=ight = f.get("height")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        ext = f.get("ext", "mp4")
        
        # فيديو مع صوت
        if vcodec not in (None, "none") and acodec not in (None, "none"):
            if height:
                heights.add(int(height))
                qualities.append({
                    "height": int(height),
                    "ext": ext,
                    "format": f
                })
        
        # صوت فقط
        if vcodec in (None, "none") and acodec not in (None, "none"):
            has_audio_only = True
        
        # فيديو فقط
        if vcodec not in (None, "none") and acodec in (None, "none"):
            has_video_only = True

    options = []

    # أفضل جودة
    options.append({
        "label": "⭐ أفضل جودة متاحة",

         "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "audio_only": False
    })

    # جودات متوسطة وعالية
    for h in sorted(heights, reverse=True)[:4]:
        if h >= 1080:
            label = f"🎬 {h}p (Full HD)"
        elif h >= 720:
            label = f"🎬 {h}p (HD)"
        else:
            label = f"🎬 {h}p"
        
        options.append({
            "label": label,
            "format": f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]",
            "audio_only": False
        })

    # فيديو فقط (بدون صوت) - إذا كان متاح
    if has_video_only:
        options.append({
            "label": "🎥 فيديو فقط (بدون صوت)",
            "format": "bestvideo[ext=mp4]",
            "audio_only": False
        })

    # صوت فقط
    if has_audio
_عالية",
            "format": "bestaudio/best",
            "audio_only": True
        })
        options.append({
            "label": "🎵 صوت فقط (MP3) - جودة منخفضة",
            "format": "bestaudio[abr<=64]",
            "audio_only": True
        })

    # صيغ أخرى
    formats_available = set()
    for f in formats:
        ext = f.get("ext")
        if ext and ext not in ["mp4", "m4a", "webm"]:
            formats_available.add(ext)
    
    for ext in formats_available:
        options.append({
            "label": f"📁 صيغة {ext.upper()}",
            "format": f"best[ext={ext}]",
            "audio_only": False
        })

    return options

def download_video(url: str, output_dir: str, format_spec: str = "best[ext=mp4]/best", audio_only: bool = False):
    """يحمل الفيديو/الصوت حسب الصيغة المطلوبة"""
    try:
        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

         ydl_opts = {
            "outtmpl": output_template,
            "format": format_spec,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "ignoreerrors": True,
            "nooverwrites": True,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "timeout": 30,
        }
        
        if audio_only:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                return None
            
            filename = ydl.prepare_filename(info)
            if audio_only:
                filename = os.path
.] + ".mp3"
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
    except Exception as e:
        logging.error(f"خطأ في التحميل: {e}")
    return None

# ===== دوال البوت =====
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
    
    welcome_msg = random.choice(WELCOME_MESSAGES)
    await update.message.reply_text(

         f"{welcome_msg}\n\n"
        "اختر المنصة التي تريد التحميل منها:",
        reply_markup=get_platforms_keyboard()
    )

async def start_callback(query, context):
    log_user_activity(query.from_user.id, "home")
    await query.message.delete()
    await query.message.reply_text(
        "🏠 القائمة الرئيسية\n\nاختر المنصة:",
        reply_markup=get_platforms_keyboard()
    )
    await query.answer()

async def stats_callback(message, context):
    total_users = len(user_data)

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    active_today = sum(1 for u in user_activity.values() if u.startswith(today))
    active_week = sum(1 for u in user_activity.values() if u >= week_ago)
    active_month = sum(1 for u in user_activity.values() if u >= month_ago)

    stats_text = f"📊 **إحصائيا
ت += f"👥 **إجمالي المستخدمين:** {total_users}\n"
    stats_text += f"🟢 **نشط اليوم:** {active_today}\n"
    stats_text += f"🟡 **نشط الأسبوع:** {active_week}\n"
    stats_text += f"🟠 **نشط الشهر:** {active_month}\n\n"

    sorted_commands = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    stats_text += "📌 **المنصات الأكثر استخداماً:**\n"
    for cmd, count in sorted_commands:
        platform_name = PLATFORMS.get(cmd, cmd)
        stats_text += f"• {platform_name}: {count} مرة\n"

    await message.reply_text(stats_text)

async def users_callback(message, context):
    users_list = list(user_data.values())
    users_list.reverse()
    users_list = users_list[:10]

    text = "👥 **آخر 10 مستخدمين:**\n\n"
    for i, user in enumerate(users_list, 1):
        name = user.get('first_name', 'غير معروف')
        username = user.get('username', '')
        added = user.get('added_date', '')
        user_id_display = user.get('user_id', '')


         text += f"{i}. **{name}**\n"
        if username:
            text += f"   🆔 @{username}\n"
        text += f"   📅 {added}\n"
        text += f"   🆔 {user_id_display}\n\n"

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

    await context.bot.send_document(
        chat_id=message.chat.id,
        document=open('export_data.json', 'rb'),
        filename=f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        caption="📊 **تصدير بيانات المستخدمين**"
    )

    os.remove('export_data.json')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TY
Pext(
        "📖 **دليل استخدام البوت**\n\n"
        "🎯 **الأوامر الأساسية:**\n"
        "/start - عرض القائمة الرئيسية\n"
        "/help - عرض هذه الرسالة\n\n"
        "💡 **كيفية الاستخدام:**\n"
        "1️⃣ اختر المنصة من القائمة\n"
        "2️⃣ أرسل رابط الفيديو\n"
        "3️⃣ اختر الجودة المناسبة من الخيارات\n"
        "4️⃣ انتظر التحميل والإرسال\n\n"
        "🔊 **مميزات البوت:**\n"
        "✅ دعم جميع المنصات المشهورة\n"
        "✅ خيارات جودة متعددة\n"
        "✅ تحميل الصوت فقط (MP3)\n"
        "✅ اكتشاف تلقائي للمنصة\n"
        "✅ واجهة سهلة الاستخدام\n\n"
        "⚠️ **ملاحظة:**\n"
        "• الحد الأقصى للملف 50 ميجابايت\n"
        "• بعض المنصات قد يكون فيها قيود"
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = int(query.from_user.id)
    await query.answer()

    log_user_activity(user_id, query.data)

    # اختيار منصة
    if query.data in PLATFORMS:
        user_selected_platform[user_id] = query.data

         label = PLATFORMS[query.data]
        
        # حذف الرسالة القديمة وإرسال رسالة جديدة
        await query.message.delete()
        await query.message.reply_text(
            f"✅ تم اختيار: {label}\n\n"
            "📎 الآن أرسل رابط الفيديو المطلوب تحميله:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
            ])
        )

    # اختيار الجودة
    elif query.data.startswith("q_"):
        await quality_chosen(query, context, user_id)

    # العودة للقائمة الرئيسية
    elif query.data == "home":
        await start_callback(query, context)

    # لوحة التحكم
    elif query.data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.message.reply_text("⛔ هذا الخيار خاص بالمطور فقط.")
            return

        admin_keyboard = [
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 المستخدمين", callback_data="admin_us
eton("📥 تصدير البيانات", callback_data="admin_export")],
            [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
        ]

        await query.message.delete()
        await query.message.reply_text(
            "⚙️ **لوحة التحكم**\n\nاختر أحد الخيارات:",
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
        )

    elif query.data == "admin_stats":
        await stats_callback(query.message, context)

    elif query.data == "admin_users":
        await users_callback(query.message, context)

    elif query.data == "admin_export":
        await export_callback(query.message, context)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    # تحقق من وجود رابط
    if not text.startswith(("http://", "https://")):
        await update.message.reply_text(
            "❌ الرجاء إرسال رابط صحيح يبدأ بـ http:// أو https://",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]

             ])
        )
        return

    # كشف المنصة تلقائياً
    detected_platform = detect_platform(text)
    platform_label = PLATFORMS.get(detected_platform, "منصة غير معروفة")
    
    if detected_platform in PLATFORMS:
        user_selected_platform[user_id] = detected_platform
        await update.message.reply_text(
            f"🔍 تم كشف المنصة تلقائياً: {platform_label}"
        )
    else:
        if user_id not in user_selected_platform:
            await update.message.reply_text(
                "❌ لم نتمكن من كشف المنصة تلقائياً\n"
                "الرجاء اختيار المنصة من القائمة:",
                reply_markup=get_platforms_keyboard()
            )
            return

    checking_msg = await update.message.reply_text("🔎 جاري فحص الجودات المتاحة...")

    options = get_available_qualities(text)
    if not options:
        await checking_msg.edit_text(
            "😕 ما قدرت أوصل للفيديو\n"
            "تأكد من:\n"
            "• الرابط صحيح\n"
            "• المحتوى غير محمي أو خاص\n"
            "• المنصة مدعومة",
            reply_markup=InlineKeyboardMarkup([
 
 [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
            ])
        )
        return

    user_pending_link[user_id] = {"url": text, "options": options}

    # بناء أزرار الجودات
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(opt["label"], callback_data=f"q_{i}")])
    
    # إضافة أزرار إضافية
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home"),
        InlineKeyboardButton("🔄 تحميل من جديد", callback_data="home")
    ])

    await checking_msg.edit_text(
        "📌 **اختر الجودة المطلوبة:**\n\n"
        f"📎 الرابط: {text[:50]}...",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quality_chosen(query, context, user_id):
    pending = user_pending_link.get(user_id)
    if not pending:
        await query.message.edit_text(
            "⏰ انتهت صلاحية هذا الطلب\n"
            "الرجاء إرسال الرابط من جديد",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
            ])
        )
        return

    try:
        idx = int(query.data.split("_", 1)[1])
        option = pending["options"][idx]
    except (ValueError, IndexError):
        await query.message.reply_text("❌ خيار غير صحيح، جرب من جديد.")
        return

    url = pending["url"]
    audio_only = option.get("audio_only", False)
    format_spec = option.get("format", "best[ext=mp4]/best")

    # حذف رسالة الاختيار
    await query.message.delete()
    
    status_msg = await query.message.reply_text("⏳ جاري التحميل...\n\n🔄 الرجاء الانتظار...")
    
    tmp_dir = tempfile.mkdtemp(prefix="vid_")

    try:
        file_path = download_video(url, tmp_dir, format_spec=format_spec, audio_only=audio_only)

        if file_path is None:
            await status_msg.edit_text(
                "😕 ما قدرت أحمل بهذي الجودة\n"
                "جرب جودة أخرى أو تأكد من الرابط",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 جودة أخرى", callback_data="home")],
                    [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
                ])
            )
            return

        
# التحقق من حجم الملف
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > MAX_TELEGRAM_MB:
            await status_msg.edit_text(
                f"⚠️ حجم الملف كبير جداً\n"
                f"📦 الحجم: {size_mb:.1f} MB\n"
                f"🚫 الحد الأقصى: {MAX_TELEGRAM_MB} MB\n\n"
                "جرب جودة أقل",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 جودة أخرى", callback_data="home")],
                    [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
                ])
            )
            return

        await status_msg.edit_text("✅ تم التحميل، جاري الإرسال...")
        
        # إرسال الملف
        with open(file_path, "rb") as file:
            if audio_only:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file,
                    title=f"صوت من {PLATFORMS.get(user_selected_platform.get(user_id, 'رابط'), '')}",
                    performer="تم التحميل بواسطة البوت"
                )
            else:
                await context.bot.send_video(

                     chat_id=query.message.chat_id,
                    video=file,
                    caption="✅ تم التحميل بنجاح!\n\n📎 للرجوع للقائمة استخدم /start",
                    supports_streaming=True
                )
        
        await status_msg.delete()
        
        # رسالة تأكيد إضافية
        await query.message.reply_text(
            "✅ تم الإرسال بنجاح!\n\n"
            "📌 اختر منصة جديدة أو أرسل رابط آخر",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home")]
            ])
        )

    except Exception as e:
        logging.error(f"خطأ أثناء المعالجة: {e}")
        await status_msg.edit_text(
            f"❌ صار خطأ: {str(e)[:200]}\n\n"
            "جرب من جديد أو اختر جودة أخرى",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="home")]
            ])
        )
    finally:
        # تنظيف الملفات المؤقتة
        shutil.rmtree(tmp_dir, ignore_errors=True)
        user_pending_link.pop(user_id, None)

# ===== تسجيل الأوامر =====
application.add_handler(Comma
nCommandHandler("help", help_command))
application.add_handler(CallbackQueryHandler(buttons))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

# ===== تشغيل البوت =====
def main():
    # بدء auto save في خيط منفصل
    save_thread = threading.Thread(target=auto_save, daemon=True)
    save_thread.start()
    
    # تنظيف الملفات القديمة كل ساعة
    def cleanup_thread():
        while True:
            time.sleep(3600)  # كل ساعة
            try:
                temp_dir = tempfile.gettempdir()
                cleanup_old_files(temp_dir, 30)
            except Exception as e:
                logging.error(f"خطأ في تنظيف الملفات: {e}")
    
    cleanup = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup.start()
    
    print("🚀 البوت شغال...")
    print(f"👤 معرف الأدمن: {ADMIN_ID}")
    print(f"📊 عدد المنصات المدعومة: {len(PLATFORMS)}")
    
    application.run_polling()

if __name__ == "__main__":
    main()
