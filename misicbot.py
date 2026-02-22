import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped
from youtubesearchpython import VideosSearch
import yt_dlp

# ================= CONFIG =================
API_ID = 32405552        # <- apna API ID
API_HASH = "4fe86dac719c9808c9324d3e1bada507"     # <- apna API HASH
BOT_TOKEN = "8548297931:AAE_HwOS9h96ofjXCkhI0skckR5fDuLadSs"   # <- BotFather token
SESSION_STRING = "BQHueDAAVjTcXn8uR9XmwLLJsg8htZAa3mX6TWuQtR1AgapQvRFJEwIVtW64ulzgZsg DYIOQH6GULPJauOR4nUbWAnZVUd_wJ3S6zdDtdz613batSt6G-GWBrTaSXXHnTn-9V9 ujBZ1t9JLkS5gSr54PcbRIItB_CxcGHu1hi4aLCxevHMLz6u58Y_TQfcPvPDwpM2l5R zdqcdtXA7WofW2XUa5BYjl8I-0aFKJxh-u6rkQ83S1Ffzqh0Zfj586mQkguIOool0J7 a4pf5auAcLE7EBblFD1HP7bCNGAgPtDsQno-307rAWERR_R7Iv-_rLpSYXtuYHpAGNtDYpvpEmvGgsrj7QAΑΑΑΗIkEAbΑΑ"

SUPPORT_CHANNEL = "vrtxportal"   # without @
SUPPORT_GROUP = "a1chatting"     # without @

START_IMAGE = "https://telegra.ph/file/8c5c6cddc3d5f2e7c7d.jpg"
# ========================================

app = Client(
    "musicbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    session_string=SESSION_STRING
)

pytgcalls = PyTgCalls(app)
queues = {}

# ---------- FORCE JOIN ----------
async def force_join(client, message):
    try:
        await client.get_chat_member(f"@{SUPPORT_CHANNEL}", message.from_user.id)
        return True
    except UserNotParticipant:
        await message.reply(
            "❌ **Use karne se pehle join karo**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")],
                [InlineKeyboardButton("💬 Support Group", url=f"https://t.me/{SUPPORT_GROUP}")]
            ])
        )
        return False

# ---------- YT AUDIO ----------
def get_audio(query):
    search = VideosSearch(query, limit=1)
    link = search.result()["result"][0]["link"]

    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "outtmpl": "song.%(ext)s",
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        return f"song.{info['ext']}"

# ---------- START ----------
@app.on_message(filters.command("start"))
async def start(_, m):
    if not await force_join(app, m):
        return

    me = await app.get_me()
    await m.reply_photo(
        photo=START_IMAGE,
        caption="🎧 **MUSIC VC BOT**\n\n"
                "➤ Group me add karo\n"
                "➤ Voice Chat start karo\n"
                "➤ `/play song name`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{me.username}?startgroup=true")],
            [InlineKeyboardButton("📢 Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")],
            [InlineKeyboardButton("💬 Support", url=f"https://t.me/{SUPPORT_GROUP}")]
        ])
    )

# ---------- PLAY ----------
@app.on_message(filters.command("play") & filters.group)
async def play(_, m):
    if not await force_join(app, m):
        return

    if len(m.command) < 2:
        return await m.reply("❌ Song name likho")

    query = " ".join(m.command[1:])
    msg = await m.reply("🔎 Searching...")

    audio = get_audio(query)
    chat_id = m.chat.id

    if chat_id in queues:
        queues[chat_id].append(audio)
        return await msg.edit("➕ Queue me add ho gaya")

    queues[chat_id] = [audio]
    await pytgcalls.join_group_call(chat_id, AudioPiped(audio))
    await msg.edit(f"▶️ **Playing:** {query}")

# ---------- CONTROLS ----------
@app.on_message(filters.command("pause") & filters.group)
async def pause(_, m):
    await pytgcalls.pause_stream(m.chat.id)
    await m.reply("⏸ Paused")

@app.on_message(filters.command("resume") & filters.group)
async def resume(_, m):
    await pytgcalls.resume_stream(m.chat.id)
    await m.reply("▶️ Resumed")

@app.on_message(filters.command("skip") & filters.group)
async def skip(_, m):
    chat_id = m.chat.id
    if chat_id not in queues or len(queues[chat_id]) == 1:
        return await m.reply("❌ Queue empty")

    queues[chat_id].pop(0)
    await pytgcalls.change_stream(chat_id, AudioPiped(queues[chat_id][0]))
    await m.reply("⏭ Skipped")

@app.on_message(filters.command("end") & filters.group)
async def end(_, m):
    queues.pop(m.chat.id, None)
    await pytgcalls.leave_group_call(m.chat.id)
    await m.reply("⏹ Music stopped")

@app.on_message(filters.command("ping"))
async def ping(_, m):
    await m.reply("🏓 Pong!")

# ---------- RUN ----------
async def main():
    await app.start()
    await pytgcalls.start()
    print("✅ MUSIC BOT RUNNING")
    await asyncio.Event().wait()

asyncio.run(main())