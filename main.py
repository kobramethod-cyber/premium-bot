import os
import asyncio
import threading
import urllib.parse
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
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MONGO_URI = "mongodb+srv://Kobra:Kartik9307@cluster0.oxqflcj.mongodb.net/premium_bot?retryWrites=true&w=majority"
PRIMARY_ADMIN = int(os.environ.get("ADMIN_ID", "0"))

BINANCE_ID = "1119812744"
UPI_ID = "BHARATPE09910027091@yesbankltd"
STORAGE_CHANNEL_ID = -1003792958477
CONTACT_URL = "http://t.me/Provider169_bot"

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.premium_bot
users_col, settings_col = db.users, db.settings

app = Client("premium_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
async def get_admins():
    data = await settings_col.find_one({"type": "admins"})
    admin_list = data['list'] if data else []
    if PRIMARY_ADMIN not in admin_list: admin_list.append(PRIMARY_ADMIN)
    return admin_list

async def get_fjoins():
    data = await settings_col.find_one({"type": "fjoins"})
    return data['channels'] if data else [{"id": -1003575487358, "link": "https://t.me/+mInAMHlOgIo0Yjg1"}]

async def check_fjoin(user_id):
    channels = await get_fjoins()
    for ch in channels:
        try:
            m = await app.get_chat_member(ch['id'], user_id)
            if m.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]: return False
        except: return False
    return True

# --- 🚀 START ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    uid, mention = message.from_user.id, message.from_user.mention
    if not await check_fjoin(uid):
        channels = await get_fjoins()
        btns = [[InlineKeyboardButton("Join channel", url=ch['link'])] for ch in channels]
        btns.append([InlineKeyboardButton("I am joined ✅", callback_data="check_joined")])
        return await message.reply(f"Hello {mention}\n\nYou need to join in my Channel/Group to use me\n\nKindly Please join Channel...", reply_markup=InlineKeyboardMarkup(btns))

    if len(message.command) > 1:
        fid = message.command[1]
        user = await users_col.find_one({"user_id": uid})
        if user and user.get("status") == "premium":
            try: return await client.copy_message(uid, STORAGE_CHANNEL_ID, int(fid))
            except: return await message.reply("❌ File not found.")
        return await message.reply("🔒 **This content is for Premium Users only!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")]]))

    await message.reply(f"Hello {mention}\n\nWelecome to premium bot\n\nPremium ke liye buy premium button tap kare", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_plans")], [InlineKeyboardButton("📞 Contact Admin 📞", url=CONTACT_URL)]]))

# --- 💰 CALLBACK HANDLER (FIXED) ---
@app.on_callback_query()
async def callback_handler(client, cb):
    uid = cb.from_user.id
    data = cb.data
    admins = await get_admins()

    if data == "check_joined":
        if await check_fjoin(uid):
            await cb.message.delete()
            await start(client, cb.message)
        else: await cb.answer("Join channel first! ❌", show_alert=True)

    elif data == "buy_plans":
        text = ("✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\nᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ\n────────────────────\n"
                "›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 /$ 1.20\n›› 15 Days : ₹120 /$ 2\n›› 1 Months : ₹200 /$ 4\n\n"
                "❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦\n❐ 𝗉𝖺𝗒𝗍𝗆 • 𝗀𝗉𝖺𝗒 • 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • 𝗎𝗉𝗂 𝖺𝗇𝖽 𝗊𝗋 and binnance\n────────────────────\n"
                "✦ Pʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴏɴᴄᴇ ᴘᴀɪᴅ\n✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ a ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓")
        btns = [[InlineKeyboardButton("1 DAY", callback_data="p_30_0.50_1"), InlineKeyboardButton("7 DAY", callback_data="p_70_1.20_7")],
                [InlineKeyboardButton("15 DAY", callback_data="p_120_2_15"), InlineKeyboardButton("30 DAY", callback_data="p_200_4_30")]]
        await cb.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("p_"):
        _, inr, usd, days = data.split("_")
        btns = [[InlineKeyboardButton("💳 PAY WITH UPI", callback_data=f"i_upi_{inr}_{days}"), InlineKeyboardButton("💰 PAY WITH BINANCE", callback_data=f"i_bin_{usd}_{days}")]]
        await cb.edit_message_text(f"💳 **Payment for {days} Days**\nChoose Method:", reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("i_"):
        m, val, d = data.split("_")[1], data.split("_")[2], data.split("_")[3]
        if m == "upi":
            qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26am={val}%26cu=INR"
            await cb.message.reply_photo(qr, caption=f"💠 **Scan & Pay ₹{val}**\nUPI ID: `{UPI_ID}`\n\n✅ Pay ke baad screenshot bhejiye.")
        else:
            await cb.message.reply(f"🟡 **Binance ID:** `{BINANCE_ID}`\nAmount: **{val}$**\n\n✅ Pay karne ke baad screenshot bhejiye.")
        await cb.message.delete()

    # Admin Panel Logic
    elif uid in admins:
        if data == "adm_gen_link":
            btns = [[InlineKeyboardButton("Video add", callback_data="add_file"), InlineKeyboardButton("Photo add", callback_data="add_file")],
                    [InlineKeyboardButton("Link add", callback_data="add_file")], [InlineKeyboardButton("🔙 Back", callback_data="back_adm")]]
            await cb.edit_message_text("📤 **Generate Permanent Link**\n\nForward your Video, Photo, or Link to the bot now.", reply_markup=InlineKeyboardMarkup(btns))
        elif data == "add_file": await cb.answer("Just forward the file to the bot!", show_alert=True)
        elif data == "back_adm": await admin_panel(client, cb.message)
        elif data == "m_stats":
            total = await users_col.count_documents({})
            prem = await users_col.count_documents({"status": "premium"})
            await cb.edit_message_text(f"📊 **Stats**\nTotal: {total}\nPremium: {prem}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="back_adm")]]))
        elif data == "m_bc": await cb.answer("Reply to any message with /broadcast", show_alert=True)
        elif data.startswith("apr_"):
            _, user_id, days = data.split("_")
            exp = datetime.now() + timedelta(days=int(days))
            await users_col.update_one({"user_id": int(user_id)}, {"$set": {"status": "premium", "expiry": exp}}, upsert=True)
            await client.send_message(int(user_id), f"✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ!\n🎉 Pʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ғᴏʀ {days} day!")
            await cb.message.edit_caption(f"Approved for {days} Days ✅")
        elif data.startswith("rej_"):
            await client.send_message(int(data.split("_")[1]), "❌ **Payment Rejected!**")
            await cb.message.edit_caption("Rejected ❌")

# --- 📸 PHOTO HANDLER ---
@app.on_message(filters.photo & filters.private)
async def handle_ss(client, message):
    uid = message.from_user.id
    if uid in await get_admins(): return
    btns = InlineKeyboardMarkup([[InlineKeyboardButton("1 day approve", callback_data=f"apr_{uid}_1"), InlineKeyboardButton("7 day approve", callback_data=f"apr_{uid}_7")],
                                 [InlineKeyboardButton("15 day approve", callback_data=f"apr_{uid}_15"), InlineKeyboardButton("1 month approve", callback_data=f"apr_{uid}_30")],
                                 [InlineKeyboardButton("Reject", callback_data=f"rej_{uid}")]])
    await message.copy(PRIMARY_ADMIN, caption=f"📩 **Payment Proof**\nUser: `{uid}`", reply_markup=btns)
    await message.reply("✅ Membership Request Submitted!\n\n⚡ Your proof is being verified.\n📝 Status: Pending\n⏳ Time: 1 Hours (Max)\n\n🟢 You will be notified automatically once funds are added.")

# --- 👑 ADMIN PANEL COMMAND ---
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message):
    if message.from_user.id not in await get_admins(): return
    total = await users_col.count_documents({})
    prem = await users_col.count_documents({"status": "premium"})
    text = f"👑 **Admin Panel**\nTotal: {total} | Prem: {prem}"
    btns = [[InlineKeyboardButton("🔗 Generate Permanent Link", callback_data="adm_gen_link")],
            [InlineKeyboardButton("📝 Plan Mngr", callback_data="m_plan"), InlineKeyboardButton("📢 F-Join Mngr", callback_data="m_fj")],
            [InlineKeyboardButton("👥 Admin Mngr", callback_data="m_adm"), InlineKeyboardButton("📊 Stats", callback_data="m_stats")],
            [InlineKeyboardButton("✉️ Broadcast", callback_data="m_bc")]]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(btns))

# --- LINK GENERATOR (FORWARD) ---
@app.on_message((filters.video | filters.photo | filters.document) & filters.private)
async def forward_handler(client, message):
    if message.from_user.id not in await get_admins(): return
    msg = await message.copy(STORAGE_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={msg.id}"
    await message.reply(f"✅ **Permanent Link Generated:**\n\n`{link}`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={link}")]]))

# --- BOOT ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await app.start()
    await idle()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
