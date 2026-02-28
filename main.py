import os
import asyncio
import threading
from flask import Flask
from pyrogram import Client, filters, idle, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

# --- RENDER WEB SERVER ---
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

# --- HANDLERS ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid = message.from_user.id
    fjoin = await get_fjoin()
    if not await is_subscribed(uid):
        return await message.reply("Join first!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join", url=fjoin['link'])]]))
    
    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium" and datetime.now() < user.get("expiry"):
            return await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
        return await message.reply("Premium Required!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy", callback_data="buy_plans")]]))
    
    await message.reply("Welcome!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Buy Premium", callback_data="buy_plans")]]))

@app.on_callback_query(filters.regex("buy_plans"))
async def buy_plans(client, cb):
    plans = await plans_col.find().to_list(length=10)
    if not plans:
        await plans_col.insert_many([{"name":"1 Day","price":20,"days":1},{"name":"30 Days","price":200,"days":30}])
        plans = await plans_col.find().to_list(length=10)
    btns = [[InlineKeyboardButton(f"{p['name']} - ₹{p['price']}", callback_data=f"pay_{p['price']}")] for p in plans]
    await cb.edit_message_text("Plans:", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"pay_(\d+)"))
async def pay_method(client, cb):
    amt = cb.data.split("_")[1]
    btns = [[InlineKeyboardButton("UPI", callback_data=f"info_upi_{amt}"), InlineKeyboardButton("Binance", callback_data=f"info_bin_{amt}")]]
    await cb.edit_message_text(f"Pay ₹{amt}", reply_markup=InlineKeyboardMarkup(btns))

@app.on_callback_query(filters.regex(r"info_(upi|bin)_(\d+)"))
async def info(client, cb):
    m, a = cb.data.split("_")[1], cb.data.split("_")[2]
    det = f"UPI: `{UPI_ID}`" if m == "upi" else f"Binance: `{BINANCE_ID}`"
    await cb.edit_message_text(f"{det}\nAmt: ₹{a}\nSend screenshot to Admin with ID: `{cb.from_user.id}`")

# --- ADMIN PANEL ---
@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin(client, message):
    btns = [[InlineKeyboardButton("Force Join", callback_data="set_fj"), InlineKeyboardButton("Add Plan", callback_data="add_p")]]
    await message.reply("Admin Panel", reply_markup=InlineKeyboardMarkup(btns))

@app.on_message(filters.command("approve") & filters.user(ADMIN_ID))
async def approve(client, message):
    try:
        _, uid, days = message.text.split()
        exp = datetime.now() + timedelta(days=int(days))
        await users_col.update_one({"user_id": int(uid)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        await client.send_message(int(uid), "Premium Activated!")
        await message.reply("Approved!")
    except: await message.reply("Usage: /approve ID days")

@app.on_message(filters.user(ADMIN_ID) & filters.forwarded)
async def gen_link(client, message):
    msg = await message.copy(STORAGE_CHANNEL_ID)
    me = await client.get_me()
    await message.reply(f"Link: https://t.me/{me.username}?start={msg.id}")

# --- START BOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
