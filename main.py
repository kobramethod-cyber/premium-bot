import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- FLASK SERVER FOR RENDER (Port Binding) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running 24/7"

def run_flask():
    # Render uses port 8080 or the one provided in ENV
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# Aapka Diya Hua Mongo URI
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0")) 

# Assets from your input
BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
FORCE_CHANNEL_ID = -1003575487358
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"
STORAGE_CHANNEL_ID = -1003792958477

# --- DATABASE SETUP ---
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def check_premium(user_id):
    user = await users_col.find_one({"user_id": user_id})
    if user and user.get("status") == "premium":
        if datetime.now() < user.get("expiry"):
            return True
        else:
            await users_col.update_one({"user_id": user_id}, {"$set": {"status": "free"}})
    return False

async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(FORCE_CHANNEL_ID, user_id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        return False
    return False

# --- HANDLERS ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    
    if not await is_subscribed(client, user_id):
        return await message.reply(
            "❌ **Access Denied!**\n\nPlease join our update channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel 📢", url=FORCE_CHANNEL_LINK)]])
        )

    if len(message.command) > 1:
        file_id = message.command[1]
        if await check_premium(user_id):
            try:
                await client.copy_message(user_id, STORAGE_CHANNEL_ID, int(file_id))
            except Exception as e:
                await message.reply(f"Error: {e}")
        else:
            await message.reply(
                "🔒 **This Content is Premium!**\n\nYou need an active subscription to view this file.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Buy Premium Plan", callback_data="buy_plans")]])
            )
        return

    await message.reply(
        f"Hello {message.from_user.first_name}!\nWelcome to the Premium Content Bot.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_plans")]])
    )

@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, callback_query: CallbackQuery):
    text = "✦ **PREMIUM PLANS**\n────────────────────\n›› 1 Day : ₹20\n›› 7 Days : ₹70\n›› 15 Days : ₹100\n›› 30 Days : ₹200"
    buttons = [
        [InlineKeyboardButton("1 Day - ₹20", callback_data="pay_20"), InlineKeyboardButton("7 Days - ₹70", callback_data="pay_70")],
        [InlineKeyboardButton("15 Days - ₹100", callback_data="pay_100"), InlineKeyboardButton("30 Days - ₹200", callback_data="pay_200")]
    ]
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"pay_(\d+)"))
async def select_payment(client, callback_query: CallbackQuery):
    amount = callback_query.data.split("_")[1]
    text = f"💳 **Select Payment Method for ₹{amount}**"
    buttons = [
        [InlineKeyboardButton("💠 UPI", callback_data=f"method_upi_{amount}"), InlineKeyboardButton("🟡 Binance", callback_data=f"method_bin_{amount}")]
    ]
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"method_(upi|bin)_(\d+)"))
async def show_pay_details(client, callback_query: CallbackQuery):
    method = callback_query.data.split("_")[1]
    amount = callback_query.data.split("_")[2]
    pay_info = f"💠 **UPI Payment**\n\nAmount: `₹{amount}`\nUPI ID: `{UPI_ID}`" if method == "upi" else f"🟡 **Binance Payment**\n\nAmount: `₹{amount}`\nBinance ID: `{BINANCE_ID}`"
    await callback_query.edit_message_text(pay_info + "\n\n**Note:** Send screenshot after payment.")

@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def save_content(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={msg.id}"
    await message.reply(f"🔗 **Permanent Sharable Link:**\n`{link}`")

@app.on_message(filters.command("approve") & filters.user(ADMIN_ID))
async def approve_user(client, message):
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        days = int(parts[2])
        expiry = datetime.now() + timedelta(days=days)
        await users_col.update_one({"user_id": target_id}, {"$set": {"status": "premium", "expiry": expiry}}, upsert=True)
        await client.send_message(target_id, f"✅ Premium Activated for {days} days!")
        await message.reply(f"User {target_id} approved.")
    except:
        await message.reply("Usage: /approve user_id days")

# --- STARTUP LOGIC ---
async def main():
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    async with app:
        print("Bot Started Successfully!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
