import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Beyond Ultra Max Bot is Online"

def run_flask():
    # Render default port 10000
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION (Bhai, API details my.telegram.org se check karna) ---
API_ID = 25691060 
API_HASH = "8ba2c49611687f1747758376916538c3"
BOT_TOKEN = "7832679234:AAHeOsnEwYh-F0T0C4K_D6N44669866" 
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = 1119812744 # Kartik Nagargoje

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"
FORCE_CHANNEL_ID = -1003575487358

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

app = Client("ultra_max_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def check_fjoin(user_id):
    try:
        m = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return m.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except: return False

async def auto_delete(client, chat_id, message_id):
    await asyncio.sleep(600) # 10 Mins
    try: await client.delete_messages(chat_id, message_id)
    except: pass

# --- 🔄 GLOBAL CHECKER (EXPIRY & 1H REMINDERS) ---
async def global_checker():
    while True:
        try:
            now = datetime.now()
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                try: await app.send_message(uid, "❗ Your premium has expired. Renew now!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 RENEW", callback_data="buy_plans")]]))
                except: pass
        except: pass
        await asyncio.sleep(600)

# --- START MENU ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        btns = [[InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)], [InlineKeyboardButton("I am joined ✅", callback_data="check_joined")]]
        return await message.reply(f"Hello {mention}\nJoin our channel to continue.", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            sent_msg = await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            await message.reply("⚠️ This file will be deleted in 10 minutes.")
            asyncio.create_task(auto_delete(client, uid, sent_msg.id))
            return
        return await message.reply("🔒 Premium Only!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}!", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")],
        [InlineKeyboardButton("👤 MY PLAN", callback_data="my_plan"), InlineKeyboardButton("📞 Contact Admin", url="http://t.me/Provider169_bot")]
    ]))

# --- 👑 LINK GENERATOR ---
@app.on_message(filters.user(ADMIN_ID) & (filters.command("link") | filters.media | filters.regex(r"t.me\/")))
async def link_gen(client, message):
    try:
        target = message.reply_to_message if message.reply_to_message else message
        if message.text and "start=" in message.text:
            fid = message.text.split("start=")[1].split()[0]
            target = await client.get_messages(STORAGE_CHANNEL_ID, int(fid))
        msg = await target.copy(STORAGE_CHANNEL_ID)
        link = f"https://t.me/{(await client.get_me()).username}?start={msg.id}"
        await message.reply(f"✅ **Permanent Link:** `{link}`")
    except: await message.reply("❌ Error generating link.")

# --- 👑 ADMIN PANEL ---
@app.on_message(filters.user(ADMIN_ID) & filters.command("admin"))
async def admin_panel(client, message):
    total = await users_col.count_documents({}); prem = await users_col.count_documents({"status": "premium"})
    text = f"👑 **ULTRA ADMIN PANEL**\n\n📊 Total: {total}\n💎 Premium: {prem}"
    btns = [[InlineKeyboardButton("📝 Plan Mngr", callback_data="m_plan"), InlineKeyboardButton("📢 F-Join Mngr", callback_data="m_fj")],
            [InlineKeyboardButton("📊 Stats", callback_data="m_stats"), InlineKeyboardButton("❌ Close", callback_data="close_admin")]]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(btns))

# --- PHOTO HANDLER ---
@app.on_message(filters.photo & filters.private)
async def user_ss(client, message):
    uid = message.from_user.id
    if uid == ADMIN_ID: return 
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("1 Day", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 Day", callback_data=f"apr_{uid}_7")],
                                 [InlineKeyboardButton("1 Month", callback_data=f"apr_{uid}_30"), InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]])
    await message.copy(ADMIN_ID, caption=f"📩 Proof from `{uid}`", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!\nStatus: Pending")

# --- CALLBACK HANDLER ---
@app.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data
    if data == "buy_plans":
        text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n›› 1 day : ₹30 / $0.50\n›› 7 day : ₹70 / $1.20\n›› 30 day : ₹200 / $4"
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("p_"):
        _, inr, usd, days = data.split("_")
        btns = [[InlineKeyboardButton("💳 UPI (₹)", callback_data=f"i_upi_{inr}"), InlineKeyboardButton("💰 BINANCE ($)", callback_data=f"i_bin_{usd}")]]
        await cb.edit_message_text(f"Select Method for {days} Days:", reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("i_"):
        m, val = data.split("_")[1], data.split("_")[2]
        if m == "upi": await cb.message.reply_photo(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26am={val}", caption=f"💠 Pay ₹{val} to UPI")
        else: await cb.message.reply(f"🟡 Binance ID: `{BINANCE_ID}`\nAmount: {val}$")
        await cb.message.delete()
    elif data.startswith("apr_"):
        _, u, d = data.split("_"); exp = datetime.now() + timedelta(days=int(d))
        await users_col.update_one({"user_id": int(u)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(u), "✅ Premium Activated!"); await cb.message.edit_caption(f"Approved ✅")
    elif data == "check_joined":
        if await check_fjoin(cb.from_user.id): await cb.message.delete(); await start(client, cb.message)
        else: await cb.answer("Join first!", show_alert=True)
    elif data == "close_admin": await cb.message.delete()
    elif data == "m_stats": await cb.answer(f"Stats shown in panel text.", show_alert=True)

# --- THE FIX: FINAL BOOT LOGIC ---
async def start_bot():
    print("--- STARTING TELEGRAM BOT ---")
    await app.start()
    asyncio.create_task(global_checker())
    print("--- BOT IS LIVE ---")
    await idle()

if __name__ == "__main__":
    # Flask thread chalu karein
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Pyrogram event loop setup
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
