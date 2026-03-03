import os
import asyncio
import threading
import urllib.parse
import random
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Ultra Max Pro Bot Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "25691060"))
API_HASH = os.environ.get("API_HASH", "8ba2c49611687f1747758376916538c3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = 1119812744 # Kartik Nagargoje ID

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
    await asyncio.sleep(600) # 10 Minutes
    try: await client.delete_messages(chat_id, message_id)
    except: pass

# --- 🔄 AUTO EXPIRE & REMINDERS ---
async def global_checker():
    while True:
        try:
            now = datetime.now()
            # 1. Expiry Logic
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                try: await app.send_message(uid, "❗ Your premium has expired. Renew now!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 RENEW", callback_data="buy_plans")]]))
                except: pass
            
            # 2. 1-Hour Reminder
            rem_time = now + timedelta(hours=1)
            remind = users_col.find({"status": "premium", "expiry": {"$lt": rem_time, "$gt": now}, "reminded": {"$ne": True}})
            async for user in remind:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"reminded": True}})
                try: await app.send_message(uid, "⚠️ Warning: Your premium expires in 1 hour!")
                except: pass
        except: pass
        await asyncio.sleep(600)

# --- START & COMMANDS ---
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
            await message.reply("⚠️ Deleted in 10 mins.")
            asyncio.create_task(auto_delete(client, uid, sent_msg.id))
            return
        return await message.reply("🔒 Premium Only!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY", callback_data="buy_plans")]]))

    await message.reply(
        f"Hello {mention}!\n\nWelcome to Premium Bot.", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")],
            [InlineKeyboardButton("👤 MY PLAN", callback_data="my_plan"), InlineKeyboardButton("📞 Contact Admin", url="http://t.me/Provider169_bot")]
        ])
    )

# --- 👑 LINK GENERATOR (REPLY/DIRECT) ---
@app.on_message(filters.user(ADMIN_ID) & (filters.command("link") | filters.regex(r"t.me\/") | filters.media))
async def ultra_link_gen(client, message):
    try:
        if message.reply_to_message: target = message.reply_to_message
        elif message.media: target = message
        elif "start=" in (message.text or ""):
            file_id = message.text.split("start=")[1].split()[0]
            target = await client.get_messages(STORAGE_CHANNEL_ID, int(file_id))
        else: return await message.reply("Reply to a file or send a link.")

        msg = await target.copy(STORAGE_CHANNEL_ID)
        link = f"https://t.me/{(await client.get_me()).username}?start={msg.id}"
        await message.reply(f"✅ **Permanent Link:** `{link}`")
    except Exception as e: await message.reply(f"❌ Error: {str(e)}")

# --- USER PHOTO HANDLER ---
@app.on_message(filters.photo & filters.private)
async def user_ss(client, message):
    uid = message.from_user.id
    if uid == ADMIN_ID: return 
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("1 day", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day", callback_data=f"apr_{uid}_7")],
                                 [InlineKeyboardButton("15 day", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month", callback_data=f"apr_{uid}_30")],
                                 [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]])
    await message.copy(ADMIN_ID, caption=f"📩 Proof from `{uid}`", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!\n\n⚡ Your proof is being verified.\n📝 Status: Pending\n⏳ Time: 1 Hours (Max)\n\n🟢 You will be notified automatically once funds are added.")

# --- CALLBACKS ---
@app.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data
    uid = cb.from_user.id
    if data == "buy_plans":
        text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1.20\n›› 15 Days : ₹120 /$ 2\n›› 1 Months : ₹200 /$ 4"
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("15 DAY", callback_data="p_120_2_15"), InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("p_"):
        _, inr, usd, days = data.split("_")
        btns = [[InlineKeyboardButton("💳 UPI", callback_data=f"i_upi_{inr}"), InlineKeyboardButton("💰 BINANCE", callback_data=f"i_bin_{usd}")]]
        await cb.edit_message_text(f"Select Method for {days} Days:", reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("i_"):
        m, val = data.split("_")[1], data.split("_")[2]
        if m == "upi":
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26am={val}"
            await cb.message.reply_photo(qr, caption=f"💠 Pay ₹{val}\nBhejne ke baad screenshot dein.")
        else: await cb.message.reply(f"🟡 Binance ID: `{BINANCE_ID}`\nAmount: {val}$")
        await cb.message.delete()
    elif data.startswith("apr_"):
        _, u, d = data.split("_"); exp = datetime.now() + timedelta(days=int(d))
        await users_col.update_one({"user_id": int(u)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(u), "✅ Premium Activated!"); await cb.message.edit_caption("Approved ✅")
    elif data == "my_plan":
        user = await users_col.find_one({"user_id": uid})
        status = "Active ✅" if user and user.get("status") == "premium" else "Inactive ❌"
        await cb.answer(f"Your Plan: {status}", show_alert=True)
    elif data == "check_joined":
        if await check_fjoin(uid): await cb.message.delete(); await start(client, cb.message)
        else: await cb.answer("Join first!", show_alert=True)

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.create_task(global_checker())
    await app.start(); await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
