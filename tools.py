import math
from typing import Sequence

from telebot import types


def get_inline_keyboard_page(items: Sequence[types.InlineKeyboardButton], page: int, columns: int,
                             pagination_callback: str,
                             rows=9, back_to='menu'):
    starts_from = (page - 1) * columns * rows
    if starts_from>len(items):
        starts_from=0
        page=1
    ends_on = starts_from + columns * rows
    keyboard = []
    for i in range(starts_from, min(len(items), ends_on), columns):
        keyboard.append(items[i:i + columns])
    btns = []
    if page > 1:
        btns.append(types.InlineKeyboardButton('<=', callback_data=pagination_callback + str(page - 1)))
    if len(items) > columns * rows:
        btns.append(types.InlineKeyboardButton(f'{page}/{math.ceil(len(items) / (columns * rows))}',
                                               callback_data=f'back&{back_to}'))
    else:
        btns.append(types.InlineKeyboardButton('Назад', callback_data=f'back&{back_to}'))
    if ends_on < len(items):
        btns.append(types.InlineKeyboardButton('=>', callback_data=pagination_callback + str(page + 1)))
    keyboard.append(btns)
    return types.InlineKeyboardMarkup(keyboard)
