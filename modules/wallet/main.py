from loader import dp
from aiogram import types
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram_dialog import StartMode
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Row, Cancel, Back, Url, Next, Back
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput
from models.main_db import User

from loguru import logger

from utils.functions import checkBalance, get_wallet_data


#### start dialog

@dp.message_handler(Command(commands=['wallet']))
async def start(m: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(WalletSG.receive, mode=StartMode.RESET_STACK)

#### button check_balance
async def check_balance(c: types.CallbackQuery, button: Button, dialog_manager: DialogManager):
    from_user = dialog_manager.event.from_user
    user, created = User.get_or_create(user_id = from_user.id)
    balance = checkBalance(user)
    if balance:
        await c.answer(f'Баланс пополнен на {balance}₽!', show_alert = True)
        await dialog_manager.done()
    else:
        await c.answer(f'На баланс ничего не поступало...', show_alert = True)

#### dialog actions



#### Windows

#### states
class WalletSG(StatesGroup):
    receive = State()
    buy = State()

#### dialogs
wallet_dialog = Dialog(
    Window(
        #Format("Текущий баланс: <b>{balance} TON💎</b>"),
        Format("Сейчас баланс берётся из TON Testnet! Получить тестовые монеты можно здесь: @testgiver_ton_bot\n\n"),
        Format("Текущий баланс: <b>{balance}₽</b>"),
        Format("Адрес для пополнения баланса:\n"),
        Format("<code>{wallet}</code>"),
        Format('Можно открыть через <a href="https://app.tonkeeper.com/transfer/{wallet}">Tonkeeper</a>'),
        Format('\n\nПосле отправки TON на указанный адрес - обновите баланс'),
        Format('\n<b>Внимание! Курс TON автоматически сконвертируется в рубли, по текущему курсу <a href="https://www.coingecko.com/ru/Криптовалюты/toncoin/rub">CoinGecko</a></b>'),
        Button(Const("Обновить баланс"), id="check_balance", on_click=check_balance),
        Row(Cancel(Const("Назад")),Next(Const("Купить TON💎"))),
        state=WalletSG.receive,
        disable_web_page_preview=True,
    ),
    Window(
        Format("Сейчас баланс берётся из TON Testnet! Получить тестовые монеты можно здесь: @testgiver_ton_bot\n\n"),
        Format("<s>Купить <b>НАСТОЯЩИЙ</b> TON💎 можно прямо в Telegram, например через через этих ботов:</s>"),
        #Format("Купить TON💎 можно прямо в Telegram, например через через этих ботов:"),
        Row(
            Url(Const("@CryptoBot"),Const('http://t.me/CryptoBot?start=r-304645')),
            Url(Const("@Wallet"),Const('http://t.me/Wallet'))
        ),
        Back(Const("Назад")),
        state=WalletSG.buy,
        disable_web_page_preview=True,
    ),
    getter=get_wallet_data,
)

#### Windows
