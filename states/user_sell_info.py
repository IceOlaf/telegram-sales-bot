from aiogram.dispatcher.filters.state import StatesGroup, State


class SellInfo(StatesGroup):
    description = State()
    documentCheck = State()
    document = State()
    promoCodeCheck = State()
    promoCode = State()
    wait = State()