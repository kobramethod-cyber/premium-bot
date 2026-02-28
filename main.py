import os
import asyncio
import threading
import uvloop
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# Install uvloop for better performance and fixing loop errors
uvloop.install()

# --- FLASK SERVER ---
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
FORCE_CHANNEL_ID = -1003575487358
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"
STORAGE_CHANNEL_ID = -1003792958477

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

# IMPORTANT: Set sleep_threshold to avoid flood waite
app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, sleep_threshold=60)

# --- HANDLERS ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    # Force Join Check
    try:
        member = await client.get_chat_member(FORCE_CHANNEL_ID, user_id)
    except:
        return await message.reply("Join channel first!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=FORCE_CHANNEL_LINK)]]))

    if len(message.command) > 1:
        file_id = message.command[1]
        user = await users_col.find_one({"user_id": user_id})
        if user and user.get("status") == "premium" and datetime.now() < user.get("expiry"):
            await client.copy_message(user_id, STORAGE_CHANNEL_ID, int(file_id))
        else:
            await message.reply("Premium required!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy", callback_data="buy_plans")]]))
        return
    await message.reply("Welcome!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Plans", callback_data="buy_plans")]]))

@app.on_callback_query(filters.regex("buy_plans"))
async def plans(client, cb):
    await cb.edit_message_text("Plans: 1D: ₹20 | 7D: ₹70 | 15D: ₹100 | 30D: ₹200", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("UPI", callback_data="pay_upi"), InlineKeyboardButton("Binance", callback_data="pay_bin")]
    ]))

@app.on_callback_query(filters.regex("pay_"))
async def pay(client, cb):
    method = cb.data.split("_")[1]
    details = f"UPI: {UPI_ID}" if method == "upi" else f"Binance: {BINANCE_ID}"
    await cb.edit_message_text(f"{details}\nSend screenshot to Admin.")

@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def link_gen(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    await message.reply(f"Link: https://t.me/{(await client.get_me()).username}?start={msg.id}")

@app.on_message(filters.command("approve") & filters.user(ADMIN_ID))
async def approve(client, message):
    try:
        _, uid, days = message.text.split()
        exp = datetime.now() + timedelta(days=int(days))
        await users_col.update_one({"user_id": int(uid)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(uid), "Activated!")
        await message.reply("Done.")
    except: await message.reply("/approve user_id days")

# --- BOOT ---
async def start_bot():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    print("Bot is Live!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
