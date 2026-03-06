import os
import asyncio
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

# --- RENDER PORT FIX ---
server = Flask('')
@server.route('/')
def home(): return "Bot is Alive 24/7"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- CONFIG ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
MONGO_URI = os.environ.get("MONGO_URI")

STORAGE_CHANNEL_ID = -1003792958477
UPI_ID = "BHARATPE09910027091@yesbankltd"
BINANCE_ID = "1119812744"
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"
FORCE_CHANNEL_ID = -1003575487358

# Database connection with timeout
db_client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = db_client.premium_bot
users_db = db.users
links_db = db.links

app = Client("PremiumBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPERS ---
async def is_subscribed(user_id):
    try:
        member = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.MEMBER]
    except: return False

# --- COMMANDS ---
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    print(f"Start command received from {user_id}") # LOG FOR DEBUGGING
    
    if not await is_subscribed(user_id):
        return await message.reply(f"Hello {message.from_user.mention}\n\nYou need to join in my Channel/Group to use me\n\nKindly Please join Channel...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)],
                [InlineKeyboardButton("I am joined", callback_data="check_join")]
            ]))

    await message.reply(f"Hello {message.from_user.mention}\n\nWelecome to premium bot\n\nPremium ke liye buy premium button tap kare",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_premium")],
            [InlineKeyboardButton("⚙️ MY PLAN ⚙️", callback_data="my_plan")],
            [InlineKeyboardButton("📞 Contact Admin 📞", user_id=ADMIN_ID)]
        ]))

# --- CALLBACKS & OTHER LOGIC ---
@app.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    if query.data == "buy_premium":
        cap = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\nᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ\n────────────────────\n›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 / $ 1\n›› 15 Days : ₹120 / $ 1.50\n›› 1 Months : ₹200 / $ 2.50\n\n❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦\n❐ 𝗉𝖺𝗒𝗍𝗆 • 𝗀𝗉𝖺𝗒 • 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • 𝗎𝗉𝗂 𝖺𝗇ᴅ 𝗊𝗋 and binnance\n────────────────────\n✦ Pʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴏɴᴄᴇ ᴘᴀɪᴅ\n✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓"
        btns = [[InlineKeyboardButton(f"{d} DAY", callback_data=f"p_{d}")] for d in [1, 7, 15, 30]]
        await query.message.edit(cap, reply_markup=InlineKeyboardMarkup(btns))

async def main():
    Thread(target=run_server).start()
    print("Starting Pyrogram Client...")
    try:
        await app.start()
        print(">>> BOT IS LIVE AND READY! <<<")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
