import os
import asyncio
import threading
import urllib.parse
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER WEB SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "25691060")) # Apna sahi API_ID dalein
API_HASH = os.environ.get("API_HASH", "8ba2c49611687f1747758376916538c3") # Apna sahi Hash dalein
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
PRIMARY_ADMIN = int(os.environ.get("ADMIN_ID", "1119812744")) # Yahan APNA ID check karein

STORAGE_CHANNEL_ID = -1003792958477
UPI_ID = "BHARATPE09910027091@yesbankltd"
BINANCE_ID = "1119812744"

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- LINK GENERATOR LOGIC (FOR ADMIN ONLY) ---
@app.on_message((filters.photo | filters.video | filters.document | filters.audio) & filters.private)
async def link_generator(client, message):
    if message.from_user.id != PRIMARY_ADMIN:
        # Agar user photo bhej raha hai toh wo Payment Screenshot hai
        if message.photo:
            uid = message.from_user.id
            btns = InlineKeyboardMarkup([
                [InlineKeyboardButton("1 day", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day", callback_data=f"apr_{uid}_7")],
                [InlineKeyboardButton("15 day", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month", callback_data=f"apr_{uid}_30")],
                [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]
            ])
            await message.copy(PRIMARY_ADMIN, caption=f"📩 **Payment Proof**\nUser: `{uid}`", reply_markup=btns)
            await message.reply("✅ Membership Request Submitted!\n\n⚡ Your proof is being verified.\n📝 Status: Pending\n⏳ Time: 1 Hours (Max)\n\n🟢 You will be notified automatically once funds are added.")
        return

    # AGAR ADMIN BHEJ RAHA HAI (PHOTO/VIDEO/FILE)
    wait = await message.reply("⏳ Generating Permanent Link...")
    try:
        msg = await message.copy(STORAGE_CHANNEL_ID)
        link = f"https://t.me/{(await client.get_me()).username}?start={msg.id}"
        await wait.edit(f"✅ **Permanent Link Generated:**\n\n`{link}`", 
                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={link}")]]))
    except Exception as e:
        await wait.edit(f"❌ Error: {e}\nMake sure bot is Admin in Storage Channel.")

# --- CALLBACK HANDLER (ALL BUTTONS) ---
@app.on_callback_query()
async def cb_handler(client, cb):
    data = cb.data
    uid = cb.from_user.id

    if data == "buy_plans":
        text = ("✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1.20\n›› 15 Days : ₹120 /$ 2\n›› 1 Months : ₹200 /$ 4")
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("15 DAY", callback_data="p_120_2_15"), InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("p_"):
        _, inr, usd, days = data.split("_")
        btns = [[InlineKeyboardButton("💳 UPI", callback_data=f"i_upi_{inr}"), InlineKeyboardButton("💰 BINANCE", callback_data=f"i_bin_{usd}")]]
        await cb.edit_message_text(f"💳 Payment for {days} Days", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("i_"):
        m, val = data.split("_")[1], data.split("_")[2]
        if m == "upi":
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26am={val}%26cu=INR"
            await cb.message.reply_photo(qr, caption=f"💠 Pay ₹{val} to `{UPI_ID}`\nBhejne ke baad screenshot dein.")
        else:
            await cb.message.reply(f"🟡 Binance ID: `{BINANCE_ID}`\nAmount: {val}$")
        await cb.message.delete()

    elif data.startswith("apr_") and uid == PRIMARY_ADMIN:
        _, user_id, days = data.split("_")
        exp = datetime.now() + timedelta(days=int(days))
        await users_col.update_one({"user_id": int(user_id)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(user_id), f"✅ Premium Activated for {days} days!")
        await cb.message.edit_caption(f"Approved ✅ ({days} days)")

    elif data.startswith("rej_") and uid == PRIMARY_ADMIN:
        await client.send_message(int(data.split("_")[1]), "❌ Payment Rejected!")
        await cb.message.edit_caption("Rejected ❌")

# --- START COMMAND ---
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": message.from_user.id})
        if user and user.get("status") == "premium":
            return await client.copy_message(message.from_user.id, STORAGE_CHANNEL_ID, int(fid))
        return await message.reply("🔒 Premium Only!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy", callback_data="buy_plans")]]))
    
    await message.reply("Welcome!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 Buy Premium", callback_data="buy_plans")]]))

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
