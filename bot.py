from pyrogram import Client, filters
import json
import asyncio

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

client = Client("my_account", api_id=API_ID, api_hash=API_HASH)

sender_task = None

async def send_messages():
    await asyncio.sleep(5)
    
    while app_data['is_running']:
        try:
            if app_data['message'] and app_data['groups']:
                for group in app_data['groups']:
                    try:
                        await client.send_message(group, app_data['message'])
                        print(f"OK: {group}")
                    except Exception as e:
                        print(f"ERROR {group}: {e}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        await asyncio.sleep(60)

@client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    text = "/set_msg\n/add_group\n/list\n/send\n/stop"
    await message.reply(text)

@client.on_message(filters.command("set_msg") & filters.private)
async def set_msg(client, message):
    await message.reply("Reply with message:")

@client.on_message(filters.command("add_group") & filters.private)
async def add_grp(client, message):
    await message.reply("Reply with group:\n@name or -100123")

@client.on_message(filters.command("list") & filters.private)
async def lst(client, message):
    if not app_data['groups']:
        await message.reply("No groups")
        return
    text = "\n".join([f"{i}. {g}" for i, g in enumerate(app_data['groups'], 1)])
    await message.reply(text)

@client.on_message(filters.command("send") & filters.private)
async def snd(client, message):
    global sender_task
    
    if not app_data['message']:
        await message.reply("Set message first")
        return
    if not app_data['groups']:
        await message.reply("Add groups first")
        return
    if app_data['is_running']:
        await message.reply("Running")
        return
    
    app_data['is_running'] = True
    save_data()
    sender_task = asyncio.create_task(send_messages())
    await message.reply(f"Started {len(app_data['groups'])} groups")
    print("STARTED")

@client.on_message(filters.command("stop") & filters.private)
async def stp(client, message):
    global sender_task
    
    app_data['is_running'] = False
    save_data()
    
    if sender_task:
        sender_task.cancel()
        sender_task = None
    
    await message.reply("Stopped")
    print("STOPPED")

@client.on_message(filters.private)
async def txt_handler(client, message):
    if message.text.startswith('/'):
        return
    
    if not message.reply_to_message_id:
        return
    
    try:
        replied = await client.get_messages(message.chat.id, message.reply_to_message_id)
        
        if "Reply with message" in replied.text:
            app_data['message'] = message.text
            save_data()
            await message.reply(f"OK: {app_data['message']}")
        
        elif "Reply with group" in replied.text:
            group = message.text
            if group not in app_data['groups']:
                app_data['groups'].append(group)
                save_data()
                await message.reply(f"Added: {group}")
            else:
                await message.reply("Exists")
    except:
        pass

def main():
    print("BOT STARTED")
    client.run()

if __name__ == "__main__":
    main()
