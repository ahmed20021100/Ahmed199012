from pyrogram import Client, filters
import json
import asyncio

# ===== البيانات المطلوبة =====
API_ID = 39001664
API_HASH = "2fcd5c353777e4a297df4797e662c379"

app_data = {
    'message': '',
    'groups': [],
    'is_running': False
}

def load_data():
    global app_data
    try:
        with open('spammer.json', 'r', encoding='utf-8') as f:
            app_data = json.load(f)
    except:
        app_data = {'message': '', 'groups': [], 'is_running': False}

def save_data():
    with open('spammer.json', 'w', encoding='utf-8') as f:
        json.dump(app_data, f, ensure_ascii=False, indent=2)

load_data()

# إنشاء Client (حسابك الشخصي)
client = Client("my_account", api_id=API_ID, api_hash=API_HASH)

sender_task = None

async def send_messages():
    """إرسال الرسالة كل دقيقة"""
    await asyncio.sleep(5)
    
    while app_data['is_running']:
        try:
            if app_data['message'] and app_data['groups']:
                for group in app_data['groups']:
                    try:
                        await client.send_message(group, app_data['message'])
                        print(f"✅ تم الإرسال إلى: {group}")
                    except Exception as e:
                        print(f"❌ خطأ {group}: {e}")
        except Exception as e:
            print(f"❌ خطأ: {e}")
        
        await asyncio.sleep(60)

@client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    text = (
        "🤖 مرحبا!\n\n"
        "الأوامر:\n"
        "/set_msg - اكتب الرسالة\n"
        "/add_group - أضيف كروب\n"
        "/list - عرض الكروبات\n"
        "/send - ابدأ الإرسال\n"
        "/stop - أوقف الإرسال\n"
    )
    await message.reply(text)

@client.on_message(filters.command("set_msg") & filters.private)
async def set_message(client, message):
    await message.reply("اكتب الرسالة (reply على هذه الرسالة):")

@client.on_message(filters.command("add_group") & filters.private)
async def add_group(client, message):
    await message.reply("اكتب معرف الكروب:\n@group_name\nأو\n-1001234567890")

@client.on_message(filters.command("list") & filters.private)
async def list_groups(client, message):
    if not app_data['groups']:
        await message.reply("لا توجد كروبات!")
        return
    
    text = "الكروبات:\n\n"
    for i, g in enumerate(app_data['groups'], 1):
        text += f"{i}. {g}\n"
    
    await message.reply(text)

@client.on_message(filters.command("send") & filters.private)
async def start_sending(client, message):
    global sender_task
    
    if not app_data['message']:
        await message.reply("اكتب الرسالة أولاً!")
        return
    if not app_data['groups']:
        await message.reply("أضيف كروبات أولاً!")
        return
    if app_data['is_running']:
        await message.reply("البوت يعمل بالفعل!")
        return
    
    app_data['is_running'] = True
    save_data()
    
    sender_task = asyncio.create_task(send_messages())
    await message.reply(f"✅ بدأ الإرسال!\n\nعدد الكروبات: {len(app_data['groups'])}")
    print("✅ بدأ الإرسال")

@client.on_message(filters.command("stop") & filters.private)
async def stop_sending(client, message):
    global sender_task
    
    app_data['is_running'] = False
    save_data()
    
    if sender_task:
        sender_task.cancel()
        sender_task = None
    
    await message.reply("⏹️ توقف الإرسال!")
    print("⏹️ توقف الإرسال")

@client.on_message(filters.text & filters.private & ~filters.command)
async def text_handler(client, message):
    if not message.reply_to_message_id:
        return
    
    # الحصول على الرسالة المرد عليها
    replied = await client.get_messages(message.chat.id, message.reply_to_message_id)
    
    # إذا كان الرد على "اكتب الرسالة"
    if "اكتب الرسالة" in replied.text:
        app_data['message'] = message.text
        save_data()
        await message.reply(f"✅ تم حفظ الرسالة!\n\n{app_data['message']}")
        print(f"✅ رسالة محفوظة: {app_data['message'][:50]}")
    
    # إذا كان الرد على "اكتب معرف الكروب"
    elif "معرف الكروب" in replied.text:
        group = message.text
        
        if group not in app_data['groups']:
            app_data['groups'].append(group)
            save_data()
            await message.reply(f"✅ تم إضافة: {group}")
            print(f"✅ كروب مضاف: {group}")
        else:
            await message.reply("هذا الكروب موجود بالفعل!")

def main():
    print("=" * 50)
    print("🤖 بوت الحساب الشخصي - شغال!")
    print("=" * 50)
    print("أول تشغيل:")
    print("1. أدخل رقم الهاتف")
    print("2. أدخل كود التحقق")
    print("=" * 50)
    client.run()

if __name__ == "__main__":
    main()
