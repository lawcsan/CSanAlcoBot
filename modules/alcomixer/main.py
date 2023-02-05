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




#### getter

async def get_drinks_data(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.current_context().dialog_data or {}
    data.update(dialog_manager.current_context().start_data or {})
    
    drinks = [(_.name, _.id) for _ in Drink]
    drinks.sort()
    return {"drinks_list": drinks, "drink_name": data.get("drink_name")}

#### getter



#### Windows

#### states
class MixerSG(StatesGroup):
    main = State()
    buy = State()

class DrinkSG(StatesGroup):
    drink_list = State()
    drink_edit = State()
    confirm = State()
#### states

#### dialogs
mixer_dialog = Dialog(
    Window(
        #Format("Ваш текущий баланс: <b>{balance} TON💎</b>"),
        Format("Текущий баланс: <b>{balance}₽</b>"),
        Start(Const("Пополнить через TON💎"), id="wallet", state=WalletSG.receive),
        #Start(Const("Напитки"), id="drinklist", state=DrinkSG.drink_list),
        Start(Const("Напитки"), id="drinklist", state=DrinksSG.main),
        state=MixerSG.main,
    ),
    getter=get_wallet_data,
)

#### Windows





async def edit_drinks(c: types.CallbackQuery, widget: Any, dialog_manager: DialogManager, item_id: str):
    drink = Drink.get(id = item_id)
    print('edit', item_id, drink)
    data_for_copy = {"drink_id": item_id, "drink_name": drink.name}
    await dialog_manager.start(DrinkSG.drink_edit, data = data_for_copy)


#### Клавиатура - список напитков
drinks_list_kbd = Group(
        Select(
            Format("{item[0]}"),
            id = "s_drinks",
            item_id_getter = operator.itemgetter(1),
            items = "drinks_list",
            on_click=edit_drinks,
        ),
        id = 'scrolldrinks', width = 2)



async def add_drink_name(m: types.Message, dialog: Dialog, dialog_manager: DialogManager):
    dialog_manager.current_context().dialog_data["drink_name"] = m.text
    await dialog.next(dialog_manager)


async def on_finish(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    drink_name = dialog_manager.current_context().dialog_data["drink_name"]
    p = Drink.create(name = drink_name)
    await c.answer(f"✅ Создан напиток: {p.name}")
    await dialog_manager.dialog().back()



async def upd_drink(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.current_context().dialog_data or {}
    data.update(dialog_manager.current_context().start_data or {})
    drink_id = data.get("drink_id")
    drink = Drink.get(id = drink_id)
    await c.answer(f"✅ Обновил напиток: {drink.name}")





alco_editor_dialog = Dialog(
    Window(
        Format("Список напитков:"),
        Format("Чтобы добавить новый - отправьте в сообщении название"),
        drinks_list_kbd,
        Cancel(Const("↩️ Назад")),
        MessageInput(add_drink_name),
        state=DrinkSG.drink_list,
        getter = get_drinks_data,
    ),
        Window(
            Format('Создаю напиток <b>"{drink_name}"</b>'),
            Row(Back(Const("↩️ Отмена")), Button(Const("✅ Создать"), id="yes", on_click=on_finish)),
            state=DrinkSG.confirm,
            getter=get_drinks_data,
        ),
    Window(
        Format('Редактировать <b>"{drink_name}"</b>'),
        Row(Cancel(Const("↩️ Отмена")), Button(Const("✅ Обновить"), id="update", on_click=upd_drink)),
        state=DrinkSG.drink_edit,
        getter=get_drinks_data,
    ),
    #Window(
        #Format("Купить TON💎 можно прямо в Telegram, например через через этих ботов:"),
        #Row(
            #Url(Const("@CryptoBot"),Const('http://t.me/CryptoBot?start=r-304645')),
            #Url(Const("@Wallet"),Const('http://t.me/Wallet'))
        #),
        #Back(Const("Назад")),
        #state=MixerSG.buy,
    #),
    #getter=get_wallet_data,
)

#### Windows
