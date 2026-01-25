from utils.decorators.inline_keyboard_builder import inline_keyboard_builder
from telegram_bot.common_keyboard import back_button
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from LoggerFactory import logger_factory


logger = logger_factory.create_logger(name='tg.AdminPanelKeyboard')

@inline_keyboard_builder
async def admin_panel_inline_keyboard(builder: InlineKeyboardBuilder) -> InlineKeyboardBuilder:
    add_user_button = InlineKeyboardButton(text='✅ Добавить пользователя', callback_data="add_user")
    del_user_button = InlineKeyboardButton(text='❌ Удалить пользователя', callback_data="del_user")
    users_list_button = InlineKeyboardButton(text='📋 Список пользователей', callback_data="users_list")
    back_button_ = await back_button()

    builder.row(add_user_button, del_user_button)
    builder.row(users_list_button)
    builder.row(back_button_)

    return builder