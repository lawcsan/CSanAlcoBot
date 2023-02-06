from loguru import logger
from config_reader import config
from aiogram import Bot, Dispatcher, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
#from apscheduler_di import ContextSchedulerDecorator
from typing import Optional
from aiogram.types import Message


from middlewares import ThrottlingMiddleware #, SchedulerMiddleware
from apscheduler.jobstores.redis import RedisJobStore


#from aiogram.contrib.fsm_storage.redis import RedisStorage2
#storage = RedisStorage2('localhost', 6379)

from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()

bot = Bot(token=config.bot_token.get_secret_value(), parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)



#scheduler = AsyncIOScheduler()
job_stores = {
    "default": RedisJobStore(
        jobs_key="dispatched_trips_jobs", run_times_key="dispatched_trips_running",
        # параметры host и port необязательны, для примера показано как передавать параметры подключения
        host="localhost", port=6379
    )
}


scheduler = AsyncIOScheduler(jobstores=job_stores)
#scheduler = ContextSchedulerDecorator(AsyncIOScheduler(jobstores=job_stores))
#scheduler.ctx.add_instance(bot, declared_class=Bot)


dp.setup_middleware(ThrottlingMiddleware())
#dp.setup_middleware(SchedulerMiddleware(scheduler))


scheduler.start()

from aiogram_dialog import DialogRegistry
from modules import *






async def remove_kbd(bot: Bot, old_message: Optional[Message]):
    if old_message:
        try:
            await bot.delete_message(
                message_id=old_message.message_id,
                chat_id=old_message.chat.id,
            )
        except:
            pass  # nothing to remove



registry = DialogRegistry(dp)
registry._message_manager.remove_kbd = remove_kbd
register_all_modules(registry)


@dp.errors_handler()
async def some_error(msg, error):
    logger.error("ERROR {} {}".format(error, msg))


logger.info('all modules loaded!')
