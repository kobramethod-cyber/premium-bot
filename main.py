import os
import asyncio
import threading
import urllib.parse
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "25691060"))
API_HASH = os.environ.get("API_HASH", "8ba2c49611687f1747758376916538c3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1119812744"))

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"
FORCE_CHANNEL_ID = -1003575487358

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def check_fjoin(user_id):
    try:
        m = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return m.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except: return False

async def auto_delete(client, chat_id, message_id):
    await asyncio.sleep(600)
    try: await client.delete_messages(chat_id, message_id)
    except: pass

async def expiry_checker():
    while True:
        try:
            now = datetime.now()
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                try: await app.send_message(uid, "❗ ›› Your premium membership has expired.\n\nRenew your premium membership to continue. Contact Our Admins.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url="http://t.me/Provider169_bot")]]))
                except: pass
        except: pass
        await asyncio.sleep(600)

# --- START ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        btns = [[InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)], [InlineKeyboardButton("I am joined ✅", callback_data="check_joined")]]
        return await message.reply(f"Hello {mention}\n\nYou need to join in my Channel/Group to use me", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            sent_msg = await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            await message.reply("⚠️ This file will be deleted automatically after 10 minutes.")
            asyncio.create_task(auto_delete(client, uid, sent_msg.id))
            return
        return await message.reply("🔒 **This content is for Premium Users only!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}\n\nWelecome to premium bot", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")], [InlineKeyboardButton("📞 Contact Admin", url="http://t.me/Provider169_bot")]]))

# --- ADMIN HANDLER (GENERATE LINK & /ADMIN) ---
@app.on_message(filters.user(ADMIN_ID) & filters.private)
async def admin_handler(client, message):
    if message.text:
        if message.text.startswith("/start"): return
        if message.text == "/admin":
            total = await users_col.count_documents({})
            prem = await users_col.count_documents({"status": "premium"})
            btns = [[InlineKeyboardButton("📊 Stats", callback_data="m_stats")], [InlineKeyboardButton("✉️ Broadcast", callback_data="bc_cmd")]]
            return await message.reply(f"👑 **Admin Panel**\nTotal: {total} | Prem: {prem}", reply_markup=InlineKeyboardMarkup(btns))
        
        if message.text.startswith("/link"):
            target = message.reply_to_message if message.reply_to_message else message
            wait = await message.reply("⏳ Generating...")
            msg = await target.copy(STORAGE_CHANNEL_ID)
            link = f"https://t.me/{(await client.get_me()).username}?start={msg.id}"
            return await wait.edit(f"✅ **Link Generated:**\n`{link}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={link}")]]))

    if message.media:
        wait = await message.reply("⏳ Generating Link...")
        msg = await message.copy(STORAGE_CHANNEL_ID)
        link = f"https://t.me/{(await client.get_me()).username}?start={msg.id}"
        return await wait.edit(f"✅ **Link Generated:**\n`{link}`")

# --- USER SCREENSHOT HANDLER ---
@app.on_message(filters.photo & filters.private)
async def user_ss(client, message):
    uid = message.from_user.id
    if uid == ADMIN_ID: return 
    
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 day approve", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day approve", callback_data=f"apr_{uid}_7")],
        [InlineKeyboardButton("15 day approve", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month approve", callback_data=f"apr_{uid}_30")],
        [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]
    ])
    await message.copy(ADMIN_ID, caption=f"📩 **Proof** from `{uid}`", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!\n\n⚡ Your proof is being verified.\n📝 Status: Pending\n⏳ Time: 1 Hours (Max)\n\n🟢 You will be notified automatically once funds are added.")

# --- CALLBACK HANDLER (FIXED) ---
@app.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data
    if data == "buy_plans":
        text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1.20\n›› 15 Days : ₹120 /$ 2\n›› 1 Months : ₹200 /$ 4"
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("15 DAY", callback_data="p_120_2_15"), InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))
    
    elif data.startswith("p_"):
        _, inr, usd, days = data.split("_")
        btns = [[InlineKeyboardButton("💳 UPI", callback_data=f"i_upi_{inr}"), InlineKeyboardButton("💰 BINANCE", callback_data=f"i_bin_{usd}")]]
        await cb.edit_message_text("Select Method:", reply_markup=InlineKeyboardMarkup(btns))
    
    elif data.startswith("i_"):
        m, val = data.split("_")[1], data.split("_")[2]
        if m == "upi":
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26am={val}"
            await cb.message.reply_photo(qr, caption=f"💠 Pay ₹{val}\nBhejne ke baad screenshot dein.")
        else: await cb.message.reply(f"🟡 Binance ID: `{BINANCE_ID}`\nAmount: {val}$")
        await cb.message.delete()
    
    elif data.startswith("apr_"):
        _, uid, days = data.split("_")
        exp = datetime.now() + timedelta(days=int(days))
        await users_col.update_one({"user_id": int(uid)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(uid), "✅ Premium Activated!")
        await cb.message.edit_caption(f"Approved ✅")
        await cb.answer("User Approved!", show_alert=True)
        
    elif data.startswith("rej_"):
        uid = data.split("_")[1]
        await client.send_message(int(uid), "❌ Your payment was rejected.")
        await cb.message.edit_caption("Rejected ❌")
        await cb.answer("User Rejected!", show_alert=True)

    elif data == "check_joined":
        if await check_fjoin(cb.from_user.id):
            await cb.message.delete(); await start(client, cb.message)
        else: await cb.answer("Join channel first! ❌", show_alert=True)

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.create_task(expiry_checker())
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
