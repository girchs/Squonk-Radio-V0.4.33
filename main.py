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
    await message.reply(
        "👋 Welcome to Squonk Radio V0.4.3!
Use /setup to link your group."
    )

@dp.message_handler(commands=['setup'])
async def cmd_setup(message: types.Message):
    await message.reply("📫 Send me `GroupID: <your_group_id>` to register a group.")

@dp.message_handler(commands=['play'])
async def cmd_play(message: types.Message):
    await message.reply("❌ No songs found for this group.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
