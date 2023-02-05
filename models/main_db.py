from utils.db_api import db
from peewee import *
from datetime import datetime
from loader import dp
from aiogram import types
from loguru import logger


class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = IntegerField(primary_key = True, null = False, index = True, unique = True)
    username = CharField(max_length = 120, null = True)
    first_name = CharField(max_length = 120, null = True)
    last_name = CharField(max_length = 120, null = True)
    tz = CharField(max_length = 120, null = True)
    is_admin = BooleanField(default = False)
    
    wallet = CharField(max_length = 120, null = True)
    mnemonic = TextField(null = True)
    balance = FloatField(default = 100)
    minLt = CharField(default = "0")

    @property
    def short_name(self):
        return f'{self.first_name or ""} {self.last_name or ""}'

    @property
    def name(self):
        return str(self)

    @property
    def id(self):
        return self.user_id

    def __str__(self):
        return f'{self.first_name or ""} {self.last_name or ""} @{self.username or ""}'


class Channel(BaseModel):
    chat_id = IntegerField(null = False, index = True, unique = True)
    name = CharField(max_length = 500, null = True)
    bot_status = CharField(max_length = 500, null = True)
    admins = TextField(null = True)
    def __str__(self):
        return self.name
        


@dp.my_chat_member_handler()
async def my_chat_member_handler(my_chat_member: types.ChatMemberUpdated):
    new_chat_member = my_chat_member.new_chat_member
    old_chat_member = my_chat_member.old_chat_member
    forbot = await my_chat_member.bot.get_me()
    try:
        chat = Channel.get(chat_id=my_chat_member.chat.id)
    except DoesNotExist:
        chat = Channel.create(chat_id=my_chat_member.chat.id, name = my_chat_member.chat.title)
        upd = True
    
    if forbot.id == new_chat_member.user.id or upd:
        chat.bot_status = new_chat_member.status
        chat.save()
        logger.info(f'Bot new status in channel: [{my_chat_member.chat.id}] {my_chat_member.chat.title}, Status: {chat.bot_status}')
        if chat.bot_status == 'administrator' or upd:
            await updAdmins(my_chat_member)
        

@dp.chat_member_handler()
async def chat_member_handler(chat_member: types.ChatMemberUpdated):
    upd = False
    try:
        chat = Channel.get(chat_id=chat_member.chat.id)
    except DoesNotExist:
        chat = Channel.create(chat_id=chat_member.chat.id, name = chat_member.chat.title)
        upd = True
        
    new_chat_member = chat_member.new_chat_member
    old_chat_member = chat_member.old_chat_member
    if 'administrator' in [new_chat_member.status, old_chat_member.status] or upd:
        await updAdmins(chat_member)
        
async def updAdmins(chat_member):
    try:
        chat = Channel.get(chat_id=chat_member.chat.id)
    except DoesNotExist:
        chat = Channel.create(chat_id=chat_member.chat.id, name = chat_member.chat.title)
    try:
        admins = await chat_member.chat.get_administrators()
        admin_ids = [str(t.user.id) for t in admins if not t.user.is_bot]
        chat.name = chat_member.chat.title
        chat.admins = ','.join(admin_ids)
        chat.save()
        logger.info(f'New admin list in channel: [{chat_member.chat.id}] {chat.name} Admins: {chat.admins}')
    except Exception as e:
        logger.error('Cant get admin list in chat', chat_member)
        logger.error(repr(e))
    

#class Departament(BaseModel):
    #name = CharField(max_length = 500, null = True)
    #managers = ManyToManyField(User, backref = 'departaments')
    #def __str__(self):
        #return self.name


#class GroupChat(BaseModel):
    #chat_id = IntegerField(null = False, index = True, unique = True)
    #name = CharField(max_length = 500, null = True)
    #def __str__(self):
        #return self.name


#class Manager(BaseModel):
    #user_id = IntegerField(primary_key = True, null = False, index = True, unique = True)
    #def user(self):
        #return User.get(user_id = self.user_id)
    #def __str__(self):
        #return str(self.user())


#class Project(BaseModel):
    #name = CharField(max_length = 500, null = True)
    #chats = ManyToManyField(GroupChat, backref = 'projects')
    #managers = ManyToManyField(User, backref = 'projects')
    #def __str__(self):
        #return self.name


def create_main_dbs():
    global db
    db.create_tables([
        User,
        Channel,
        #Departament,
        #GroupChat,
        #Manager,
        #Project,
        #Project.chats.get_through_model(),
        #Project.managers.get_through_model(),
        #Departament.managers.get_through_model(),
        ])
