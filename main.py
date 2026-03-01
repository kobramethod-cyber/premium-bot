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

# --- DYNAMIC ADMIN & FJOIN UTILS ---
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

# --- 🔄 AUTO EXPIRE & REMINDER LOOP ---
async def expiry_checker():
    while True:
        try:
            now = datetime.now()
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                await app.send_message(uid, "❗ ›› Your premium membership has expired.\n\nRenew your premium membership to continue enjoying the benefits. Contact Our Admins.", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=CONTACT_URL)]]))

            reminder_time = now + timedelta(hours=1)
            remind = users_col.find({"status": "premium", "expiry": {"$lt": reminder_time, "$gt": now}, "reminded": {"$ne": True}})
            async for user in remind:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"reminded": True}})
                await app.send_message(uid, "››⚠️ Reminder: Your premium membership will expire in 1 hour.\n\nTo renew your premium membership, please Contact Our Admins.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=CONTACT_URL)]]))
        except: pass
        await asyncio.sleep(600)

# --- 🚀 START & USER FLOW ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        channels = await get_fjoins()
        btns = [[InlineKeyboardButton("Join Channel", url=ch['link'])] for ch in channels]
        btns.append([InlineKeyboardButton("I am joined ✅", callback_data="check_joined")])
        return await message.reply(f"Hello {mention}\n\nYou need to join in my Channel/Group to use me\n\nKindly Please join Channel...", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            try: return await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            except: return await message.reply("❌ File not found.")
        return await message.reply("🔒 **This content is for Premium Users only!**", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}\n\nWelecome to premium bot\n\nPremium ke liye buy premium button tap kare", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")], [InlineKeyboardButton("📞 Contact Admin 📞", url=CONTACT_URL)]]))

@app.on_callback_query(filters.regex("check_joined"))
async def check_joined_cb(client, cb):
    if await check_fjoin(cb.from_user.id):
        await cb.message.delete()
        await start(client, cb.message)
    else: await cb.answer("Join all channels first! ❌", show_alert=True)

# --- 💰 DYNAMIC PLANS ---
@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, cb):
    plans = await plans_col.find().to_list(length=20)
    if not plans:
        default = [{"name":"1 Day","price":30,"days":1},{"name":"7 Days","price":70,"days":7},{"name":"15 Days","price":120,"days":15},{"name":"30 Days","price":200,"days":30}]
        await plans_col.insert_many(default)
        plans = default
    
    text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\nᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ\n────────────────────\n"
    for p in plans: text += f"›› {p['name']} : ₹{p['price']}\n"
    text += "\n❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦\n❐ 𝗉𝖺𝗒𝗍𝗆 • 𝗀𝗉𝖺𝗒 • 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • 𝗎𝗉𝗂 𝖺𝗇𝖽 𝗊𝗋 and binnance\n────────────────────\n✦ Pʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴏɴᴄᴇ ᴘᴀɪᴅ\n✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓"
    
    btns = [[InlineKeyboardButton(f"{p['name']}", callback_data=f"pay_{p['price']}_{p['days']}")] for p in plans]
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"pay_(\d+)_(\d+)"))
async def select_pay_method(client, cb):
    amt, days = cb.data.split("_")[1], cb.data.split("_")[2]
    btns = [[InlineKeyboardButton("💳 PAY WITH UPI", callback_data=f"info_upi_{amt}_{days}"), InlineKeyboardButton("💰 PAY WITH BINANCE", callback_data=f"info_bin_{amt}_{days}")]]
    await cb.edit_message_text(f"💳 **Payment for ₹{amt} ({days} Days)**\nSelect Method:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"info_(upi|bin)_(\d+)_(\d+)"))
async def info_pay(client, cb):
    m, a, d = cb.data.split("_")[1], cb.data.split("_")[2], cb.data.split("_")[3]
    if m == "upi":
        upi_url = f"upi://pay?pa={UPI_ID}&am={a}&cu=INR"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
        await cb.message.reply_photo(qr, caption=f"💠 **Scan & Pay ₹{a}**\nUPI ID: `{UPI_ID}`\n\n✅ Payment ke baad screenshot bhejiye.")
    else:
        await cb.message.reply(f"🟡 **Binance ID:** `{BINANCE_ID}`\nAmount: **₹{a}**\n\n✅ Payment ke baad screenshot bhejiye.")
    await cb.message.delete()

# --- 👑 POWER ADMIN PANEL ---
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message):
    if message.from_user.id not in await get_admins(): return
    btns = [
        [InlineKeyboardButton("📝 Plan Mngr", callback_data="mng_plans"), InlineKeyboardButton("📢 F-Join Mngr", callback_data="mng_fj")],
        [InlineKeyboardButton("👥 Admin Mngr", callback_data="mng_admins"), InlineKeyboardButton("📊 Stats", callback_data="mng_stats")],
        [InlineKeyboardButton("✉️ Broadcast", callback_data="bc_cmd")]
    ]
    await message.reply("👑 **SUPER ADMIN PANEL**", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"mng_(plans|fj|admins|stats)"))
async def manage_cb(client, cb):
    target = cb.data.split("_")[1]
    if cb.from_user.id not in await get_admins(): return
    if target == "stats":
        total = await users_col.count_documents({})
        prem = await users_col.count_documents({"status": "premium"})
        text = f"📊 **STATS**\nTotal Users: {total}\nPremium Users: {prem}"
    elif target == "plans":
        text = "📝 **PLAN MANAGER**\n`/add_plan Name|Price|Days`\n`/del_plan Name`"
    elif target == "fj":
        text = "📢 **F-JOIN MANAGER**\n`/add_fj ID|Link`\n`/del_fj ID`"
    elif target == "admins":
        text = "👥 **ADMIN MANAGER**\n`/add_admin ID`\n`/del_admin ID`"
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]]))

# --- ADMIN ACTIONS (COMMANDS) ---
@app.on_message(filters.command("add_plan") & filters.private)
async def add_plan_cmd(client, message):
    if message.from_user.id not in await get_admins(): return
    try:
        _, data = message.text.split(" ", 1)
        n, p, d = data.split("|")
        await plans_col.update_one({"name": n}, {"$set": {"price": int(p), "days": int(d)}}, upsert=True)
        await message.reply(f"✅ Plan '{n}' Added/Updated!")
    except: await message.reply("Usage: `/add_plan Gold|200|30` (Name|Price|Days)")

@app.on_message(filters.command("add_admin") & filters.private)
async def add_admin_cmd(client, message):
    if message.from_user.id != PRIMARY_ADMIN: return
    try:
        _, uid = message.text.split()
        await settings_col.update_one({"type": "admins"}, {"$push": {"list": int(uid)}}, upsert=True)
        await message.reply(f"✅ User {uid} added as Admin!")
    except: await message.reply("Usage: `/add_admin 1234567`")

@app.on_message(filters.command("add_fj") & filters.private)
async def add_fj_cmd(client, message):
    if message.from_user.id not in await get_admins(): return
    try:
        _, data = message.text.split
