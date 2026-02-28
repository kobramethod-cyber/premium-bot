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
    return data if data else {"id": -1003575487358, "link": "https://t.me/+mInAMHlOgIo0Yjg1"}

async def is_subscribed(user_id):
    fjoin = await get_fjoin()
    try:
        member = await app.get_chat_member(fjoin['id'], user_id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except: return False
    return False

# --- USER HANDLERS ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    fjoin = await get_fjoin()
    
    if not await is_subscribed(user_id):
        return await message.reply("❌ Join our channel to use the bot!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url=fjoin['link'])]]))

    if len(message.command) > 1:
        file_id = message.command[1]
        user = await users_col.find_one({"user_id": user_id})
        if user and user.get("status") == "premium" and datetime.now() < user.get("expiry"):
            return await client.copy_message(user_id, STORAGE_CHANNEL_ID, int(file_id))
        else:
            return await message.reply("🔒 Premium required!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Buy Plan", callback_data="buy_plans")]]))

    await message.reply(f"Hello {message.from_user.first_name}!\nWelcome to Premium Bot.", 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_plans")]]))

@app.on_callback_query(filters.regex("buy
