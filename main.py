import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER PORT BINDING ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col, settings_col, plans_col = db.users, db.settings, db.plans

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def get_fjoin():
    data = await settings_col.find_one({"type": "fjoin"})
    return data if data else {"id": -1003575487358, "link": "https://t.me/+mInAMHlOgIo0Yjg1"}

async def is_subscribed(user_id):
    fjoin = await get_fjoin()
    try:
        m = await app.get_chat_member(fjoin['id'], user_id)
        return m.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except: return False

# --- 1️⃣ /START & FORCE JOIN ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = message.from_user.id
    fjoin = await get_fjoin()
    
    if not await is_subscribed(uid):
        return await message.reply(
            "⚠️ **Join our channel to continue!**",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel 📢", url=fjoin['link'])]])
        )

    # Deep Link Handler
    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium" and datetime.now() < user.get("expiry"):
            return await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
        else:
            return await message.reply("🔒 **This content is for Premium Users only!**", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Buy Premium", callback_data="buy_plans")]]))

    # 2️⃣ MAIN MENU
    await message.reply(
        "👋 **Welcome to Premium Bot!**\n\nChoose an option from below:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Buy Plan", callback_data="buy_plans")]])
    )

# --- 3️⃣ PLAN SELECTION ---
@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, cb):
    text = (
        "✦ **SHORTNER PLANS**\n"
        "Duration & Price\n"
        "────────────────────\n"
        "›› 1 Day : ₹20\n"
        "›› 7 Days : ₹70\n"
        "›› 15 Days : ₹100\n"
        "›› 30 Days : ₹200"
    )
    buttons = [
        [InlineKeyboardButton("1 DAY", callback_data="pay_20"), InlineKeyboardButton("7 DAYS", callback_data="pay_70")],
        [InlineKeyboardButton("15 DAYS", callback_data="pay_100"), InlineKeyboardButton("30 DAYS", callback_data="pay_200")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
    ]
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 4️⃣ PAYMENT METHOD ---
@app.on_callback_query(filters.regex(r"pay_(\d+)"))
async def select_payment(client, cb):
    amt = cb.data.split("_")[1]
    text = f"💳 **Payment for ₹{amt}**\n\nChoose your preferred payment method:"
    buttons = [
        [InlineKeyboardButton("💠 UPI", callback_data=f"info_upi_{amt}"), InlineKeyboardButton("🟡 Binance", callback_data=f"info_bin_{amt}")],
        [InlineKeyboardButton("🔙 Back", callback_data="buy_plans")]
    ]
    await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 5️⃣ & 6️⃣ UPI/BINANCE FLOW ---
@app.on_callback_query(filters.regex(r"info_(upi|bin)_(\d+)"))
async def show_pay_info(client, cb):
    method, amt = cb.data.split("_")[1], cb.data.split("_")[2]
    
    if method == "upi":
        msg = f"💠 **UPI Payment**\n\nExact Amount: `₹{amt}`\nUPI ID: `{UPI_ID}`"
    else:
        msg = f"🟡 **Binance Payment**\n\nExact Amount: `₹{amt}`\nBinance ID: `{BINANCE_ID}`"
    
    msg += f"\n\n**Note:** Send screenshot after payment with your ID: `{cb.from_user.id}`\n\n⏳ *Payment window: 10 mins*"
    await cb.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"pay_{amt}")]]))

# --- 7️⃣ & 8️⃣ ADMIN APPROVE SYSTEM ---
@app.on_message(filters.command("approve") & filters.user(ADMIN_ID))
async def approve(client, message):
    try:
        _, uid, days = message.text.split()
        exp = datetime.now() + timedelta(days=int(days))
        await users_col.update_one({"user_id": int(uid)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(uid), f"✅ **Payment Approved!**\n\nStatus: **Active**\nExpiry: {days} Days.")
        await message.reply(f"User {uid} activated for {days} days.")
    except: await message.reply("Usage: `/approve user_id days`")

# --- FILE TO LINK SYSTEM ---
@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def gen_link(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    me = await client.get_me()
    await message.reply(f"🔗 **Sharable Link:**\n`https://t.me/{me.username}?start={msg.id}`")

# --- BACK NAVIGATION ---
@app.on_callback_query(filters.regex("back_start"))
async def back_start(client, cb):
    await start(client, cb.message)

# --- RUN BOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    print(">>> BOT IS LIVE WITH PROFESSIONAL FLOW")
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
