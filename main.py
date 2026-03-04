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

# Database connection with timeout to prevent bot hang
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

async def check_premium(user_id):
    user = await users_db.find_one({"user_id": user_id})
    if user and "expiry" in user:
        if datetime.now() < user["expiry"]:
            return True, user["expiry"]
    return False, None

# --- COMMANDS ---
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    
    # 1. Force Join Check
    if not await is_subscribed(user_id):
        return await message.reply(
            f"Hello {message.from_user.mention}\n\nYou need to join in my Channel/Group to use me\n\nKindly Please join Channel...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join channel", url=FORCE_CHANNEL_LINK)],
                [InlineKeyboardButton("I am joined", callback_data="check_join")]
            ])
        )

    # 2. Link Access Logic (Premium Check)
    if len(message.command) > 1 and message.command[1].startswith("get_"):
        is_p, _ = await check_premium(user_id)
        if not is_p:
            return await message.reply(
                "❗ This content is for Premium Users only.", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_premium")]])
            )
        
        link_id = message.command[1].split("_")[1]
        data = await links_db.find_one({"link_id": link_id})
        if data:
            content = await client.copy_message(user_id, STORAGE_CHANNEL_ID, data["msg_id"])
            warn = await message.reply("⚠️ WARNING: This message will be auto-deleted in 10 minutes!")
            await asyncio.sleep(600)
            try:
                await content.delete()
                await warn.delete()
            except: pass
            return

    # 3. Main Menu
    await message.reply(
        f"Hello {message.from_user.mention}\n\nWelecome to premium bot\n\nPremium ke liye buy premium button tap kare",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 BUY PREMIUM 💎", callback_data="buy_premium")],
            [InlineKeyboardButton("⚙️ MY PLAN ⚙️", callback_data="my_plan")],
            [InlineKeyboardButton("📞 Contact Admin 📞", user_id=ADMIN_ID)]
        ])
    )

@app.on_message(filters.command("link") & filters.user(ADMIN_ID) & filters.reply)
async def gen_link(client, message):
    sent = await message.reply_to_message.forward(STORAGE_CHANNEL_ID)
    link_id = str(sent.id)
    await links_db.insert_one({"link_id": link_id, "msg_id": sent.id})
    await message.reply(f"✅ Permanent Link:\n`https://t.me/{client.me.username}?start=get_{link_id}`")

# --- CALLBACKS ---
@app.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    uid = query.from_user.id

    if data == "check_join":
        if await is_subscribed(uid):
            await query.answer("Thank you for joining!", show_alert=True)
            await start_cmd(client, query.message)
        else:
            await query.answer("Please join the channel first!", show_alert=True)

    elif data == "buy_premium":
        cap = (
            "✦ 𝗦𝗛𝗢𝗥𝗧𝗡𝗘𝗥 𝗣𝗟𝗔𝗡𝗦\nᴅᴜʀᴀᴛɪᴏɴ & ᴘʀɪᴄᴇ\n────────────────────\n"
            "›› 1 days : ₹30 / $ 0.50\n›› 7 Days : ₹70 / $ 1\n"
            "›› 15 Days : ₹120 / $ 1.50\n›› 1 Months : ₹200 / $ 2.50\n\n"
            "❐ 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗠𝗘𝗧𝗛𝗢𝗗𝗦\n❐ 𝗉𝖺𝗒𝗍𝗆 • 𝗀𝗉𝖺𝗒 • 𝗉𝗁𝗈𝗇𝖾 𝗉𝖺𝗒 • 𝗎𝗉𝗂 𝖺𝗇𝖽 𝗊𝗋 and binnance\n────────────────────\n"
            "✦ Pʀᴇᴍɪᴜᴍ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴏɴᴄᴇ ᴘᴀɪᴅ\n✦ 𝗔𝗙𝗧𝗘𝗥 𝗣𝗔𝗬𝗠𝗘𝗡𝗧:\n❐ Sᴇɴᴅ ᴀ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ & ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍɪɴᴜᴛᴇꜱ ғᴏʀ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ✓"
        )
        btns = [[InlineKeyboardButton(f"{d} DAY", callback_data=f"p_{d}")] for d in [1, 7, 15, 30]]
        await query.message.edit(cap, reply_markup=InlineKeyboardMarkup(btns))

    elif data.startswith("p_"):
        day = data.split("_")[1]
        await query.message.edit(f"Select Payment Method for {day} Day Plan:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 PAY WITH UPI", callback_data=f"pay_upi_{day}")],
                [InlineKeyboardButton("💰 PAY WITH BINANCE", callback_data=f"pay_bin_{day}")]
            ]))

    elif data.startswith("pay_upi_"):
        day = data.split("_")[2]
        amt = {"1": 30, "7": 70, "15": 120, "30": 200}[day]
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}&am={amt}&cu=INR"
        await query.message.reply_photo(qr, caption=f"✦ Plan: {day} Day\n✦ Amount: ₹{amt}\n\nSend Screenshot after payment.")

    elif data.startswith("pay_bin_"):
        day = data.split("_")[2]
        amt = {"1": "0.50", "7": "1", "15": "1.50", "30": "2.50"}[day]
        await query.message.reply(f"✦ Plan: {day} Day\n✦ Amount: ${amt}\n✦ Binance ID: `{BINANCE_ID}`\n\nSend Screenshot after payment.")

    elif data.startswith("approve_"):
        _, target, d = data.split("_")
        exp = datetime.now() + timedelta(days=int(d))
        await users_db.update_one({"user_id": int(target)}, {"$set": {"expiry": exp}}, upsert=True)
        await client.send_message(int(target), f"✅ Pᴀʏᴍᴇɴᴛ Sᴜᴄᴄᴇssғᴜʟ!\n\n🎉 Pʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ғᴏʀ {d} day!\n💎 Eɴᴊᴏʏ ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss!")
        await query.message.edit(f"✅ Approved User {target} for {d} days.")

# --- PHOTO HANDLER ---
@app.on_message(filters.photo & filters.private)
async def photo_handler(client, message):
    if message.from_user.id == ADMIN_ID: return
    await message.reply("✅ Membership Request Submitted!\n\n⚡ Your proof is being verified.\n📝 Status: Pending\n⏳ Time: 1 Hours (Max)\n\n🟢 You will be notified automatically once membership are added.")
    await message.forward(ADMIN_ID)
    await client.send_message(ADMIN_ID, f"New Payment Request\nUser ID: `{message.from_user.id}`\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Approve 1 Day", callback_data=f"approve_{message.from_user.id}_1")],
            [InlineKeyboardButton("Approve 7 Day", callback_data=f"approve_{message.from_user.id}_7")],
            [InlineKeyboardButton("Approve 15 Day", callback_data=f"approve_{message.from_user.id}_15")],
            [InlineKeyboardButton("Approve 30 Day", callback_data=f"approve_{message.from_user.id}_30")],
            [InlineKeyboardButton("Reject", callback_data="reject")]
        ]))

# --- MONITOR ---
async def monitor():
    while True:
        now = datetime.now()
        async for user in users_db.find({"expiry": {"$exists": True}}):
            if now < user["expiry"] <= now + timedelta(hours=1) and not user.get("w"):
                await app.send_message(user["user_id"], "⚠️ Reminder: Your premium membership will expire in 1 hour.\n\nTo renew your premium membership, please Contact Our Admins.")
                await users_db.update_one({"user_id": user["user_id"]}, {"$set": {"w": True}})
            elif now >= user["expiry"]:
                await app.send_message(user["user_id"], "❗ ›› Your premium membership has expired.\n\nRenew your premium membership to continue enjoying the benefits. Contact Our Admins.")
                await users_db.update_one({"user_id": user["user_id"]}, {"$unset": {"expiry": "", "w": ""}})
        await asyncio.sleep(60)

async def main():
    Thread(target=run_server).start()
    await app.start()
    asyncio.create_task(monitor())
    print("Bot is started successfully!") 
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
