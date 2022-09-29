import logging
import math
from typing import Sequence
import models
import api
import telebot
from telebot import types

from os import environ
from telebot_main import BANNED_CHARS


def get_inline_keyboard_page(
    items: Sequence[types.InlineKeyboardButton],
    page: int,
    columns: int,
    pagination_callback: str,
    rows=9,
    back_to="menu",
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
        keyboard.append(items[i : i + columns])
    btns = []
    if page > 1:
        btns.append(
            types.InlineKeyboardButton(
                "<=", callback_data=pagination_callback + str(page - 1)
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
                "=>", callback_data=pagination_callback + str(page + 1)
            )
        )
    keyboard.append(btns)
    return types.InlineKeyboardMarkup(keyboard)


def cart_buttons_for_product(
    product: models.Product, chat_id: int, from_data: str
) -> list[types.InlineKeyboardButton]:
    try:
        cart = api.get_cart(chat_id)
    except FileNotFoundError:
        return [
            types.InlineKeyboardButton(
                "В корзину", callback_data=f"add_to_cart&{product.id};{from_data}"
            )
        ]
    in_cart = False
    buttons = []
    for prod_in_cart in cart:
        if prod_in_cart.catalogue_item == product:
            in_cart = True
            buttons.append(
                types.InlineKeyboardButton(
                    "-",
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.catalogue_item.id}&{prod_in_cart.quantity - 1};{from_data}",
                )
            )
            buttons.append(
                types.InlineKeyboardButton(
                    str(prod_in_cart.quantity),
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.catalogue_item.id}&0;{from_data}",
                )
            )
            buttons.append(
                types.InlineKeyboardButton(
                    "+",
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.catalogue_item.id}&{prod_in_cart.quantity + 1};{from_data}",
                )
            )
            break
    if not in_cart:
        buttons = [
            types.InlineKeyboardButton(
                "В корзину", callback_data=f"add_to_cart&{product.id};{from_data}"
            )
        ]
    return buttons


def keyboard_for_product(chat_id: int, product: models.Product, from_data: str):
    other = api.get_products(name=product.name)
    keyboard = []
    if len(other) > 1:
        other.remove(product)
    for prod in other:
        if (
            prod != product
            and prod.brand == product.brand
            and prod.category == product.category
        ):
            logging.info(f"found different {prod=} {product=}")
            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        "Ещё есть на " + prod.volume,
                        callback_data=f"product&{prod.id}" + f";{from_data}"
                        if from_data is not None
                        else "",
                    )
                ]
            )
    keyboard.append(cart_buttons_for_product(product, chat_id, from_data))
    keyboard.append([types.InlineKeyboardButton("Назад", callback_data=from_data)])
    return types.InlineKeyboardMarkup(keyboard)


def order_paid(order_id: int):
    order = api.get_order(order_id)
    user = api.get_user(order.client)
    if order.status not in (models.Status.CASH, models.Status.PAID):
        raise ValueError("Order isn't paid")
    for char in BANNED_CHARS:
        order.address = order.address.replace(char, "\\" + char)
    order.address = order.address.replace("\n", "\n\t\t")
    notification_text = f"""
*Новый заказ*
{order.cart}
Телефон: {user.phone_number}
Адрес:
\t\t{order.address}

Заказ оплачен *__{"Картой" if order.status == models.Status.PAID else "Наличными"}__*
    """
    bot = telebot.TeleBot(token=environ.get('notification_token'))
    bot.send_message(
        environ.get('notification_chat'), notification_text, parse_mode="MarkdownV2"
    )
    api.clear_cart(order.client)
