from loader import dp
from typing import Any
from aiogram import types
import operator
from magic_filter import F
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram_dialog import StartMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel, Back, Url, Next, Back, Start, ScrollingGroup, Group, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from models.main_db import User
from models.drink_db import Drink

from utils.functions import checkBalance, get_wallet_data, list_admins

from loguru import logger
from icecream import ic

from models.drink_db import Drink



class DrinksSG(StatesGroup):
    main = State()
    drink_edit = State()
    drink_pour = State()
    confirm = State()
    confirm_delete = State()


async def edit_drinks(c: types.CallbackQuery, widget: Any, dialog_manager: DialogManager, item_id: str):
    data = dialog_manager.current_context().dialog_data or {}
    data.update(dialog_manager.current_context().start_data or {})
    
    drink = Drink.get(id = item_id)
    dialog_manager.current_context().dialog_data["drink_id"] = drink.id
    dialog_manager.current_context().dialog_data["drink_name"] = drink.name
    
    if c.from_user.id in list_admins():
        await dialog_manager.switch_to(DrinksSG.drink_edit)
    else:
        await dialog_manager.switch_to(DrinksSG.drink_pour)


async def get_drinks_data(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.current_context().dialog_data or {}
    data.update(dialog_manager.current_context().start_data or {})
    
    drinks = [('%s / %s₽' % (_.name, _.cost), _.id) for _ in Drink]
    drinks.sort()
    
    drink = None
    if data.get('drink_id'):
        try:
            drink = Drink.get(id = data.get('drink_id'))
        except:
            pass
    longlist = len(drinks) > 10
    is_admin = dialog_manager.event.from_user.id in list_admins()
        
    return {"drink": drink, "drinks_list": drinks, "drink_name": data.get("drink_name"), "longlist": longlist, "is_admin": is_admin}


#### Клавиатура - список напитков
drinks_list_kbd = Group(
        Select(
            Format("{item[0]}"),
            id = "s_drinks",
            item_id_getter = operator.itemgetter(1),
            items = "drinks_list",
            on_click=edit_drinks,
        ),
        id = 'scrolldrinks', width = 1, when=F["longlist"].is_not(True))
        
drinks_list_kbd_group = ScrollingGroup(
        Select(
            Format("{item[0]}"),
            id = "s_drinks",
            item_id_getter = operator.itemgetter(1),
            items = "drinks_list",
            on_click=edit_drinks,
        ),
        id = 'scrolldrinkslong', width = 2, height = 5, when=F["longlist"])


async def edit_drink(m: types.Message, dialog: Dialog, dialog_manager: DialogManager):
    if m.text and m.from_user.id in list_admins():
        data = dialog_manager.current_context().dialog_data or {}
        data.update(dialog_manager.current_context().start_data or {})
        drink = Drink.get(id = data.get("drink_id"))
        try:
            cost = int(m.text)
            drink.cost = cost
            drink.save()
        except:
            drink.name = m.text
            drink.save()


async def add_drink_name(m: types.Message, dialog: Dialog, dialog_manager: DialogManager):
    if m.from_user.id in list_admins():
        dialog_manager.current_context().dialog_data["drink_name"] = m.text
        await dialog.next(dialog_manager)

async def add_drink_name_confirm(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    if c.from_user.id in list_admins():
        drink_name = dialog_manager.current_context().dialog_data["drink_name"]
        p = Drink.create(name = drink_name)
        dialog_manager.current_context().dialog_data["drink_id"] = p.id
        await c.answer(f"✅ Создан напиток: {p.name}")
        await dialog_manager.dialog().switch_to(DrinksSG.drink_edit)


async def on_finish(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.done()

async def pour_drink(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.current_context().dialog_data or {}
    data.update(dialog_manager.current_context().start_data or {})
    drink = Drink.get(id = data.get("drink_id"))
    print('Наливаю', drink.name)
    from_user = c.from_user
    user, created = User.get_or_create(user_id = from_user.id)
    if user.balance < drink.cost:
        need = round(drink.cost - user.balance, 2)
        await c.answer(f"Не хватает {need} рублей!", show_alert = True)
    else:
        user.balance -= drink.cost
        user.save()
        await c.answer(f"Наливаю {drink.name}, за {drink.cost} рублей!")
        

async def del_drink_confirm(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    data = dialog_manager.current_context().dialog_data or {}
    data.update(dialog_manager.current_context().start_data or {})
    drink_id = data.get("drink_id")
    drink = Drink.get(id = drink_id)
    drink.delete_instance()
    await c.answer(f"Удалил: {drink.name}")
    await dialog_manager.dialog().switch_to(DrinksSG.main)




drinks_menu = Dialog(
    Window(
        Format("Список напитков:"),
        Format("Ваш баланс: <b>{balance}₽</b>"),
        drinks_list_kbd,
        drinks_list_kbd_group,
        Button(Const("↩️ Назад"), id="finish", on_click=on_finish),
        MessageInput(add_drink_name),
        state=DrinksSG.main,
        getter=get_wallet_data,
    ),
        Window(
            Format('Создаю напиток <b>"{drink_name}"</b>'),
            Row(Back(Const("↩️ Отмена")), Button(Const("✅ Создать"), id="yes", on_click=add_drink_name_confirm)),
            state=DrinksSG.confirm,
            getter=get_drinks_data,
        ),
    Window(
        Format("Редактируем {drink.name}", when = "drink"),
        Format("Цена {drink.cost}", when = "drink"),
        Format("\n\n<i>Введите название, или цену</i>", when = "drink"),
        SwitchTo(Const("Налить 🥤"), id="to_pour", state = DrinksSG.drink_pour, when = "is_admin"),
        Row(SwitchTo(Const("↩️ Назад"), id="to_list", state = DrinksSG.main), Next(Const("❌ Удалить"))),
        MessageInput(edit_drink),
        state=DrinksSG.drink_edit,
    ),
        Window(
            Format('Удалить напиток <b>"{drink_name}"</b>?'),
            Row(Button(Const("❌ Удалить"), id="del", on_click=del_drink_confirm), Back(Const("↩️ Отмена"))),
            state=DrinksSG.confirm_delete,
            getter=get_drinks_data,
        ),
    Window(
        Format("Налить <b>{drink.name}</b>? 🥤", when = "drink"),
        Format("Цена {drink.cost}", when = "drink"),
        Format("Ваш баланс: <b>{balance}₽</b>"),
        Row(SwitchTo(Const("↩️ Назад"), id="to_list", state = DrinksSG.main), Button(Const("Налить! 🥤"), id="pour", on_click=pour_drink)),
        state=DrinksSG.drink_pour,
        getter=get_wallet_data,
    ),
    getter = get_drinks_data,
)
