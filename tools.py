import datetime
import logging
import math
from os import environ
from typing import Sequence, List, Tuple

import requests
from telebot.types import InlineKeyboardButton

import models
import api
import telebot
from telebot import types
from keys import *
from telebot_main import BANNED_CHARS

logger = logging.getLogger(__name__)


def get_inline_keyboard_page(
        items: Sequence[types.InlineKeyboardButton],
        page: int,
        columns: int,
        pagination_callback: str,
        rows=9,
        back_to="menu",
        add_to_pagination="",
):
    if rows > 9:
        raise ValueError(
            "Telegram API doesn't support more than 10 rows (one needed for pagination buttons)"
        )
    starts_from = (page - 1) * columns * rows
    while starts_from >= len(items):
        page -= 1
        starts_from = (page - 1) * columns * rows
    ends_on = starts_from + columns * rows
    keyboard = []
    for i in range(starts_from, min(len(items), ends_on), columns):
        keyboard.append(items[i: i + columns])
    btns = []
    if page > 1:
        btns.append(
            types.InlineKeyboardButton(
                "<=",
                callback_data=pagination_callback + str(page - 1) + add_to_pagination,
            )
        )
    if len(items) > columns * rows:
        btns.append(
            types.InlineKeyboardButton(
                f"{page}/{math.ceil(len(items) / (columns * rows))}",
                callback_data=f"back&{back_to}",
            )
        )
    else:
        btns.append(
            types.InlineKeyboardButton("Назад", callback_data=f"back&{back_to}")
        )
    if ends_on < len(items):
        btns.append(
            types.InlineKeyboardButton(
                "=>",
                callback_data=pagination_callback + str(page + 1) + add_to_pagination,
            )
        )
    keyboard.append(btns)
    return types.InlineKeyboardMarkup(keyboard)


def cart_buttons_for_product(
        product: models.Product, chat_id: int, from_data: str
) -> list[InlineKeyboardButton] | tuple[list[InlineKeyboardButton], bool]:
    try:
        cart = api.get_cart(chat_id)
    except FileNotFoundError:
        return [
            types.InlineKeyboardButton(
                ADD_TO_CART_BUTTON,
                callback_data=f"add_to_cart&{product.id}*{from_data}",
            )
        ], False
    in_cart = False
    buttons = []
    for prod_in_cart in cart:
        if prod_in_cart.catalogue_item.id == product.id:
            in_cart = True
            buttons.append(
                types.InlineKeyboardButton(
                    "-",
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.catalogue_item.id}&{prod_in_cart.quantity - 1}*{from_data}",
                )
            )
            buttons.append(
                types.InlineKeyboardButton(
                    str(prod_in_cart.quantity),
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.catalogue_item.id}&0*{from_data}",
                )
            )
            buttons.append(
                types.InlineKeyboardButton(
                    "+",
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.catalogue_item.id}&{prod_in_cart.quantity + 1}*{from_data}",
                )
            )
            break
    if not in_cart:
        buttons = [
            types.InlineKeyboardButton(
                ADD_TO_CART_BUTTON,
                callback_data=f"add_to_cart&{product.id}*{from_data}",
            )
        ]
    return buttons, in_cart


def keyboard_for_product(
        chat_id: int, product: models.Product, from_data: str
) -> types.InlineKeyboardMarkup:
    other = api.get_products(name=product.name, brand_id=product.brand)
    for i in other:
        i.photo_url = ""
    buffer = product.photo_url
    product.photo_url = ""
    keyboard = []
    if len(other) > 1:
        other.remove(product)
    product.photo_url = buffer
    for prod in other:
        if prod.id != product.id:
            logging.info(f"found different {prod=} {product=}")
            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        ANOTHER_SIZE_BUTTON.format(size=prod.volume),
                        callback_data=f"product&{prod.id}" + f"*{from_data}"
                        if from_data is not None
                        else "",
                    )
                ]
            )
    buttons, in_cart = cart_buttons_for_product(product, chat_id, from_data)
    keyboard.append(buttons)
    if in_cart:
        keyboard.append(
            [types.InlineKeyboardButton(CHECKOUT_BUTTON, callback_data="cart")]
        )
    keyboard.append([types.InlineKeyboardButton("Назад", callback_data=from_data)])
    return types.InlineKeyboardMarkup(keyboard)


def order_paid(order_id: int, chat_id: int, notify: Tuple[int, ...], username: str):
    user = api.get_user(chat_id)
    order = api.get_order(order_id)
    if order.status not in (models.Status.CASH, models.Status.PAID):
        raise ValueError("Order isn't paid")
    for char in BANNED_CHARS:
        order.address = order.address.replace(char, "\\" + char)
        if username:
            username=username.replace(char, "\\" + char)
        # order.cart=order.cart.replace(char, "\\" + char)
    order.address = order.address.replace("\n", "\n\t\t")
    notification_text = f"""
*Новый заказ*
{order.cart}
*Итого: {order.sum}₽*
Телефон: \\{user.phone_number} \\({"@"+username if username else "No nickname"}\\)
Адрес:
\t\t{order.address}
    
Заказ оплачен *__{"Картой" if order.status == models.Status.PAID else "Наличными"}__*
    """
    bot = telebot.TeleBot(token=environ.get("notification_token"))
    for chat in notify:
        try:
            bot.send_message(chat, notification_text, parse_mode="MarkdownV2")
        except telebot.apihelper.ApiTelegramException as exc:
            logger.error(f"Unable to notify {chat}", exc_info=exc)


def get_payment_link(msg: telebot.types.Message, order: models.Order):
    user=api.get_user(msg.chat.id)
    bill_data = {
        "amount": {
            "currency": "RUB",
            "value": f"{order.sum}.00"
        },
        "comment": f"Заказ №{order.id}",
        "expirationDateTime": (datetime.datetime.now()+datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        "customer": {
            "phone": user.phone_number,
            "account": str(msg.chat.id)
        },
        "customFields": {
            "username": msg.from_user.username or msg.from_user.first_name,
        }
    }
    headers={'content-type': 'application/json','accept': 'application/json','Authorization': f'Bearer {environ.get("qiwi_secret")}'}
    response=requests.put(f'https://api.qiwi.com/partner/bill/v1/bills/{order.id}', headers=headers,json=bill_data)
    if response.status_code!=200:
        raise Exception("Incorrect response")
    return response.json()['payUrl']
