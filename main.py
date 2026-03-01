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

# --- DYNAMIC ADMIN & UTILS ---
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

# --- 🔄 AUTO EXPIRE & REMINDER ---
async def expiry_checker():
    while True:
        try:
            now = datetime.now()
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                await app.send_message(uid, "❗ ›› Your premium membership has expired.\n\nRenew your premium membership to continue. Contact Our Admins.", 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Contact Admin", url=CONTACT_URL)]]))
        except: pass
        await asyncio.sleep(600)

# --- 🚀 START & USER FLOW ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        channels = await get_fjoins()
        btns = [[InlineKeyboardButton(f"Join Channel {i+1}", url=ch['link'])] for i, ch in enumerate(channels)]
        btns.append([InlineKeyboardButton("I am joined ✅", callback_data="check_joined")])
        return await message.reply(f"Hello {mention}\n\nYou need to join in my Channel/Group to use me", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            try: return await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            except: return await message.reply("❌ File not found.")
        return await message.reply("🔒 **Premium required!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}\n\nWelcome to premium bot", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")], [InlineKeyboardButton("📞 Contact Admin 📞", url=CONTACT_URL)]]))

# --- 💰 DYNAMIC PLANS ---
@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, cb):
    plans = await plans_col.find().to_list(length=20)
    text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n────────────────────\n"
    for p in plans: text += f"›› {p['name']} : ₹{p['price']}\n"
    btns = [[InlineKeyboardButton(f"{p['name']} - ₹{p['price']}", callback_data=f"pay_{p['price']}_{p['days']}")] for p in plans]
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"pay_(\d+)_(\d+)"))
async def pay_info(client, cb):
    amt, days = cb.data.split("_")[1], cb.data.split("_")[2]
    upi_url = f"upi://pay?pa={UPI_ID}&am={amt}&cu=INR"
    qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"
    await cb.message.reply_photo(qr, caption=f"💠 **Pay ₹{amt} for {days} Days**\nUPI: `{UPI_ID}`\n\nSend screenshot.")
    await cb.message.delete()

# --- 👑 MEGA ADMIN PANEL ---
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message):
    admins = await get_admins()
    if message.from_user.id not in admins: return
    
    btns = [
        [InlineKeyboardButton("📝 Plan Mngr", callback_data="mng_plans"), InlineKeyboardButton("📢 F-Join Mngr", callback_data="mng_fj")],
        [InlineKeyboardButton("👥 Admin Mngr", callback_data="mng_admins"), InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("✉️ Broadcast", callback_data="broadcast_cmd")]
    ]
    await message.reply("👑 **SUPER ADMIN PANEL**\nChoose a category to manage:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"mng_(plans|fj|admins|stats)"))
async def manage_cb(client, cb):
    target = cb.data.split("_")[1]
    admins = await get_admins()
    if cb.from_user.id not in admins: return

    if target == "stats":
        total = await users_col.count_documents({})
        prem = await users_col.count_documents({"status": "premium"})
        exp = await users_col.count_documents({"status": "free", "expiry": {"$exists": True}})
        text = f"📊 **BOT STATISTICS**\n\nTotal Users: {total}\nPremium Users: {prem}\nExpired Users: {exp}"
        return await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]]))

    if target == "plans":
        text = "📝 **PLAN MANAGER**\n\nCommands:\n`/add_plan Name|Price|Days`\n`/del_plan Name`"
    elif target == "fj":
        text = "📢 **FORCE JOIN MANAGER**\n\nCommands:\n`/add_fj ChannelID|Link`\n`/del_fj ChannelID`"
    elif target == "admins":
        text = "👥 **ADMIN MANAGER**\n\nCommands:\n`/add_admin UserID`\n`/del_admin UserID`"
    
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_admin")]]))

# --- ADMIN ACTIONS (COMMANDS) ---
@app.on_message(filters.command("add_plan") & filters.private)
async def add_plan_cmd(client, message):
    if message.from_user.id not in await get_admins(): return
    try:
        _, data = message.text.split(" ", 1)
        n, p, d = data.split("|")
        await plans_col.update_one({"name": n}, {"$set": {"price": int(p), "days": int(d)}}, upsert=True)
        await message.reply(f"✅ Plan '{n}' saved/updated!")
    except: await message.reply("Usage: `/add_plan Gold|500|30`")

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
        _, data = message.text.split(" ", 1)
        cid, link = data.split("|")
        await settings_col.update_one({"type": "fjoins"}, {"$push": {"channels": {"id": int(cid), "link": link}}}, upsert=True)
        await message.reply("✅ F-Join Added!")
    except: await message.reply("Usage: `/add_fj -100xxx|https://t.me/xxx`")

@app.on_message(filters.command("approve") & filters.private)
async def approve_cmd(client, message):
    if message.from_user.id not in await get_admins(): return
    try:
        _, uid, d = message.text.split()
        exp = datetime.now() + timedelta(days=int(d))
        await users_col.update_one({"user_id": int(uid)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(uid), f"✅ Premium Activated for {d} days!")
        await message.reply("Approved!")
    except: await message.reply("Usage: `/approve ID days`")

# --- OTHER HANDLERS ---
@app.on_callback_query(filters.regex("back_admin"))
async def back_admin(client, cb):
    await admin_panel(client, cb.message)

@app.on_message(filters.user(PRIMARY_ADMIN) & filters.forwarded)
async def gen_link(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    await message.reply(f"🔗 Link: https://t.me/{(await client.get_me()).username}?start={msg.id}")

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.create_task(expiry_checker())
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
