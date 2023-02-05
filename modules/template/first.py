from loader import dp
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram_dialog import StartMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from loguru import logger

#### message command

@dp.message_handler(Command(commands=['back']))
async def name_start(m: types.Message):
    logger.info('back command!')
    await m.reply('Вспоминаем хорошо!')

#### message command









#### start dialog

@dp.message_handler(Command(commands=['start']))
async def start(m: types.Message, dialog_manager: DialogManager):
    logger.info('start command!')
    await dialog_manager.start(TemplSG.input, mode=StartMode.RESET_STACK)

#### start dialog









#### getter

async def get_name_data(dialog_manager: DialogManager, **kwargs):
    return {
        "name": dialog_manager.current_context().dialog_data.get("name")
    }

#### getter









#### dialog actions

#### message input
async def inp_handler(m: types.Message, dialog: Dialog, dialog_manager: DialogManager):
    dialog_manager.current_context().dialog_data["name"] = m.text
    await dialog.next(dialog_manager)

#### button click action
async def on_finish(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    name = dialog_manager.current_context().dialog_data["name"]
    await c.answer(f'hahaha, {name}')
    await dialog_manager.done({"name": name})

#### dialog actions









#### Windows

#### states
class TemplSG(StatesGroup):
    input = State()
    confirm = State()

#### dialogs
template_dialog = Dialog(
    Window(
        Const("Wat?"),
        Cancel(),
        MessageInput(inp_handler),
        state=TemplSG.input,
    ),
    Window(
        Format("Your name is `{name}`, it is korrect?"),
        Row(Back(Const("No")), Button(Const("Yes"), id="yes", on_click=on_finish)),
        state=TemplSG.confirm,
        getter=get_name_data,
    )
)

#### Windows
