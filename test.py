from telebot_main import bot
from telebot import *
from telebot.util import quick_markup


for i in range(100):
    keyboard= quick_markup({str(i):{'callback_data':"brand="+chr(i)*i}})
    bot.send_message(354640082,str(i),reply_markup=keyboard)