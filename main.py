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
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477
CONTACT_URL = "http://t.me/Provider169_bot"
FORCE_CHANNEL_ID = -1003575487358
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS: FORCE JOIN ---
async def check_fjoin(user_id):
    try:
        m = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return m.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except: return False

# --- 🔄 AUTO EXPIRE & REMINDER LOOP ---
async def expiry_checker():
    while True:
        try:
            now = datetime.now()
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                await app.send_message(uid, "❗ ›› Your premium membership has expired.\n\nRenew your premium membership to continue enjoying the benefits. Contact Our Admins.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=CONTACT_URL)]]))

            reminder_time = now + timedelta(hours=1)
            remind = users_col.find({"status": "premium", "expiry": {"$lt": reminder_time, "$gt": now}, "reminded": {"$ne": True}})
            async for user in remind:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"reminded": True}})
                await app.send_message(uid, "››⚠️ Reminder: Your premium membership will expire in 1 hour.\n\nTo renew your premium membership, please Contact Our Admins.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=CONTACT_URL)]]))
        except: pass
        await asyncio.sleep(600)

# --- START & FORCE JOIN ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        btns = [[InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)], [InlineKeyboardButton("I am joined", callback_data="check_joined")]]
        return await message.reply(f"Hello {mention}\n\nYou need to join in my Channel/Group to use me\n\nKindly Please join Channel...", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            try: return await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            except: return await message.reply("❌ File not found.")
        return await message.reply("🔒 **This content is for Premium Users only!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}\n\nWelecome to premium bot \n\nPremium ke liye buy premium button tap kare", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")], [InlineKeyboardButton("📞 Contact Admin 📞", url=CONTACT_URL)]]))

@app.on_callback_query(filters.regex("check_joined"))
async def check_joined_cb(client, cb):
    if await check_fjoin(cb.from_user.id):
        await cb.message.delete()
        await start(client, cb.message)
    else: await cb.answer("Join first! ❌", show_alert=True)

# --- 💰 PLANS (EXACT TEXT) ---
@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, cb):
    text = (
        "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n"
        "ᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ\n"
        "────────────────────\n"
        "›› 1 days : ₹30 / $ 0.50\n"
        "›› 7 Days : ₹70 /$ 1\n"
        "›› 15 Days : ₹120 /$ 1.50\n"
        "›› 1 Months : ₹200 /$ 2.50\n\n"
        "❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦\n"
        "❐ 𝗉𝖺𝗒𝗍𝗆 • 𝗀𝗉𝖺𝗒 • 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • 𝗎𝗉𝗂 𝖺𝗇𝖽 𝗊𝗋 and binnance\n"
        "────────────────────\n"
        "✦ Pʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴏɴᴄᴇ ᴘᴀɪᴅ\n"
        "✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n"
        "❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ a ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓"
    )
    btns = [
        [InlineKeyboardButton("1 DAY", callback_data="pay_30_1"), InlineKeyboardButton("7 DAY", callback_data="pay_70_7")],
        [InlineKeyboardButton("15 DAY", callback_data="pay_120_15"), InlineKeyboardButton("30 DAY", callback_data="pay_200_30")]
    ]
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"pay_(\d+)_(\d+)"))
async def select_method(client, cb):
    amt, days = cb.data.split("_")[1], cb.data.split("_")[2]
    btns = [[InlineKeyboardButton("💳 PAY WITH UPI", callback_data=f"info_upi_{amt}_{days}"), InlineKeyboardButton("💰 PAY WITH BINNANCE", callback_data=f"info_bin_{amt}_{days}")]]
    await cb.edit_message_text(f"Select Payment Method for ₹{amt}:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"(upi|bin)_(\d+)_(\d+)"))
async def info_pay(client, cb):
    m, a, d = cb.data.split("_")[1], cb.data.split("_")[2], cb.data.split("_")[3]
    if m == "upi":
        upi_url = f"upi://pay?pa={UPI_ID}&am={a}&cu=INR"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
        await cb.message.reply_photo(qr, caption=f"💠 **Scan & Pay ₹{a}**\nUPI ID: `{UPI_ID}`\n\n✅ Pay karne ke baad screenshot bhejiye.")
    else:
        await cb.message.reply(f"🟡 **Binnance ID:** `{BINANCE_ID}`\nAmount: **₹{a}**\n\n✅ Pay karne ke baad screenshot bhejiye.")
    await cb.message.delete()

# --- 📸 SCREENSHOT & ADMIN APPROVAL ---
@app.on_message(filters.photo & filters.private)
async def handle_ss(client, message):
    uid = message.from_user.id
    if uid == ADMIN_ID: return
    btns = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 day approve", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day approve", callback_data=f"apr_{uid}_7")],
        [InlineKeyboardButton("15 day approve", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month approve", callback_data=f"apr_{uid}_30")],
        [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]
    ])
    await message.copy(ADMIN_ID, caption=f"📩 **Payment Screenshot**\nUser ID: `{uid}`\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!\n\n⚡ Your proof is being verified.\n📝 Status: Pending\n⏳ Time: 1 Hours (Max)\n\n🟢 You will be notified automatically once funds are added.")

@app.on_callback_query(filters.regex(r"(apr|rej)_(\d+)(_(\d+))?"))
async def admin_action(client, cb):
    data = cb.data.split("_")
    act, uid = data[0], int(data[1])
    if act == "apr":
        days = int(data[2])
        exp = datetime.now() + timedelta(days=days)
        await users_col.update_one({"user_id": uid}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(uid, f"✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ!\n\n🎉 Pʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ғᴏʀ {days} day!\n💎 Eɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss!")
        await cb.message.edit_caption(f"Approved for {days} Days ✅")
    else:
        await client.send_message(uid, "❌ **Payment Rejected!**")
        await cb.message.edit_caption("Rejected ❌")

# --- ADMIN PANEL & TOOLS ---
@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(client, message):
    total = await users_col.count_documents({})
    prem = await users_col.count_documents({"status": "premium"})
    await message.reply(f"📊 **Stats**\nTotal Users: {total}\nPremium: {prem}\n\n/broadcast - Sabko bhejie\nForward any file for link.")

@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def gen_link(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    me = await client.get_me()
    await message.reply(f"🔗 **Protected Link:**\n`https://t.me/{me.username}?start={msg.id}`")

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def bc(client, message):
    users = users_col.find({})
    async for u in users:
        try: await message.reply_to_message.copy(u['user_id'])
        except: pass
    await message.reply("Broadcast Done!")

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.create_task(expiry_checker())
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
