from aiogram import executor
from loader import dp
from logs.logger_conf import *
from aiogram import types

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates = True, allowed_updates=(types.AllowedUpdates.all()))
