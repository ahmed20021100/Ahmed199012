import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import asyncio

TOKEN = "8852345354:AAFILybdpOLslQus7acOxqkszjPWwzCYgms"
ADMIN_ID = 1025310531

app_data = {
    'message': '',
    'groups': [],
    'is_running': False
}

def load_data():
    global app_data
    try:
        with open('spammer_config.json', 'r', encoding='utf-8') as f:
            app_data = json.load(f)
    except:
        app_data = {'message': '', 'groups': [], 'is_running': False}

def save_data():
    with open('spammer_config.json', 'w', encoding='utf-8') as f:
        json.dump(app_data, f, ensure_ascii=False, indent=2)

load_data()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

application = None
sender_task = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Admin only!")
        return
    
    keyboard = [
        [InlineKeyboardButton("Set Message", callback_data="set_message")],
        [InlineKeyboardButton("Add Group", callback_data="add_group")],
        [InlineKeyboardButton("Remove Group", callback_data="remove_group")],
        [InlineKeyboardButton("Show List", callback_data="show_list")],
        [InlineKeyboardButton("Start Sending", callback_data="start_sending")],
        [InlineKeyboardButton("Stop Sending", callback_data="stop_sending")],
    ]
    
    status = "STOPPED" if not app_data['is_running'] else "RUNNING"
    msg = app_data['message'][:50] + "..." if len(app_data['message']) > 50 else app_data['message']
    
    await update.message.reply_text(
        f"Status: {status}\nMessage: {msg if msg else 'Not set'}\nGroups: {len(app_data['groups'])}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Send the message:")
    context.user_data['waiting_for'] = 'message'

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Send group ID (@group_name or -1001234567890):")
    context.user_data['waiting_for'] = 'group'

async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not app_data['groups']:
        await query.message.reply_text("No groups!")
        return
    
    keyboard = []
    for idx, group in enumerate(app_data['groups']):
        keyboard.append([InlineKeyboardButton(f"X {group}", callback_data=f"delete_group_{idx}")])
    
    await query.message.reply_text("Delete:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not app_data['groups']:
        await query.message.reply_text("No groups!")
        return
    
    text = "Groups:\n" + "\n".join([f"{i}. {g}" for i, g in enumerate(app_data['groups'], 1)])
    await query.message.reply_text(text)

async def sender_loop():
    """Send message every 60 seconds"""
    while app_data['is_running']:
        try:
            if app_data['message'] and app_data['groups']:
                for group in app_data['groups']:
                    try:
                        await application.bot.send_message(chat_id=group, text=app_data['message'])
                        logger.info(f"Sent to {group}")
                    except Exception as e:
                        logger.error(f"Error {group}: {e}")
        except Exception as e:
            logger.error(f"Sender error: {e}")
        
        await asyncio.sleep(60)

async def start_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sender_task
    query = update.callback_query
    await query.answer()
    
    if not app_data['message']:
        await query.message.reply_text("Set message first!")
        return
    if not app_data['groups']:
        await query.message.reply_text("Add groups first!")
        return
    if app_data['is_running']:
        await query.message.reply_text("Already running!")
        return
    
    app_data['is_running'] = True
    save_data()
    
    sender_task = asyncio.create_task(sender_loop())
    await query.message.reply_text(f"Started! Groups: {len(app_data['groups'])}")
    logger.info("Sender started")

async def stop_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sender_task
    query = update.callback_query
    await query.answer()
    
    if not app_data['is_running']:
        await query.message.reply_text("Already stopped!")
        return
    
    app_data['is_running'] = False
    save_data()
    
    if sender_task:
        sender_task.cancel()
        sender_task = None
    
    await query.message.reply_text("Stopped!")
    logger.info("Sender stopped")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    if context.user_data.get('waiting_for') == 'message':
        app_data['message'] = update.message.text
        save_data()
        await update.message.reply_text("Message saved!")
        context.user_data['waiting_for'] = None
    
    elif context.user_data.get('waiting_for') == 'group':
        group = update.message.text
        if group not in app_data['groups']:
            app_data['groups'].append(group)
            save_data()
            await update.message.reply_text(f"Added: {group}")
        else:
            await update.message.reply_text("Exists!")
        context.user_data['waiting_for'] = None

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("Error!")
        return
    
    await query.answer()
    
    if query.data == "set_message":
        await set_message(update, context)
    elif query.data == "add_group":
        await add_group(update, context)
    elif query.data == "remove_group":
        await remove_group(update, context)
    elif query.data == "show_list":
        await show_list(update, context)
    elif query.data == "start_sending":
        await start_sending(update, context)
    elif query.data == "stop_sending":
        await stop_sending(update, context)
    elif query.data.startswith("delete_group_"):
        idx = int(query.data.split("_")[-1])
        deleted = app_data['groups'].pop(idx)
        save_data()
        await query.message.reply_text(f"Deleted: {deleted}")

def main():
    global application
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(buttons))
    
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot running...")
    application.run_polling()

if __name__ == "__main__":
    main()
