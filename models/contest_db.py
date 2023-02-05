from utils.db_api import db
from peewee import *
from datetime import datetime
from loader import dp
from aiogram import types
from loguru import logger
from .main_db import Channel

class BaseModel(Model):
    class Meta:
        database = db

class Contest(BaseModel):
    chat_id = IntegerField(null = True)
    description = TextField(null = True)
    file_id = TextField(null = True)
    file_typ = TextField(null = True)
    start_contest = TextField(null = True)
    finish_contest = TextField(null = True)
    finish_users_count = IntegerField(null = True)
    winners_count = IntegerField(null = False, default = 1)
    button_text = TextField(null = True, default = "Участвовать")
    attach_preview_message = IntegerField(null = True)
    need_channels = ManyToManyField(Channel, backref = 'contests')
    status = TextField(null = True, default = 'wizard')
    url = TextField(null = True)
    start_schedule = TextField(null = True)
    finish_schedule = TextField(null = True)

    def __str__(self):
        return self.description
        
class Participate(BaseModel):
    user_id = IntegerField(null = False)
    chat_id = IntegerField(null = False)
    contest_id = IntegerField(null = False)
    created_at = DateTimeField(default=datetime.now)



def create_contest_dbs():
    global db
    db.create_tables([
        Contest,
        Participate,
        Contest.need_channels.get_through_model(),
        #Departament,
        #GroupChat,
        #Manager,
        #Project,
        #Project.chats.get_through_model(),
        #Project.managers.get_through_model(),
        #Departament.managers.get_through_model(),
        ])
