import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import json
import os

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
        app_data = {
            'message': '',
            'groups': [],
            'is_running': False
        }

def save_data():
    with open('spammer_config.json', 'w', encoding='utf-8') as f:
        json.dump(app_data, f, ensure_ascii=False, indent=2)

load_data()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("Error: Admin only!")
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
        f"Bot Status: {status}\nMessage: {msg if msg else 'Not set'}\nGroups: {len(app_data['groups'])}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Send the message you want to send every minute:")
    context.user_data['waiting_for'] = 'message'

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Send the group ID (e.g., @group_name or -1001234567890):")
    context.user_data['waiting_for'] = 'group'

async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not app_data['groups']:
        await query.message.reply_text("No groups!")
        return
    
    keyboard = []
    for idx, group in enumerate(app_data['groups']):
        keyboard.append([InlineKeyboardButton(f"Delete: {group}", callback_data=f"delete_group_{idx}")])
    
    await query.message.reply_text("Choose group to delete:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not app_data['groups']:
        await query.message.reply_text("No groups!")
        return
    
    text = "Groups:\n\n"
    for idx, group in enumerate(app_data['groups'], 1):
        text += f"{idx}. {group}\n"
    
    await query.message.reply_text(text)

async def start_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    if not scheduler.running:
        scheduler.start()
    
    if scheduler.get_job('spam_job'):
        scheduler.remove_job('spam_job')
    
    scheduler.add_job(send_message_to_groups, 'interval', minutes=1, id='spam_job')
    
    await query.message.reply_text(f"Started! Sending to {len(app_data['groups'])} groups every minute.")
    logger.info("Sender started")

async def stop_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not app_data['is_running']:
        await query.message.reply_text("Already stopped!")
        return
    
    app_data['is_running'] = False
    save_data()
    
    if scheduler.get_job('spam_job'):
        scheduler.remove_job('spam_job')
    
    await query.message.reply_text("Stopped!")
    logger.info("Sender stopped")

async def send_message_to_groups():
    if not app_data['is_running'] or not app_data['message'] or not app_data['groups']:
        return
    
    for group in app_data['groups']:
        try:
            await application.bot.send_message(chat_id=group, text=app_data['message'])
            logger.info(f"Sent to: {group}")
        except Exception as e:
            logger.error(f"Error sending to {group}: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        return
    
    if context.user_data.get('waiting_for') == 'message':
        app_data['message'] = update.message.text
        save_data()
        await update.message.reply_text(f"Message saved!")
        context.user_data['waiting_for'] = None
    
    elif context.user_data.get('waiting_for') == 'group':
        group = update.message.text
        
        if group not in app_data['groups']:
            app_data['groups'].append(group)
            save_data()
            await update.message.reply_text(f"Group added: {group}")
        else:
            await update.message.reply_text(f"Group already exists!")
        
        context.user_data['waiting_for'] = None

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.answer("Error!", show_alert=True)
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

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(buttons))

from telegram.ext import MessageHandler, filters
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

def main():
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
