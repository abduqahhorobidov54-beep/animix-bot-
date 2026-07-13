import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, get_all_anime, save_anime_db, get_next_anime_id, add_user_to_stats, get_total_users

TOKEN = "8980539059:AAE4UdU4bXjv3Cp00a-WrhitnUKMwgbFwp4" 
ADMIN_ID = 6052679916  # Bu yerga o'zingizning haqiqiy ID raqamingizni yozing

bot = Bot(token=TOKEN)
dp = Dispatcher()

admin_states = {}

@dp.message(Command("start"))
async def start_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        await add_user_to_stats()
    
    await message.answer(
        "👋 Assalomu alaykum! Animix botga xush kelibsiz.\n"
        "Bu yerda siz o'zingizga yoqqan animelarni tomosha qilishingiz mumkin."
    )

@dp.message(Command("panel"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz bot admini emassiz!")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Anime qo'shish", callback_data="add_anime")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")]
    ])
    await message.answer("🛠 Admin panelga xush kelibsiz:", reply_markup=kb)

@dp.callback_query(F.data == "stats")
async def show_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    users = await get_total_users()
    await call.message.answer(f"📊 Botdagi jami foydalanuvchilar: {users} ta")
    await call.answer()

@dp.callback_query(F.data == "add_anime")
async def add_anime_start(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_states[call.from_user.id] = {"step": "title"}
    await call.message.answer("📝 Anime nomini kiriting:")
    await call.answer()

@dp.message()
async def handle_inputs(message: Message):
    # Agar xabar yozgan odam admin bo'lsa va anime qo'shish jarayonida bo'lsa
    if message.from_user.id == ADMIN_ID and message.from_user.id in admin_states:
        state = admin_states[message.from_user.id]
        step = state["step"]

        if step == "title":
            state["title"] = message.text
            state["step"] = "genres"
            await message.answer("🎭 Janrlarini kiriting:")
            
        elif step == "genres":
            state["genres"] = message.text
            state["step"] = "description"
            await message.answer("📝 Anime haqida qisqacha tavsif kiriting:")
            
        elif step == "description":
            state["description"] = message.text
            state["step"] = "photo"
            await message.answer("🖼 Anime uchun rasm (poster) yuboring:")
            
        elif step == "photo":
            if not message.photo:
                await message.answer("❌ Iltimos, rasm yuboring!")
                return
            state["photo_id"] = message.photo[-1].file_id
            
            next_id = await get_next_anime_id()
            anime_data = {
                "title": state["title"],
                "genres": state["genres"],
                "description": state["description"],
                "photo_id": state["photo_id"],
                "seasons": []
            }
            await save_anime_db(next_id, anime_data)
            del admin_states[message.from_user.id]
            await message.answer(f"✅ Anime muvaffaqiyatli qo'shildi!\n🆔 Anime ID: `{next_id}`", parse_mode="Markdown")
        return

    # Foydalanuvchilar uchun qidiruv (Anime ID yozilganda)
    if message.text and message.text.isdigit():
        animes = await get_all_anime()
        anime_id = message.text
        if anime_id in animes:
            anime = animes[anime_id]
            text = f"🎬 *{anime['title']}*\n\n🎭 Janrlar: {anime['genres']}\n📝 {anime['description']}"
            
            kb_list = []
            for idx, season in enumerate(anime.get('seasons', [])):
                kb_list.append([InlineKeyboardButton(text=f"{idx+1}-fasl", callback_data=f"season_{anime_id}_{idx}")])
            
            kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
            if anime['photo_id']:
                await message.answer_photo(photo=anime['photo_id'], caption=text, parse_mode="Markdown", reply_markup=kb)
            else:
                await message.answer(text, parse_mode="Markdown", reply_markup=kb)
        else:
            await message.answer("❌ Bunday ID dagi anime topilmadi.")

@dp.callback_query(F.data.startswith("season_"))
async def show_season_episodes(call: CallbackQuery):
    parts = call.data.split("_")
    anime_id = parts[1]
    season_idx = int(parts[2])
    
    animes = await get_all_anime()
    if anime_id in animes:
        anime = animes[anime_id]
        season = anime['seasons'][season_idx]
        
        kb_list = []
        row = []
        for ep_idx in range(len(season)):
            row.append(InlineKeyboardButton(text=f"{ep_idx+1}-qism", callback_data=f"play_{anime_id}_{season_idx}_{ep_idx}"))
            if len(row) == 3:
                kb_list.append(row)
                row = []
        if row:
            kb_list.append(row)
            
        kb_list.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_anime")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_list)
        await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("play_"))
async def play_episode(call: CallbackQuery):
    parts = call.data.split("_")
    anime_id = parts[1]
    season_idx = int(parts[2])
    ep_idx = int(parts[3])
    
    animes = await get_all_anime()
    if anime_id in animes:
        anime = animes[anime_id]
        video_id = anime['seasons'][season_idx][ep_idx]
        await call.message.answer_video(video=video_id, caption=f"🎬 {anime['title']}\n🍿 {season_idx+1}-fasl, {ep_idx+1}-qism")
    await call.answer()

async def main():
    await init_db()
    print("🤖 Bot muvaffaqiyatli ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
