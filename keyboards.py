from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Anime qo'shish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="➕ Admin qo'shish"), KeyboardButton(text="➖ Admin o'chirish")],
            [KeyboardButton(text="📢 Broadcast (Xabar yuborish)")]
        ],
        resize_keyboard=True
    )
