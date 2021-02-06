import time

from aiogram import types

from data import config
from loader import dp, bot
from utils.db_api.models import paymentModel, orderModel
from utils.notify_admins import notify_admins_message


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    payment = paymentModel.get_payment(pre_checkout_query.from_user.id)
    await bot.answer_pre_checkout_query(pre_checkout_query.id,
                                        ok=payment["success"] and payment["date"] + 60 * 60 * 24 * 7 > time.time() and
                                           pre_checkout_query.invoice_payload == payment["secret_key"],
                                        error_message=config.errorMessage["exceeded_time_pay"])


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    paymentModel.add_payment_history(message.from_user.id, message.successful_payment.total_amount // 100)
    mes = config.errorMessage["payment_missing"]
    payment = paymentModel.get_payment(message.from_user.id)
    if payment["success"]:
        orderModel.create_order(message.from_user.id, payment["description"], payment["nameProduct"],
                                message.successful_payment.total_amount // 100)
        await notify_admins_message(config.adminMessage["admin_mes_order_paid"])
        mes = config.message["comment_confirmation_yes"]
    paymentModel.del_payment(message.from_user.id)
    await message.answer(mes)