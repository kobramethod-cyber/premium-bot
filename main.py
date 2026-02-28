import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER PORT BINDING ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running"

def run_flask():
    # Render ke liye port setup
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

# Database initialization
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

# Client Initialization
app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HANDLERS ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply("✅ **Bot is Online!**\n\nUse /buy to see premium plans.")

@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def link_gen(client, message):
    try:
        msg = await message.copy(STORAGE_CHANNEL_ID)
        bot_me = await client.get_me()
        await message.reply(f"🔗 **Sharable Link:**\n`https://t.me/{bot_me.username}?start={msg.id}`")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- STARTUP ---
async def start_bot():
    # Background mein Flask chalana (Render ke liye)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Bot start
    await app.start()
    print(">>> BOT IS LIVE NOW")
    
    # Idle mode (keeps bot running)
    await idle()
    
    # Stop
    await app.stop()

if __name__ == "__main__":
    try:
        # Purana get_event_loop() use kar rahe hain compatibility ke liye
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
