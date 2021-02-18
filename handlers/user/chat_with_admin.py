import time

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Text

from data import config
from keyboards.inline import buttons
from keyboards.inline.callback_datas import confirmation_callback
from loader import dp
from states.user_mes import UserMes
from utils.db_api.models import orderModel, messagesModel, banListModel
from utils.notify_admins import notify_admins_message
from utils import function


@dp.message_handler(Text(equals=["Написать администрации"]))
async def start_write_administration(message: types.Message, state: FSMContext):
    if banListModel.get_ban_user(message.from_user.id)["code"] == 200:
        await message.answer("Вы забанены")
        return

    lastMessage = messagesModel.get_last_message_day_user(message.from_user.id)
    if lastMessage["code"] == 200 and len(lastMessage["data"]) >= 20:
        mes = "Вы привысили количество обращений в день"
    elif lastMessage["code"] == 200 and lastMessage["data"][len(lastMessage["data"]) - 1]["date"] > time.time() - 60 * 30:
        mes = "Вы недавно отпраили сообщение.\nПовторное можно будет отправить через <b>{date}</b> минут".format(
            date=int((lastMessage["data"][len(lastMessage["data"]) - 1]["date"]-(time.time() - 60 * 30))/60))
    else:
        await UserMes.message.set()
        await function.set_state_active(state)
        mes = "Напишите свое сообщение:"
    await message.answer(mes)


@dp.message_handler(state=UserMes.message)
async def adding_comment(message: types.Message, state: FSMContext):
    message.text = function.string_handler(message.text)
    await state.update_data(message=message.text)
    await UserMes.wait.set()
    await message.answer(config.message["comment_confirmation"].format(text=message.text),
                         reply_markup=buttons.getConfirmationKeyboard(cancel="Отменить"))


@dp.message_handler(state=UserMes.wait)
async def waiting(message: types.Message):
    pass


@dp.message_handler(state=UserMes.document, content_types=types.ContentType.DOCUMENT)
async def message_add_doc(message: types.Message, state: FSMContext):
    await state.update_data(document=message.document)
    await UserMes.wait.set()
    await message.answer(config.message["document_confirmation"].format(
        text="{name} {size}кб\n".format(name=message.document.file_name, size=message.document.file_size)),
        reply_markup=buttons.getConfirmationKeyboard(cancel="Отменить"))


@dp.message_handler(state=UserMes.document, content_types=types.ContentType.PHOTO)
async def message_add_doc(message: types.Message):
    await message.answer(text=config.errorMessage["not_add_photo"])


@dp.callback_query_handler(confirmation_callback.filter(bool="noElement"), state=UserMes)
async def adding_promoCode_yes(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=2)
    data = await state.get_data()
    mes = ""
    state_active = data.get("state_active")
    keyboard = None
    if "UserMes:document" == state_active:
        await create_mes(call, state)
        return
    await call.message.edit_text(text=mes, reply_markup=keyboard)


@dp.callback_query_handler(confirmation_callback.filter(bool="Yes"), state=UserMes)
async def adding_comment_yes(call: types.CallbackQuery, state: FSMContext):
    await call.answer(cache_time=2)
    data = await state.get_data()
    state_active = data.get("state_active")
    mes = ""
    keyboard = None
    if "UserMes:document" == state_active:
        await create_mes(call, state)
        return
    elif "UserMes:documentCheck" == state_active:
        await UserMes.document.set()
        mes = config.message["comment_document"]
        keyboard = buttons.getCustomKeyboard(noElement="Нет файла")
    elif "UserMes:message" == state_active:
        await UserMes.documentCheck.set()
        mes = config.message["comment_documentCheck"]
        keyboard = buttons.getConfirmationKeyboard(cancel="Отменить")
    await function.set_state_active(state)
    await call.message.edit_text(text=mes, reply_markup=keyboard)


@dp.callback_query_handler(confirmation_callback.filter(bool="No"), state=UserMes)
async def adding_comment_no(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_active = data.get("state_active")
    if "UserMes:document" == state_active:
        await UserMes.document.set()
    elif "UserMes:documentCheck" == state_active:
        await create_mes(call, state)
        return
    elif "UserMes:message" == state_active:
        await UserMes.message.set()

    await call.message.edit_text(config.message["message_no"])


@dp.callback_query_handler(confirmation_callback.filter(bool="cancel"), state=UserMes)
async def adding_comment_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(config.message["message_cancel"])


async def create_mes(call, state):
    data = await state.get_data()
    orders = orderModel.get_ALLOrders()
    message = data.get("message") if "message" in data.keys() else ""
    document = [data.get("document").file_id] if "document" in data.keys() else []
    isOrder = orders["code"] == 200 and call.from_user.id in [order["userID"] for order in orders["data"]]
    messagesModel.create_messages(call.from_user.id, message, document, isOrder)
    await state.finish()
    await notify_admins_message("Новое сообщение от " + (
        "<b>пользователя с заказом</b>" if isOrder else "<b>обычного пользователя</b>"))
    await call.message.edit_text(config.message["message_sent"])
