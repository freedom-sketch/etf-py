from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from telegram_bot.filters import IsAdminFilter
from telegram_bot.inline_keyboards.admin_panel import admin_panel_inline_keyboard
from telegram_bot.FSM.admin_fsm import AddUserForm
from telegram_bot.common_keyboard import yn_panel, cancel_button
from dao.add_methods_dao import add_user, add_subscription
from dao.select_methods_dao import all_servers
from xui.methods import XuiAPI
from LoggerFactory import logger_factory
from config import SubscriptionApiData


logger = logger_factory.create_logger(name='tg.AdminHandler')
admin_router = Router()

@admin_router.callback_query(F.data == 'admin_panel', IsAdminFilter())
async def main_panel(callback: types.CallbackQuery):
    keyboard = await admin_panel_inline_keyboard() #type: ignore
    await callback.message.edit_text("Панель администратора", reply_markup=keyboard.as_markup())
    await callback.answer()


@admin_router.callback_query(F.data == 'add_user', StateFilter(None), IsAdminFilter())
async def set_name(callback: types.CallbackQuery, state: FSMContext):
    keyboard = await cancel_button()
    await callback.message.answer("Как зовут нового пользователя?", reply_markup=keyboard.as_markup())
    await callback.answer()
    await state.set_state(AddUserForm.user_name)


@admin_router.message(AddUserForm.user_name)
async def set_id(message: types.Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    keyboard = await cancel_button()
    await message.answer("Какой у пользователя id в телеграме?", reply_markup=keyboard.as_markup())
    await state.set_state(AddUserForm.user_id)


@admin_router.callback_query(AddUserForm.need_subscription, F.data == 'yes')
async def need_subscription_y(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(need_subscription='True')
    await callback.message.answer("На какой период подписка? (0 - бессрочно)")
    await callback.answer()
    await state.set_state(AddUserForm.subscription_duration)


@admin_router.callback_query(AddUserForm.need_subscription, F.data == 'no')
async def need_subscription_y(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(need_subscription='False')
    await callback.message.delete()
    await state.clear()


@admin_router.message(AddUserForm.subscription_duration)
async def need_subscription_y(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    user_add_id = state_data['user_id']
    user_add_name = state_data['user_name']
    subscription_duration = int(message.text)

    servers = await all_servers()
    for server in servers:
        await XuiAPI.add_new_client(email=user_add_name,
                                    user_id=str(user_add_id),
                                    panel_url=str(server.panel_url),
                                    login=str(server.login),
                                    password=str(server.password),
                                    subscription_duration=subscription_duration,
                                    inbound_id=int(server.inbound_id))
    duration = 10000 if subscription_duration == 0 else subscription_duration
    await add_subscription(telegram_id=int(user_add_id), duration_days=duration)

    await message.answer("Подписка добавлена")
    domain = SubscriptionApiData.DOMAIN
    url = SubscriptionApiData.WEB_PATH
    await message.answer(f"<code>https://{domain}{url}{user_add_id}</code>", parse_mode='html')
    await state.clear()


@admin_router.message(AddUserForm.user_id)
async def try_add_user(message: types.Message, state: FSMContext):
    try:
        await state.update_data(user_id=message.text)
        state_data = await state.get_data()
        user_add_id = state_data['user_id']

        await add_user(telegram_id=int(user_add_id))
        await message.answer('Пользователь добавлен')

        keyboard = await yn_panel()
        await message.answer("Добавить подписку этому пользователю?", reply_markup=keyboard.as_markup())
        await state.set_state(AddUserForm.need_subscription)
    except Exception as e:
        await message.answer(f'Не удалось добавить пользователя:\n<code>{e}</code>', parse_mode='html')


@admin_router.callback_query(F.data == 'cancel_fsm')
async def cancel_add_user(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer('Действие отменено')