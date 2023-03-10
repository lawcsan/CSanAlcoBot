from aiogram_dialog import DialogRegistry

from modules.drinks.list import drinks_menu
from modules.alcomixer.main import mixer_dialog
from modules.wallet.main import wallet_dialog


def register_all_modules(registry: DialogRegistry) -> None:
    registry.register(drinks_menu)
    registry.register(mixer_dialog)
    registry.register(wallet_dialog)
    
