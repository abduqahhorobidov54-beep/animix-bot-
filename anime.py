from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import read_data, write_data
from config import SUPER_ADMIN, KANAL_ID, BOT_USERNAME
import uuid

router = Router()

class AnimeState(StatesGroup):
    waiting_for_name = State()
    waiting_for_genre = State()
    waiting_for_desc = State()
    waiting_for_poster = State()
    
    waiting_for_season_num = State()
    waiting_for_episode_num = State()
    waiting_for_episode_video = State()

@router.message(F.text == "➕ Anime qo'shish")
async def start_add_anime(message: Message, state: FSMContext):
    admins = await read_data("admins")
    if message.from_user.id != SUPER_ADMIN and message.from_user.id not in admins: return
    await message.answer("Anime nomini kiriting:")
    await state.set_state(AnimeState.waiting_for_name)

@router.message(AnimeState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Janrini kiriting:")
    await state.set_state(AnimeState.waiting_for_genre)

@router.message(AnimeState.waiting_for_genre)
async def process_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await message.answer("Tavsif (opisaniya) kiriting:")
    await state.set_state(AnimeState.waiting_for_desc)

@router.message(AnimeState.waiting_for_desc)
async def process_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("Poster (Rasm) yuboring:")
    await state.set_state(AnimeState.waiting_for_poster)

@router.message(AnimeState.waiting_for_poster, F.photo)
async def process_poster(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    await state.clear()
    
    anime_id = str(uuid.uuid4())[:8]
    animes = await read_data("anime")
    
    animes[anime_id] = {
        "name": data["name"],
        "genre": data["genre"],
        "desc": data["desc"],
        "poster": photo_id,
        "seasons": {}
    }
    await write_data("anime", animes)
    
    caption = f"🎬 **{data['name']}**\n\n🎭 Janr: {data['genre']}\n📝 Tavsif: {data['desc']}"
    
    btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={anime_id}")]
    ])
    
    try:
        await message.bot.send_photo(chat_id=KANAL_ID, photo=photo_id, caption=caption, reply_markup=btn)
        await message.answer("✅ Anime muvaffaqiyatli saqlandi va kanalga 'Tomosha qilish' tugmasi bilan yuborildi!")
    except Exception as e:
        await message.answer(f"✅ Anime bazaga saqlandi, lekin kanalga yuborishda xatolik yuz berdi: {e}\n(Eslatma: Bot kanalda admin bo'lishi kerak!)")

@router.callback_query(F.data.startswith("add_season_"))
async def add_season_start(call: CallbackQuery, state: FSMContext):
    anime_id = call.data.split("_")[2]
    await state.update_data(anime_id=anime_id)
    await call.message.answer("Fasl raqamini kiriting (Masalan: 1):")
    await state.set_state(AnimeState.waiting_for_season_num)

@router.message(AnimeState.waiting_for_season_num)
async def add_season_finish(message: Message, state: FSMContext):
    season = message.text
    state_data = await state.get_data()
    anime_id = state_data["anime_id"]
    
    animes = await read_data("anime")
    if season not in animes[anime_id]["seasons"]:
        animes[anime_id]["seasons"][season] = {}
        await write_data("anime", animes)
        await message.answer(f"✅ {season}-fasl muvaffaqiyatli ochildi!")
    else:
        await message.answer("Bu fasl allaqachon mavjud.")
    await state.clear()

@router.callback_query(F.data.startswith("add_ep_"))
async def add_episode_start(call: CallbackQuery, state: FSMContext):
    _, _, anime_id, season = call.data.split("_")
    await state.update_data(anime_id=anime_id, season=season)
    await call.message.answer("Qism raqamini kiriting (Masalan: 1):")
    await state.set_state(AnimeState.waiting_for_episode_num)

@router.message(AnimeState.waiting_for_episode_num)
async def add_episode_num(message: Message, state: FSMContext):
    await state.update_data(ep_num=message.text)
    await message.answer("Endi ushbu qismning videosini (Telegram video faylini) yuboring:")
    await state.set_state(AnimeState.waiting_for_episode_video)

@router.message(AnimeState.waiting_for_episode_video, F.video)
async def add_episode_finish(message: Message, state: FSMContext):
    video_id = message.video.file_id
    state_data = await state.get_data()
    
    anime_id = state_data["anime_id"]
    season = state_data["season"]
    ep_num = state_data["ep_num"]
    
    animes = await read_data("anime")
    animes[anime_id]["seasons"][season][ep_num] = video_id
    await write_data("anime", animes)
    
    await message.answer(f"✅ {season}-fasl, {ep_num}-qism bazaga muvaffaqiyatli saqlandi!")
    await state.clear()
