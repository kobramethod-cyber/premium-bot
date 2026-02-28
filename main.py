import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER PORT FIX ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Alive"

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

# Database initialization
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users
settings_col = db.settings
plans_col = db.plans

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def get_fjoin():
    data = await settings_col.find_one({"type": "fjoin"})
    if data:
        return data
    return {"id": -1003575487358, "link": "https://t.me/+mInAMHlOgIo0Yjg1"}

async def is_subscribed(user_id):
    fjoin = await get_fjoin()
    try:
        member = await app.get_chat_member(fjoin['id'], user_id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        return False
    return False

# --- USER HANDLERS ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    fjoin = await get_fjoin()
    
    if not await is_subscribed(user_id):
        return await message.reply(
            "❌ **Join our channel to use the bot!**", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=fjoin['link'])]])
        )

    if len(message.command) > 1:
        file_id = message.command[1]
        user = await users_col.find_one({"user_id": user_id})
        if user and user.get("status") == "premium" and datetime.now() < user.get("expiry"):
            try:
                return await client.copy_message(user_id, STORAGE_CHANNEL_ID, int(file_id))
            except Exception as e:
                return await message.reply(f"Error: {e}")
        else:
            return await message.reply(
                "🔒 **Premium Access Required!**", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Buy Plan", callback_data="buy_plans")]])
            )

    await message.reply(
        f"Hello {message.from_user.first_name}!\nWelcome to Premium Bot.", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_plans")]])
    )

@app.on_callback_query(filters.regex("buy_plans"))
async def buy_plans_cb(client, cb):
    plans = await plans_col.find().to_list(length=10)
    if not plans:
        # Default plans if DB is empty
        default_plans = [
            {"name": "1 Day", "price": 20, "days": 1},
            {"name": "7 Days", "price": 70, "days": 7},
            {"name": "30 Days", "price": 200, "days": 30}
        ]
        await plans_col.insert_many(default_plans)
        plans = default_plans
    
    buttons = []
    for p in plans:
        buttons.append([InlineKeyboardButton(f"{p['name']} - ₹{p['price']}", callback_data=f"pay_{p['price']}")])
    
    await cb.edit_message_text("✦ **PREMIUM PLANS**\nChoose a plan to continue:", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"pay_(\d+)"))
async def pay_method_cb(client, cb):
    amt = cb.data.split("_")[1]
    buttons = [
        [InlineKeyboardButton("💠 UPI", callback_data=f"info_upi_{amt}"), InlineKeyboardButton("🟡 Binance", callback_data=f"info_bin_{amt}")],
        [InlineKeyboardButton("🔙 Back", callback_data="buy_plans")]
    ]
    await cb.edit_message_text(f"💳 **Select Payment Method for ₹{amt}**", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"info_(upi|bin)_(\d+)"))
async def info_cb(client, cb):
    method = cb.data.split("_")[1]
    amount = cb.data.split("_")[2]
    if method == "upi":
        details = f"💠 **UPI Payment**\n\nAmount: `₹{amount}`\nUPI ID: `{UPI_ID}`"
    else:
        details = f"🟡 **Binance Payment**\n\nAmount: `₹{amount}`\nBinance ID: `{BINANCE_ID}`"
    
    await cb.edit_message_text(f"{details}\n\n**Note:** Pay and send screenshot to Admin with your User ID: `{cb.from_user.id}`")

# --- ADMIN PANEL ---
@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_menu(client, message):
    buttons = [
        [InlineKeyboardButton("📊 Stats", callback_data="adm_stats"), InlineKeyboardButton("🔐 Force Join", callback_data="adm_fjoin")],
        [InlineKeyboardButton("💰 Plan Settings", callback_data="adm_plans")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_bc")]
    ]
    await message.reply("👑 **Admin Control Panel**", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.command("set_fjoin") & filters.user(ADMIN_ID))
async def set_fjoin_cmd(client, message):
    try:
        _, cid, clink = message.text.split()
        await settings_col.update_one({"type": "fjoin"}, {"$set": {"id": int(cid), "link": clink}}, upsert=True)
        await message.reply("✅ Force Join Updated!")
    except:
        await message.reply("Usage: `/set_fjoin -100xxx https://t.me/xxx`")

@app.on_message(filters.command("add_plan") & filters.user(ADMIN_ID
