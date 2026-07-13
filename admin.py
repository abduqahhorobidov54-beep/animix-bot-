from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import read_data, write_data
from config import SUPER_ADMIN

router = Router()

class AdminState(StatesGroup):
    waiting_for_admin_id = State()
    waiting_for_remove_id = State()
    waiting_for_broadcast = State()

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    admins = await read_data("admins")
    if message.from_user.id != SUPER_ADMIN and message.from_user.id not in admins: return
    users = await read_data("users")
    animes = await read_data("anime")
    await message.answer(f"📊 **Bot statistikasi:**\n\n👥 Foydalanuvchilar: {len(users)}\n🎬 Jami Animelar: {len(animes)}")

@router.message(F.text == "➕ Admin qo'shish")
async def add_admin_start(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN: return
    await message.answer("Yangi adminning Telegram ID raqamini yozing:")
    await state.set_state(AdminState.waiting_for_admin_id)

@router.message(AdminState.waiting_for_admin_id)
async def add_admin_finish(message: Message, state: FSMContext):
    try:
        new_admin = int(message.text)
        admins = await read_data("admins")
        if new_admin not in admins:
            admins.append(new_admin)
            await write_data("admins", admins)
            await message.answer("✅ Yangi admin qo'shildi!")
        else:
            await message.answer("Bu foydalanuvchi allaqachon admin!")
    except ValueError:
        await message.answer("Xato! Faqat raqamlardan iborat ID kiriting.")
    await state.clear()

@router.message(F.text == "➖ Admin o'chirish")
async def remove_admin_start(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN: return
    await message.answer("O'chiriladigan adminning Telegram ID raqamini kiriting:")
    await state.set_state(AdminState.waiting_for_remove_id)

@router.message(AdminState.waiting_for_remove_id)
async def remove_admin_finish(message: Message, state: FSMContext):
    try:
        admin_id = int(message.text)
        admins = await read_data("admins")
        if admin_id in admins:
            admins.remove(admin_id)
            await write_data("admins", admins)
            await message.answer("✅ Admin muvaffaqiyatli o'chirildi!")
        else:
            await message.answer("Bu ID adminlar ro'yxatida topilmadi.")
    except ValueError:
        await message.answer("Xato! ID raqam bo'lishi kerak.")
    await state.clear()

@router.message(F.text == "📢 Broadcast (Xabar yuborish)")
async def broadcast_start(message: Message, state: FSMContext):
    admins = await read_data("admins")
    if message.from_user.id != SUPER_ADMIN and message.from_user.id not in admins: return
    await message.answer("Foydalanuvchilarga yuboriladigan xabarni (matn, rasm, video) yuboring:")
    await state.set_state(AdminState.waiting_for_broadcast)

@router.message(AdminState.waiting_for_broadcast)
async def broadcast_finish(message: Message, state: FSMContext):
    users = await read_data("users")
    count = 0
    await message.answer("🚀 Reklama yuborish boshlandi...")
    for user_id in users:
        try:
            await message.copy_to(chat_id=user_id)
            count += 1
        except:
            continue
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yetkazildi.")
    await state.clear()
