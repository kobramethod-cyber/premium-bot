import os
import asyncio
import threading
import urllib.parse
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
PRIMARY_ADMIN = int(os.environ.get("ADMIN_ID", "0"))

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477
CONTACT_URL = "http://t.me/Provider169_bot"

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col, settings_col, plans_col = db.users, db.settings, db.plans

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- DYNAMIC UTILS ---
async def get_admins():
    data = await settings_col.find_one({"type": "admins"})
    admin_list = data['list'] if data else []
    if PRIMARY_ADMIN not in admin_list: admin_list.append(PRIMARY_ADMIN)
    return admin_list

async def get_fjoins():
    data = await settings_col.find_one({"type": "fjoins"})
    return data['channels'] if data else [{"id": -1003575487358, "link": "https://t.me/+mInAMHlOgIo0Yjg1"}]

async def check_fjoin(user_id):
    channels = await get_fjoins()
    for ch in channels:
        try:
            m = await app.get_chat_member(ch['id'], user_id)
            if m.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]: return False
        except: return False
    return True

async def auto_delete(client, chat_id, message_id):
    await asyncio.sleep(600) # 10 Minutes
    try: await client.delete_messages(chat_id, message_id)
    except: pass

# --- 🚀 START & USER FLOW ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        channels = await get_fjoins()
        btns = [[InlineKeyboardButton("Join channel", url=ch['link'])] for ch in channels]
        btns.append([InlineKeyboardButton("I am joined", callback_data="check_joined")])
        return await message.reply(f"Hello {mention}\n\nYou need to join in my Channel/Group to use me\n\nKindly Please join Channel...", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            try: 
                sent_msg = await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
                await message.reply("⚠️ This file will be deleted automatically after 10 minutes.")
                asyncio.create_task(auto_delete(client, uid, sent_msg.id))
                return
            except: return await message.reply("❌ File not found.")
        return await message.reply("🔒 **This content is for Premium Users only!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}\n\nWelecome to premium bot\n\nPremium ke liye buy premium button tap kare", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")], [InlineKeyboardButton("📞 Contact Admin 📞", url=CONTACT_URL)]]))

# --- 💰 PLANS (EXACT TEXT) ---
@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, cb):
    plans = await plans_col.find().to_list(length=20)
    if not plans:
        default = [{"name":"1 Day","price":30,"days":1},{"name":"7 Days","price":70,"days":7},{"name":"15 Days","price":120,"days":15},{"name":"30 Days","price":200,"days":30}]
        await plans_col.insert_many(default)
        plans = default
    text = (
        "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\nᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ\n────────────────────\n"
        "›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1\n›› 15 Days : ₹120 /$ 1.50\n›› 1 Months : ₹200 /$ 2.50\n\n"
        "❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦\n❐ 𝗉𝖺𝗒𝗍𝗆 • 𝗀𝗉𝖺𝗒 • 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • 𝗎𝗉𝗂 𝖺𝗇𝖽 𝗊𝗋 and binnance\n────────────────────\n"
        "✦ Pʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴏɴᴄᴇ ᴘᴀɪᴅ\n✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ a ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓"
    )
    btns = [[InlineKeyboardButton(f"{p['name']}", callback_data=f"pay_{p['price']}_{p['days']}")] for p in plans]
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

# --- 👑 POWER ADMIN PANEL ---
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message):
    if message.from_user.id not in await get_admins(): return
    btns = [
        [InlineKeyboardButton("📊 Stats", callback_data="mng_stats"), InlineKeyboardButton("📝 Plan Mngr", callback_data="mng_plans")],
        [InlineKeyboardButton("📢 F-Join Mngr", callback_data="mng_fj"), InlineKeyboardButton("👥 Admin Mngr", callback_data="mng_admins")],
        [InlineKeyboardButton("✉️ Broadcast", callback_data="bc_cmd"), InlineKeyboardButton("❌ Close", callback_data="close_admin")]
    ]
    await message.reply("👑 **SUPER ADMIN PANEL**", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"mng_(plans|fj|admins|stats)"))
async def manage_cb(client, cb):
    target = cb.data.split("_")[1]
    if cb.from_user.id not in await get_admins(): return
    if target == "stats":
        total = await users_col.count_documents({})
        prem = await users_col.count_documents({"status": "premium"})
        text = f"📊 **STATS**\nTotal: {total}\nPremium: {prem}"
    elif target == "plans": text = "📝 **PLAN MANAGER**\n`/add_plan Name|Price|Days`"
    elif target == "fj": text = "📢 **F-JOIN MANAGER**\n`/add_fj ID|Link`"
    elif target == "admins": text = "👥 **ADMIN MANAGER**\n`/add_admin ID`"
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]]))

# --- PHOTO & APPROVAL (EXACT 5 BUTTONS) ---
@app.on_message(filters.photo & filters.private)
async def handle_ss(client, message):
    uid = message.from_user.id
    if uid in await get_admins(): return
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 day approve", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day approve", callback_data=f"apr_{uid}_7")],
        [InlineKeyboardButton("15 day approve", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month approve", callback_data=f"apr_{uid}_30")],
        [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]
    ])
    await message.copy(PRIMARY_ADMIN, caption=f"📩 **Payment Proof**\nUser: `{uid}`", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!")

# --- [BAAKI LOGIC SAME] ---
@app.on_callback_query(filters.regex("back_admin"))
async def back_admin_cb(client, cb):
    await admin_panel(client, cb.message)

@app.on_callback_query(filters.regex("close_admin"))
async def close_admin_cb(client, cb):
    await cb.message.delete()

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
