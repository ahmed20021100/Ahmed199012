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
    "tiktok": "تيك توك (TikTok)",
    "instagram": "انستغرام (Instagram)",
    "twitter": "تويتر / X",
    "facebook": "فيسبوك (Facebook)",
    "reddit": "ريديت (Reddit)",
    "pinterest": "بينتريست (Pinterest)",
    "snapchat": "سناب شات (Snapchat)",
    "vimeo": "فيميو (Vimeo)",
    "likee": "لاي
ك: "يوتيوب (YouTube)",
    "other": "رابط آخر (أي موقع)"
}

# ===== حدود الحجم =====
MAX_VIDEO_MB = 2000  # 2 جيجابايت للفيديو (كملف)
MAX_AUDIO_MB = 100   # 100 ميجابايت للصوت

# ===== بيانات المستخدمين =====
user_data = {}
user_activity = {}
command_usage = {}
user_selected_platform = {}
user_pending_link = {}
user_queues = {}

# ===== رسائل ترحيبية =====
WELCOME_MESSAGES = [
    "اهلاً بك! جاهز لتحميل فيديوهاتك؟",

     "مرحباً! اختر المنصة وابعث الرابط",
    "اهلاً! انا هنا لأساعدك في تحميل الفيديوهات",
    "مرحباً! جرب البوت الآن واحصل على فيديوهاتك بجودة عالية",
    "اهلاً بك! معي تقدر تحمل فيديوهات من كل المنصات"
]

# ===== تحميل البيانات =====
def load_data():
    global user_data, user_activity, command_usage
    try:
        with open('user_data.json', 'r', encoding='utf-8') as f:
            user_data = json.load(f)
   
 :
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
        time.sleep(300)
        save_data
(ry, max_age_minutes=30):
    try:
        now = time.time()
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
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
def detect_platform(url):
    url_lower = url.lower()
    if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
        return "tiktok"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "facebook.com" in url_lower or "fb.com" in url_lower or "fb.wa
t in url_lower or "redd.it" in url_lower:
        return "reddit"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "pinterest"
    elif "snapchat.com" in url_lower:
        return "snapchat"
    elif "vimeo.com" in url_lower:
        return "vimeo"
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
    keyboard = []
    for key, label in PLATFORMS.items():
        keyboard.append([InlineKeyboardButton(label, callback_data=key)])
    keyboard.append([InlineKeyboardButton("لوحة التحكم", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

def get_available_qualities(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    try:
 
 ) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return None
    except Exception as e:
        logging.error(f"خطأ في فحص الجودات: {e}")
        return None

    formats = info.get("formats") or []
    
    heights = set()
    has_audio_only = False
    has_video_only = False
    qualities = []
    
    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        ext = f.get("ext", "mp4")
        
        if vcodec not in (None, "none") and acodec not in (None, "none"):
            if height:
                heights.add(int(height))

                 qualities.append({
                    "height": int(height),
                    "ext": ext,
                    "format": f
                })
        
        if vcodec in (None, "none") and acodec not in (None, "none"):
            has_audio_only = True
        
        if vcodec not in (None, "none") and acodec in (None, "none"):
            has_video_only = True

    options = []

    options.append({
        "label": "افضل جودة متاحة",
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "audio_only": False
    })

    for h in sorted(heights, reverse=True)[:4]:
        if h >= 1080:
            label = 
f 720:
            label = f"{h}p (HD)"
        else:
            label = f"{h}p"
        
        options.append({
            "label": label,
            "format": f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]",
            "audio_only": False
        })

    if has_video_only:
        options.append({
            "label": "فيديو فقط (بدون صوت)",
            "format": "bestvideo[ext=mp4]",
            "audio_only": False
        })

    if has_audio_only:
        options.append({
            "label": "صوت فقط (MP3) - جودة عالية",
            "format": "bestaudio/best",
            "audio_only": True
        })
        options.append({
            "label": "صوت فقط (MP3) - جودة منخفضة",

             "format": "bestaudio[abr<=64]",
            "audio_only": True
        })

    formats_available = set()
    for f in formats:
        ext = f.get("ext")
        if ext and ext not in ["mp4", "m4a", "webm"]:
            formats_available.add(ext)
    
    for ext in formats_available:
        options.append({
            "label": f"صيغة {ext.upper()}",
            "format": f"best[ext={ext}]",
            "audio_only": False
        })

    return options

def download_video(url, output_dir, format_spec="best[ext=mp4]/best", audio_only=False):
    try:
        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
        ydl_opts = {
            "outtmpl": output_template,
            "format"
:          "no_warnings": True,
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
                filename = os.path.splitext(filename)[0] + ".mp3"

             
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
    except Exception as e:
        logging.error(f"خطأ في التحميل: {e}")
    return None

# ===== دوال البوت =====
async def start(update, context):
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
  
 e_msg = random.choice(WELCOME_MESSAGES)
    await update.message.reply_text(
        f"{welcome_msg}\n\nاختر المنصة التي تريد التحميل منها:",
        reply_markup=get_platforms_keyboard()
    )

async def start_callback(query, context):
    log_user_activity(query.from_user.id, "home")
    await query.message.delete()
    await query.message.reply_text(
        "القائمة الرئيسية\n\nاختر المنصة:",
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

    stats_text = f"احصائيات البوت\n\n"
    stats_text += f"اجمالي المستخدمين: {total_users}\n"
    stats_text += f"نشط اليوم: {active_today}\n"
    stats_text += f"نشط الاسبوع: {active_week}\n"
    stats_text += f"نشط الشهر: {active_month}\n\n"

    sorted_commands = sorted(command_usage.items(), key=lambda x: x[1], reverse=True)[:5]
    stats_text += "المنصات الاكثر استخداماً:\n"
    for cmd, count in sorted_commands:
        platform_name = PLATFORMS.get(cmd, cmd)
        stats_text += f"- {platform_name}: {count} مرة\n"

    await message.reply_text(stats_text)

async def users_callback(message, context):
    users_list = list(user_data.values())
    users_list.re
v"
    for i, user in enumerate(users_list, 1):
        name = user.get('first_name', 'غير معروف')
        username = user.get('username', '')
        added = user.get('added_date', '')
        user_id_display = user.get('user_id', '')

        text += f"{i}. {name}\n"
        if username:
            text += f"   @{username}\n"
        text += f"   {added}\n"
        text += f"   {user_id_display}\n\n"

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
        caption="تصدير بيانات المستخدمين"
    )

    os.remove('export_data.json')

async def help_command(update, context):
    await update.message.reply_text(
        "دليل استخدام البوت\n\n"
        "الاوامر الاساسية:\n"
        "/start - عرض القائمة الرئيسية\n"
        "/help - عرض هذه الرسالة\n\n"
        "كيفية الاستخدام:\n"
        "1- اختر المنصة من القائمة\n"
        "2- ارسل رابط الفيديو\n"
        "3- اختر الجودة المناسبة من الخيارات\n"
        "4- انتظر التحميل والارسال\n\n"
        "مميزات البوت:\n"
        "- دعم جميع المنصات المشهورة\n"
        "- خيارات جودة متعددة\n"
        "- تحميل الصوت فقط (MP3)\n"
        "- اكتشاف تلقائي للمنصة\n"
        "- واجهة سهلة الاستخدام\n\n"
        "حدود الحجم:\n"
        f"- فيديو: حتى {MAX_VIDEO_MB} ميجابايت\n"
"
        "ملاحظة:\n"
        "- بعض المنصات قد يكون فيها قيود"

     )

async def buttons(update, context):
    query = update.callback_query
    user_id = int(query.from_user.id)
    await query.answer()

    log_user_activity(user_id, query.data)

    if query.data in PLATFORMS:
        user_selected_platform[user_id] = query.data
        label = PLATFORMS[query.data]
        
        await query.message.delete()
        await query.message.reply_text(
            f"تم اختيار: {label}\n\nالان ارسل رابط الفيديو المطلوب تحميله:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
            ])
        )

    elif query.data.startswith("q_"):
        await quality_chosen(query, context, user_id)

    elif query.data == "home":
        await start_callback(query, context)

    elif query.data == "admin_panel":
        if user_id != ADMIN_ID:
            await query.message.reply_text("هذا الخيار خاص بالمطور فقط.")
            return

        admi
noard = [
            [InlineKeyboardButton("الاحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("تصدير البيانات", callback_data="admin_export")],
            [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
        ]

        await query.message.delete()
        await query.message.reply_text(
            "لوحة التحكم\n\nاختر أحد الخيارات:",
            reply_markup=InlineKeyboardMarkup(admin_keyboard)
        )

    elif query.data == "admin_stats":
        await stats_callback(query.message, context)

    elif query.data == "admin_users":
        await users_callback(query.message, context)

    elif query.data == "admin_export":
        await export_callback(query.message, context)

async def handle_link(update, context):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if not text.startswith(("http://", "https://")):

         await update.message.reply_text(
            "الرجاء ارسال رابط صحيح يبدأ بـ http:// او https://",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
            ])
        )
        return

    detected_platform = detect_platform(text)
    platform_label = PLATFORMS.get(detected_platform, "منصة غير معروفة")
    
    if detected_platform in PLATFORMS:
        user_selected_platform[user_id] = detected_platform
        await update.message.reply_text(
            f"تم كشف المنصة تلقائياً: {platform_label}"
        )
    else:
        if user_id not in user_selected_platform:
            await update.message.reply_text(
                "لم نتمكن من كشف المنصة تلقائياً\nالرجاء اختيار المنصة من القائمة:",
                reply_markup=get_platforms_keyboard()
            )
            return

    checking_msg = await update.message.reply_text("جاري فحص الجودات المتاحة...")

    options = get_available_
q   await checking_msg.edit_text(
            "ما قدرت اوصل للفيديو\nتأكد من:\n- الرابط صحيح\n- المحتوى غير محمي او خاص\n- المنصة مدعومة",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
            ])
        )
        return

    user_pending_link[user_id] = {"url": text, "options": options}

    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(opt["label"], callback_data=f"q_{i}")])
    
    keyboard.append([
        InlineKeyboardButton("رجوع للقائمة", callback_data="home"),
        InlineKeyboardButton("تحميل من جديد", callback_data="home")
    ])

    await checking_msg.edit_text(
        "اختر الجودة المطلوبة:\n\n" + f"الرابط: {text[:50]}...",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def quality_chosen(query, context, user_id):
    pending = user_pending_link.get(user_id)
    if not pending:
        await query.message.edit_text(
            "انتهت صلاحية هذا الطلب\nالرجاء ارسال الرابط من جديد",

             reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
            ])
        )
        return

    try:
        idx = int(query.data.split("_", 1)[1])
        option = pending["options"][idx]
    except (ValueError, IndexError):
        await query.message.reply_text("خيار غير صحيح، جرب من جديد.")
        return

    url = pending["url"]
    audio_only = option.get("audio_only", False)
    format_spec = option.get("format", "best[ext=mp4]/best")

    await query.message.delete()
    
    status_msg = await query.message.reply_text("جاري التحميل...\n\nالرجاء الانتظار...")
    
    tmp_dir = tempfile.mkdtemp(prefix="vid_")

    try:
        file_path = download_video(url, tmp_dir, format_spec=format_spec, audio_only=audio_only)

        if file_path is None:
            await status_msg.edit_text(
                "ما قدرت احمل بهذي الجودة\nجرب جودة اخرى او تأكد من الرابط",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("جودة اخرى", cal
lKeyboardButton("رجوع للقائمة", callback_data="home")]
                ])
            )
            return

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # تحديد الحد حسب نوع الملف
        if audio_only:
            max_limit = MAX_AUDIO_MB
            file_type = "صوت"
        else:
            max_limit = MAX_VIDEO_MB
            file_type = "فيديو"
        
        if size_mb > max_limit:
            await status_msg.edit_text(
                f"حجم الملف كبير جداً\n"
                f"الحجم: {size_mb:.1f} MB\n"
                f"الحد الاقصى لـ {file_type}: {max_limit} MB\n\n"
                f"جرب جودة اقل",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("جودة اخرى", callback_data="home")],
                    [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
                ])
            )
            return

        await status_msg.edit_text(f"تم التحميل ({size_mb:.1f} MB)، جاري الارسال...")
        
        # إرسال الملف
        with open(file_path, "rb") as file:
            if audio_only:
                # إرسال الصوت كملف صوتي

                 await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=file,
                    title=f"صوت من {PLATFORMS.get(user_selected_platform.get(user_id, 'رابط'), '')}",
                    performer="تم التحميل بواسطة البوت",
                    duration=0  # سيتم كشف المدة تلقائياً
                )
            else:
                # إرسال الفيديو كملف (يدعم حتى 2 جيجابايت)
                # استخدم send_document لتجاوز حد 50 ميجا
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=file,
                    filename=os.path.basename(file_path),
                    caption=f"✅ تم التحميل بنجاح!\n"
                            f"📦 الحجم: {size_mb:.1f} MB\n"
                            f"📎 للرجوع للقائمة استخدم /start"
                )
        
        await status_msg.delete()
        
        await query.message.reply_text(
            "✅ تم الارسال بنجاح!\n\n"
            "📌 اختر منصة جديدة او ارسل رابط اخر",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboar
dhome")]
            ])
        )

    except Exception as e:
        logging.error(f"خطأ اثناء المعالجة: {e}")
        await status_msg.edit_text(
            f"❌ صار خطأ: {str(e)[:200]}\n\nجرب من جديد او اختر جودة اخرى",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("رجوع للقائمة", callback_data="home")]
            ])
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        user_pending_link.pop(user_id, None)

# ===== تسجيل الأوامر =====
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CallbackQueryHandler(buttons))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

# ===== تشغيل البوت =====
def main():
    save_thread = threading.Thread(target=auto_save, daemon=True)
    save_thread.start()
    
    def cleanup_thread():
        while True:
            time.sleep(3600)
            try:
                temp_dir = tempfile.gettempdir()
                cleanup_old_files(temp_dir, 30)
            except Exception as e:
                logging.error(f"خطأ في تنظيف الملفات: {e}")
    
    cleanup = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup.start()
    
    print("🚀 البوت شغال...")
    print(f"👤 معرف الادمن: {ADMIN_ID}")
    print(f"📊 عدد المنصات المدعومة: {len(PLATFORMS)}")
    print(f"📹 حد الفيديو: {MAX_VIDEO_MB} MB")
    print(f"🎵 حد الصوت: {MAX_AUDIO_MB} MB")
    
    application.run_polling()

if __name__ == "__main__":
    main()
