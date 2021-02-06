from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Text

from data import config
from keyboards.inline import buttons
from keyboards.inline.callback_datas import confirmation_callback
from loader import dp
from states.user_mes import UserMes
from utils.db_api.models import orderModel, messagesModel
from utils.notify_admins import notify_admins_message


@dp.message_handler(Text(equals=["Написать администрации"]))
async def start_write_administration(message: types.Message):
    await UserMes.message.set()
    await message.answer("Напишите свое сообщение:")


@dp.message_handler(commands=["mesa", "ames", "Ames", "mesA"])
async def start_write_administration(message: types.Message):
    await UserMes.message.set()
    await message.answer("Напишите свое сообщение:")


@dp.message_handler(state=UserMes.message)
async def adding_comment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["message"] = message.text
    await message.answer(config.message["comment_confirmation"].format(text=message.text),
                         reply_markup=buttons.getConfirmationKeyboard(cancel="Отменить"))
    await UserMes.wait.set()


@dp.message_handler(state=UserMes.wait)
async def waiting(message: types.Message):
    pass


@dp.callback_query_handler(confirmation_callback.filter(bool="Yes"), state=UserMes.wait)
async def adding_comment_yes(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=2)
    data = await state.get_data()
    orders = orderModel.get_ALLOrders()
    isOrder = orders["success"] and call.from_user.id in [order["userID"] for order in orders["data"]]
    messagesModel.create_messages(call.from_user.id,
                                  data.get("message") if "message" in data.keys() else "", isOrder)
    await notify_admins_message("Новое сообщение от " + (
            "<b>пользователя с заказом</b>" if isOrder else "<b>обычного пользователя</b>"))
    await call.message.edit_text(config.message["message_sent"])
    await state.finish()


@dp.callback_query_handler(confirmation_callback.filter(bool="No"), state=UserMes.wait)
async def adding_comment_no(call: types.CallbackQuery):
    await call.message.edit_text(config.message["message_no"])
    await UserMes.message.set()


@dp.callback_query_handler(confirmation_callback.filter(bool="cancel"), state=UserMes.wait)
async def adding_comment_cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(config.message["message_cancel"])
    await state.finish()
