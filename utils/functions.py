#from os import getenv
from aiogram_dialog import DialogManager
from models.main_db import User

from tonsdk.contract.wallet import WalletVersionEnum, Wallets
from tonsdk.utils import bytes_to_b64str
from tonsdk.crypto import mnemonic_new
import requests

#from modules.contest.GetterContest import *

from config_reader import config
def list_admins():
    data = config.admins.get_secret_value()
    return list(map(int, filter(None, data.split(','))))

async def upd_start_data(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.current_context().dialog_data
    data.update(dialog_manager.current_context().start_data or {})
    data.update(await contest_fields_getter(dialog_manager))
    return data

async def checkAdminAccess(bot, chat_id, admin_id):
    """Проверка прав админа бота и юзера"""
    ret = []
    try:
        me = await bot.get_me()
        admins = await bot.get_chat_administrators(chat_id = chat_id)
        for u in admins:
            if u.user.id in [admin_id, me.id]:
                ret.append(u.user.id)
    except Exception as e:
        logger.error('Cant check admin access Chat id: {chat_id}')
        logger.error(repr(e))
    if sorted(ret) == sorted([admin_id, me.id]):
        return True
    return False










def newWallet():
    wallet_workchain = 0
    wallet_version = WalletVersionEnum.v3r2
    wallet_mnemonics = mnemonic_new()

    _mnemonics, _pub_k, _priv_k, wallet = Wallets.from_mnemonics(wallet_mnemonics, wallet_version, wallet_workchain)

    query = wallet.create_init_external_message()
    base64_boc = bytes_to_b64str(query["message"].to_boc(False))
    return ' '.join(wallet_mnemonics), wallet.address.to_string(True, True, True)


def checkBalance(user):
    minLt = int(user.minLt)
    data = {'account' : user.wallet, 'limit': 100, 'minLt': minLt}
    oldbalance = user.balance
    balance = 0
    method = 'getTransactions'
    pref= 'blockchain'
    url = f'https://tonapi.io/v1/{pref}/{method}'
    url = f'https://testnet.tonapi.io/v1/{pref}/{method}'
    data['minLt'] = minLt
    response = requests.get(url, params=data)
    j = response.json()
    for t in j['transactions'] or []:
        minLt = max(t['lt'], minLt)
        print(minLt, t)
        b = t.get('in_msg').get('value') / 1000000000
        if b:
            balance += ton_rub(b)
    user.minLt = str(minLt)
    user.save()
    if balance + oldbalance != user.balance:
        user.balance = round(balance + oldbalance, 5)
        user.minLt = str(minLt)
        user.save()
        return balance
    return 0

async def get_wallet_data(dialog_manager: DialogManager, **kwargs):
    from_user = dialog_manager.event.from_user
    user, created = User.get_or_create(user_id = from_user.id)
    if not user.wallet or not user.mnemonic:
        user.username = from_user.username
        user.first_name = from_user.first_name
        user.last_name = from_user.last_name
        user.mnemonic, user.wallet = newWallet()
        user.save()
    
    return {
        "name": dialog_manager.current_context().dialog_data.get("name"),
        "wallet": user.wallet,
        "balance": round(user.balance, 2),
        #"balance_rub": float(user.balance),
    }


def ton_rub(amount = 1):
    ton_id = 'the-open-network'
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ton_id}&vs_currencies=rub'
    response = requests.get(url)
    j = response.json()
    price = j.get(ton_id).get('rub')
    return price * amount
