
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1

API_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "songs.json"
OWNER_ID = 1918624551  # Main user ID allowed to setup

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        "👋 Welcome to Squonk Radio V0.4.4!
Use /setup to link your group."
    )

@dp.message_handler(commands=['setup'])
async def cmd_setup(message: types.Message):
    if message.chat.type != "private":
        return
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ Only the bot owner can run setup.")
        return
    await message.reply("📩 Send me `GroupID: <your_group_id>` to register a group.")

@dp.message_handler(lambda message: message.text and message.text.startswith("GroupID:"))
async def set_group_id(message: types.Message):
    if message.chat.type != "private":
        return
    if message.from_user.id != OWNER_ID:
        await message.reply("⛔ You are not allowed to set GroupID.")
        return
    group_id = message.text.replace("GroupID:", "").strip()
    data = load_data()
    data["group_id"] = group_id
    data["songs"] = []
    save_data(data)
    await message.reply(f"✅ Group ID `{group_id}` saved. Now send me .mp3 files!")

@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_audio(message: types.Message):
    if message.chat.type != "private":
        return
    data = load_data()
    group_id = data.get("group_id")
    if not group_id:
        await message.reply("❗ Please first send `GroupID: <your_group_id>`")
        return

    file_info = await bot.get_file(message.audio.file_id)
    file = await bot.download_file(file_info.file_path)
    filename = message.audio.file_name or f"{message.audio.file_id}.mp3"
    with open(filename, "wb") as f:
        f.write(file.read())

    audio = MP3(filename, ID3=ID3)
    title = audio.get("TIT2", TIT2(encoding=3, text=filename)).text[0]
    artist = audio.get("TPE1", TPE1(encoding=3, text="Unknown")).text[0]

    data["songs"].append({
        "file_id": message.audio.file_id,
        "title": title,
        "artist": artist
    })
    save_data(data)
    await message.reply(f"✅ Saved `{title}` by `{artist}`.")

@dp.message_handler(commands=['play'])
async def cmd_play(message: types.Message):
    data = load_data()
    group_id = str(message.chat.id)
    if str(data.get("group_id")) != group_id:
        return
    if not data.get("songs"):
        await message.reply("❌ No songs found for this group.")
        return

    song = data["songs"][0]
    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("▶️ Next", callback_data="next"),
        InlineKeyboardButton("📜 Playlist", callback_data="playlist")
    )
    await bot.send_audio(
        chat_id=message.chat.id,
        audio=song["file_id"],
        caption="🎵 Squonking time!",
        reply_markup=buttons
    )

@dp.callback_query_handler(lambda c: c.data == "playlist")
async def playlist_callback(callback_query: types.CallbackQuery):
    data = load_data()
    group_id = str(callback_query.message.chat.id)
    if str(data.get("group_id")) != group_id:
        return
    if not data.get("songs"):
        await callback_query.message.reply("❌ No songs available.")
        return
    text = "🎵 Playlist:

"
    for i, song in enumerate(data["songs"], 1):
        text += f"{i}. {song['title']} – {song['artist']}
"
    await callback_query.message.reply(text)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
