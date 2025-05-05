
import logging
import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1

API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "songs.json"

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
    await message.reply("👋 Welcome to Squonk Radio V0.4.3!\nUse /setup to link your group.")

@dp.message_handler(commands=['setup'])
async def cmd_setup(message: types.Message):
    await message.reply("📩 Send me `GroupID: <your_group_id>` to register a group.", parse_mode="Markdown")

@dp.message_handler(lambda message: message.text and message.text.startswith("GroupID:"))
async def handle_group_id(message: types.Message):
    user_id = str(message.from_user.id)
    group_id = message.text.replace("GroupID:", "").strip()
    if not group_id.startswith("-"):
        await message.reply("❌ Invalid group ID format. It must start with `-`.", parse_mode="Markdown")
        return
    data = load_data()
    if group_id not in data:
        data[group_id] = []
        save_data(data)
    await message.reply(f"✅ Group ID `{group_id}` saved. Now send me .mp3 files!", parse_mode="Markdown")

@dp.message_handler(content_types=types.ContentType.AUDIO)
async def handle_audio(message: types.Message):
    user_id = str(message.from_user.id)
    data = load_data()
    # find group ID for user
    group_id = None
    for gid, songs in data.items():
        if songs and songs[-1].get("last_user") == user_id:
            group_id = gid
            break
    if not group_id:
        for gid in data:
            group_id = gid
            break
    if not group_id:
        await message.reply("❗ Please first send `GroupID: <your_group_id>` in this private chat.", parse_mode="Markdown")
        return

    file_info = await bot.get_file(message.audio.file_id)
    file_path = file_info.file_path
    destination = f"{message.audio.file_unique_id}.mp3"
    await bot.download_file(file_path, destination)

    try:
        audio = MP3(destination, ID3=ID3)
        title = audio.tags.get("TIT2", TIT2(encoding=3, text="Unknown")).text[0]
        artist = audio.tags.get("TPE1", TPE1(encoding=3, text="Unknown")).text[0]
    except:
        title = "Unknown"
        artist = "Unknown"

    data[group_id].append({
        "file_id": message.audio.file_id,
        "title": title,
        "artist": artist,
        "last_user": user_id
    })
    save_data(data)
    await message.reply(f"✅ Saved `{title}` by `{artist}`.", parse_mode="Markdown")

@dp.message_handler(commands=['play'])
async def cmd_play(message: types.Message):
    group_id = str(message.chat.id)
    data = load_data()
    songs = data.get(group_id)
    if not songs:
        await message.reply("❌ No songs found for this group.")
        return

    song = songs[-1]
    buttons = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("▶️ Next", callback_data="next"),
        InlineKeyboardButton("📃 Playlist", callback_data="playlist")
    )
    await bot.send_audio(chat_id=group_id, audio=song["file_id"], caption="🎶 Squonking time!", reply_markup=buttons)

@dp.callback_query_handler(lambda c: c.data == "playlist")
async def show_playlist(callback_query: types.CallbackQuery):
    group_id = str(callback_query.message.chat.id)
    data = load_data()
    songs = data.get(group_id, [])
    if not songs:
        await callback_query.answer("No songs found.")
        return
    text = "🎵 Playlist:"
    for i, s in enumerate(songs, 1):
        text += f"{i}. {s['title']} by {s['artist']}"
    await bot.send_message(chat_id=group_id, text=text)

@dp.message_handler(commands=["reset"])
async def reset_group(message: types.Message):
    group_id = str(message.chat.id)
    data = load_data()
    if group_id in data:
        del data[group_id]
        save_data(data)
        await message.reply("🧹 Group data reset.")
    else:
        await message.reply("No data to reset.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
