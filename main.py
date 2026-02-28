import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER PORT FIX ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running"

def run_flask():
    # Render PORT environment variable zaroori hai
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
STORAGE_CHANNEL_ID = -1003792958477

# Database connection
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

# Client Initialization
app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- BASIC HANDLER ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply("Bot is Online! Use /buy for plans.")

@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def link_gen(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    bot_me = await client.get_me()
    await message.reply(f"Link: https://t.me/{bot_me.username}?start={msg.id}")

# --- STARTUP LOGIC ---
async def start_bot():
    # 1. Flask ko background thread mein start karein (Render ke liye)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Bot start karein
    await app.start()
    print(">>> BOT STARTED SUCCESSFULLY")
    
    # 3. Bot ko idle mode mein rakhein
    await idle()
    
    # 4. Stop gracefully
    await app.stop()

if __name__ == "__main__":
    # Naye python versions ke liye loop handle karna
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
