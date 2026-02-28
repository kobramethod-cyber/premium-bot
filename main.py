import os
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- CONFIGURATION (Add your API_ID, API_HASH, BOT_TOKEN in Render Env Vars) ---
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0")) # Apni numeric ID yahan ya Env Var mein daalein

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

# --- UTILS: Check Premium Status ---
async def check_premium(user_id):
    user = await users_col.find_one({"user_id": user_id})
    if user and user.get("status") == "premium":
        if datetime.now() < user.get("expiry"):
            return True
        else:
            await users_col.update_one({"user_id": user_id}, {"$set": {"status": "free"}})
    return False

# --- FORCE JOIN CHECK ---
async def is_subscribed(client, user_id):
    try:
        member = await client.get_chat_member(FORCE_CHANNEL_ID, user_id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except:
        return False
    return False

# --- START COMMAND (Handling Deep Links) ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    
    # Check Force Join
    if not await is_subscribed(client, user_id):
        return await message.reply(
            "❌ **Access Denied!**\n\nPlease join our update channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel 📢", url=FORCE_CHANNEL_LINK)]])
        )

    # Deep Link Handling (if ?start=msgid)
    if len(message.command) > 1:
        file_id = message.command[1]
        if await check_premium(user_id):
            await client.copy_message(user_id, STORAGE_CHANNEL_ID, int(file_id))
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

# --- BUY PLANS MENU ---
@app.on_callback_query(filters.regex("buy_plans"))
async def show_plans(client, callback_query: CallbackQuery):
    text = "✦ **PREMIUM PLANS**\n────────────────────\n›› 1 Day : ₹20\n›› 7 Days : ₹70\n›› 15 Days : ₹100\n›› 30 Days : ₹200"
    buttons = [
        [InlineKeyboardButton("1 Day - ₹20", callback_data="pay_20"), InlineKeyboardButton("7 Days - ₹70", callback_data="pay_70")],
        [InlineKeyboardButton("15 Days - ₹100", callback_data="pay_100"), InlineKeyboardButton("30 Days - ₹200", callback_data="pay_200")]
    ]
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- PAYMENT METHOD PAGE ---
@app.on_callback_query(filters.regex(r"pay_(\d+)"))
async def select_payment(client, callback_query: CallbackQuery):
    amount = callback_query.data.split("_")[1]
    text = f"💳 **Select Payment Method for ₹{amount}**"
    buttons = [
        [InlineKeyboardButton("💠 UPI", callback_data=f"method_upi_{amount}"), InlineKeyboardButton("🟡 Binance", callback_data=f"method_bin_{amount}")]
    ]
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- PAYMENT DETAILS DISPLAY ---
@app.on_callback_query(filters.regex(r"method_(upi|bin)_(\d+)"))
async def show_pay_details(client, callback_query: CallbackQuery):
    method = callback_query.data.split("_")[1]
    amount = callback_query.data.split("_")[2]
    
    if method == "upi":
        pay_info = f"💠 **UPI Payment**\n\nAmount: `₹{amount}`\nUPI ID: `{UPI_ID}`\n\n**Note:** Pay exact amount and send screenshot."
    else:
        pay_info = f"🟡 **Binance Payment**\n\nAmount: `₹{amount}`\nBinance ID: `{BINANCE_ID}`\n\n**Note:** Send screenshot after payment."
    
    await callback_query.edit_message_text(pay_info)

# --- ADMIN: BROADCAST ---
@app.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast(client, message):
    users = users_col.find({})
    count = 0
    async for user in users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            count += 1
        except: pass
    await message.reply(f"✅ Broadcast sent to {count} users.")

# --- ADMIN: GENERATE SHARABLE LINK ---
@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def save_content(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={msg.id}"
    await message.reply(f"🔗 **Permanent Sharable Link:**\n`{link}`")

print("Bot is Starting...")
app.run()
