from loader import dp
from typing import Any
from aiogram import types
import operator
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram_dialog import StartMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel, Back, Url, Next, Back, Start, Group, Select
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from models.main_db import User
from models.drink_db import Drink
from aiogram_dialog.exceptions import UnknownIntent
from utils.functions import checkBalance, get_wallet_data

from loguru import logger
from icecream import ic

from modules.wallet.main import WalletSG
from modules.drinks.list import DrinksSG



#### start dialog

@dp.message_handler(Command(commands=['start']))
async def start(m: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(MixerSG.main, mode=StartMode.RESET_STACK)

#### start dialog


@dp.errors_handler()
async def some_error(msg, error, dialog_manager: DialogManager):
    logger.error("ERROR {} {}".format(error, msg))
    if isinstance(error, UnknownIntent):
        try:
            await dialog_manager.event.bot.delete_message(chat_id = dialog_manager.event.message.chat.id, message_id = dialog_manager.event.message.message_id)
        except:
            pass
        await dialog_manager.start(MixerSG.main, mode=StartMode.RESET_STACK)



#### states
class MixerSG(StatesGroup):
    main = State()
    buy = State()


#### dialogs
mixer_dialog = Dialog(
    Window(
        Format("Текущий баланс: <b>{balance}₽</b>"),
        Start(Const("Пополнить через TON💎"), id="wallet", state=WalletSG.receive),
        Start(Const("Напитки"), id="drinklist", state=DrinksSG.main),
        state=MixerSG.main,
    ),
    getter=get_wallet_data,
)
