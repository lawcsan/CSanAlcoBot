from utils.db_api import db
from peewee import *
from datetime import datetime
from loader import dp
from aiogram import types
from loguru import logger

class BaseModel(Model):
    class Meta:
        database = db


class Drink(BaseModel):
    name = CharField(max_length = 120, null = True)
    cost = FloatField(default = 0)

    def __str__(self):
        return self.name
        

def create_drink_dbs():
    global db
    db.create_tables([
        Drink,
        ])
