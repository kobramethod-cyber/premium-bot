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

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "25691060"))
API_HASH = os.environ.get("API_HASH", "8ba2c49611687f1747758376916538c3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7832679234:AAHeOsnEwYh-F0T0C4K_D6N44669866") 
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
ADMIN_ID = 1119812744 

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477
FORCE_CHANNEL_LINK = "https://t.me/+mInAMHlOgIo0Yjg1"
FORCE_CHANNEL_ID = -1003575487358

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col = db.users

app = Client("ultra_max_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def check_fjoin(user_id):
    try:
        m = await app.get_chat_member(FORCE_CHANNEL_ID, user_id)
        return m.status not in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]
    except: return False

async def auto_delete(client, chat_id, message_id):
    await asyncio.sleep(600)
    try: await client.delete_messages(chat_id, message_id)
    except: pass

# --- START MENU ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        btns = [[InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)], [InlineKeyboardButton("I am joined ✅", callback_data="check_joined")]]
        return await message.reply(f"Hello {mention}\nJoin our channel to continue.", reply_markup=InlineKeyboardMarkup(btns))

    # Deep Link Handler
    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            sent_msg = await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            await message.reply("⚠️ Deleted in 10 mins.")
            asyncio.create_task(auto_delete(client, uid, sent_msg.id))
            return
        return await message.reply("🔒 Premium Only!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY", callback_data="buy_plans")]]))

    await message.reply(
        f"Hello {mention}!\nWelcome to Premium Bot.", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")],
            [InlineKeyboardButton("👤 MY PLAN", callback_data="my_plan"), InlineKeyboardButton("📞 Contact Admin", url="http://t.me/Provider169_bot")]
        ])
    )

# --- ADMIN PANEL ---
@app.on_message(filters.user(ADMIN_ID) & filters.command("admin"))
async def admin_panel(client, message):
    total = await users_col.count_documents({}); prem = await users_col.count_documents({"status": "premium"})
    text = f"👑 **ULTRA PRO ADMIN PANEL**\n\n📊 Total Users: `{total}`\n💎 Premium: `{prem}`"
    btns = [[InlineKeyboardButton("📊 Stats", callback_data="m_stats"), InlineKeyboardButton("✉️ Broadcast", callback_data="m_bc")],
            [InlineKeyboardButton("❌ Close", callback_data="close_admin")]]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(btns))

# --- ALL BUTTON HANDLER ---
@app.on_callback_query()
async def cb_handler(client, cb):
    uid = cb.from_user.id
    data = cb.data

    if data == "check_joined":
        if await check_fjoin(uid):
            await cb.message.delete()
            await start(client, cb.message)
        else:
            await cb.answer("❌ Please join the channel first!", show_alert=True)

    elif data == "buy_plans":
        text = "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\n›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1.20\n›› 15 Days : ₹120 /$ 2\n›› 1 Months : ₹200 /$ 4"
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("15 DAY", callback_data="p_120_2_15"), InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("p_"):
        _, inr, usd, days = data.split("_")
        btns = [[InlineKeyboardButton("💳 UPI", callback_data=f"i_upi_{inr}"), InlineKeyboardButton("💰 BINANCE", callback_data=f"i_bin_{usd}")]]
        await cb.edit_message_text(f"Select Payment Method for {days} Days:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("i_"):
        m, val = data.split("_")[1], data.split("_")[2]
        if m == "upi":
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26am={val}"
            await cb.message.reply_photo(qr, caption=f"💠 **Scan & Pay ₹{val}**\n\nPayment ke baad screenshot bhejein.")
        else:
            await cb.message.reply(f"🟡 **Binance ID:** `{BINANCE_ID}`\n**Amount:** `{val}$`\n\nPayment ke baad screenshot bhejein.")
        await cb.message.delete()

    elif data == "my_plan":
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            rem = user['expiry'] - datetime.now()
            await cb.answer(f"✅ Premium Active\nDays left: {rem.days}", show_alert=True)
        else:
            await cb.answer("❌ You are a Free User", show_alert=True)

    elif data == "m_stats":
        total = await users_col.count_documents({}); prem = await users_col.count_documents({"status": "premium"})
        await cb.answer(f"Total: {total}\nPremium: {prem}", show_alert=True)

    elif data == "close_admin":
        await cb.message.delete()

    elif data.startswith("apr_"):
        _, u, d = data.split("_")
        exp = datetime.now() + timedelta(days=int(d))
        await users_col.update_one({"user_id": int(u)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
        try: await client.send_message(int(u), "✅ **Premium Activated!**\nEnjoy your access.")
        except: pass
        await cb.message.edit_caption(f"Approved for {d} days ✅")

    elif data.startswith("rej_"):
        _, u = data.split("_")
        try: await client.send_message(int(u), "❌ **Payment Rejected!**\nSend original proof.")
        except: pass
        await cb.message.edit_caption("Rejected ❌")

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
