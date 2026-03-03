import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Beyond Ultra Max Bot Online"

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
settings_col = db.settings

app = Client("ultra_max_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def check_fjoin(user_id):
    try:
        m = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return m.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except: return False

async def get_admins():
    data = await settings_col.find_one({"type": "admin_list"})
    return data['admins'] if data else [ADMIN_ID]

# --- 🔄 GLOBAL CHECKER (EXPIRY & REMINDERS) ---
async def global_checker():
    while True:
        try:
            now = datetime.now()
            expired = users_col.find({"status": "premium", "expiry": {"$lt": now}})
            async for user in expired:
                uid = user['user_id']
                await users_col.update_one({"user_id": uid}, {"$set": {"status": "free"}, "$unset": {"expiry": "", "reminded": ""}})
                try: await app.send_message(uid, "❗ Your premium expired. Renew now!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 RENEW", callback_data="buy_plans")]]))
                except: pass
        except: pass
        await asyncio.sleep(600)

# --- START & MENU ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        btns = [[InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)], [InlineKeyboardButton("I am joined ✅", callback_data="check_joined")]]
        return await message.reply(f"Hello {mention}\nJoin our channel to continue.", reply_markup=InlineKeyboardMarkup(btns))

    await message.reply(
        f"Hello {mention}!\nWelcome to Premium Bot.", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")],
            [InlineKeyboardButton("👤 MY PLAN", callback_data="my_plan"), InlineKeyboardButton("📞 Contact Admin", url="http://t.me/Provider169_bot")]
        ])
    )

# --- 👑 ADVANCED ADMIN PANEL ---
@app.on_message(filters.user(ADMIN_ID) & filters.command("admin"))
async def admin_panel(client, message):
    total = await users_col.count_documents({}); prem = await users_col.count_documents({"status": "premium"})
    text = f"👑 **ULTRA PRO ADMIN PANEL**\n\n📊 Total Users: `{total}`\n💎 Premium: `{prem}`"
    btns = [
        [InlineKeyboardButton("📝 Plan Mngr", callback_data="m_plan"), InlineKeyboardButton("📢 F-Join Mngr", callback_data="m_fj")],
        [InlineKeyboardButton("👥 Admin Mngr", callback_data="m_adm"), InlineKeyboardButton("📊 Stats", callback_data="m_stats")],
        [InlineKeyboardButton("✉️ Broadcast", callback_data="m_bc"), InlineKeyboardButton("❌ Close", callback_data="close_admin")]
    ]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(btns))

# --- USER PHOTO HANDLER ---
@app.on_message(filters.photo & filters.private)
async def user_ss(client, message):
    uid = message.from_user.id
    if uid in await get_admins(): return 
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("1 day", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day", callback_data=f"apr_{uid}_7")],
                                 [InlineKeyboardButton("15 day", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month", callback_data=f"apr_{uid}_30")],
                                 [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]])
    await message.copy(ADMIN_ID, caption=f"📩 Proof from `{uid}`", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!\nStatus: Pending")

# --- CALLBACKS ---
@app.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data
    if data == "m_plan":
        await cb.answer("Redirecting to Plan Manager...", show_alert=True)
    elif data == "m_fj":
        await cb.answer("Redirecting to Force Join Settings...", show_alert=True)
    elif data == "m_adm":
        await cb.answer("Redirecting to Admin Management...", show_alert=True)
    elif data == "m_stats":
        total = await users_col.count_documents({}); prem = await users_col.count_documents({"status": "premium"})
        await cb.answer(f"Users: {total}\nPremium: {prem}", show_alert=True)
    elif data == "buy_plans":
        text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1.20\n›› 15 Days : ₹120 /$ 2\n›› 1 Months : ₹200 /$ 4"
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("15 DAY", callback_data="p_120_2_15"), InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))
    elif data.startswith("apr_"):
        _, u, d = data.split("_"); exp = datetime.now() + timedelta(days=int(d))
        await users_col.update_one({"user_id": int(u)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(u), "✅ Premium Activated!"); await cb.message.edit_caption("Approved ✅")
    elif data == "close_admin": await cb.message.delete()
    elif data == "check_joined":
        if await check_fjoin(cb.from_user.id): await cb.message.delete(); await start(client, cb.message)
        else: await cb.answer("Join first!", show_alert=True)

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.create_task(global_checker())
    await app.start(); await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
