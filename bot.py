import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import BOT_TOKEN, SUPER_ADMIN
from database import init_db, read_data, write_data
from keyboards import get_admin_menu
import admin, anime

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(admin.router)
dp.include_router(anime.router)

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await init_db()
    users = await read_data("users")
    if message.from_user.id not in users:
        users.append(message.from_user.id)
        await write_data("users", users)
        
    args = message.text.split()
    if len(args) > 1:
        anime_id = args[1]
        animes = await read_data("anime")
        if anime_id in animes:
            ani = animes[anime_id]
            caption = f"🎬 **{ani['name']}**\n\n🎭 Janr: {ani['genre']}\n📝 Tavsif: {ani['desc']}"
            
            buttons = []
            for season in ani["seasons"].keys():
                buttons.append([InlineKeyboardButton(text=f"{season}-Fasl", callback_data=f"show_episodes_{anime_id}_{season}")])
            
            admins = await read_data("admins")
            if message.from_user.id == SUPER_ADMIN or message.from_user.id in admins:
                buttons.append([InlineKeyboardButton(text="➕ Fasl qo'shish", callback_data=f"add_season_{anime_id}")])
                
            kb = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer_photo(photo=ani['poster'], caption=caption, reply_markup=kb)
            return

    admins = await read_data("admins")
    if message.from_user.id == SUPER_ADMIN or message.from_user.id in admins:
        await message.answer("Xush kelibsiz, Admin! Quyidagi menyudan foydalaning:", reply_markup=get_admin_menu())
    else:
        await message.answer("Salom! Kinolar kanaldagi 'Tomosha qilish' tugmasi orqali ko'rsatiladi.")

@dp.message(Command("panel"))
async def open_panel(message: Message):
    admins = await read_data("admins")
    if message.from_user.id == SUPER_ADMIN or message.from_user.id in admins:
        await message.answer("Admin panel ochildi:", reply_markup=get_admin_menu())

@dp.callback_query(F.data.startswith("show_episodes_"))
async def show_episodes(call: CallbackQuery):
    _, _, anime_id, season = call.data.split("_")
    animes = await read_data("anime")
    ani = animes[anime_id]
    
    buttons = []
    episodes = ani["seasons"][season]
    
    for ep in episodes.keys():
        buttons.append([InlineKeyboardButton(text=f"{ep}-qism", callback_data=f"play_{anime_id}_{season}_{ep}")])
        
    admins = await read_data("admins")
    if call.from_user.id == SUPER_ADMIN or call.from_user.id in admins:
        buttons.append([InlineKeyboardButton(text="➕ Qism qo'shish", callback_data=f"add_ep_{anime_id}_{season}")])
        
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.answer(f"🎬 {ani['name']} — {season}-fasl qismlari:", reply_markup=kb)

@dp.callback_query(F.data.startswith("play_"))
async def play_episode(call: CallbackQuery):
    _, anime_id, season, ep = call.data.split("_")
    animes = await read_data("anime")
    video_id = animes[anime_id]["seasons"][season][ep]
    
    await call.message.answer_video(video=video_id, caption=f"🎬 {animes[anime_id]['name']}\n🗓 {season}-fasl, {ep}-qism")

async def main():
    await init_db()
    print("🤖 Bot muvaffaqiyatli ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
