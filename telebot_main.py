import logging

import telebot.apihelper
from telebot import TeleBot, types
from telebot.util import quick_markup

import api
import models
import secure
import tools
from keys import *

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] -  (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
)

BANNED_CHARS = (
    "_",
    "*",
    "[",
    "]",
    "(",
    ")",
    "~",
    "`",
    ">",
    "#",
    "+",
    "-",
    "=",
    "|",
    "{",
    "}",
    ".",
    "!",
)
bot = TeleBot(token=secure.teletoken)


@bot.message_handler(commands=["start"])
def start(msg: types.Message):
    logging.info(f"{msg.chat.id} came")

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(START_BUTTON))
    bot.send_message(
        msg.chat.id,
        START_MESSAGE,
        reply_markup=keyboard,
    )
    bot.register_next_step_handler(msg, prove_18)


def prove_18(msg: types.Message):
    logging.info(f"{msg.chat.id} came")

    if msg.text == START_BUTTON:
        bot.send_message(
            msg.chat.id,
            START_ANSWER_SUCCESS,
            reply_markup=types.ReplyKeyboardRemove(),
        )
        menu(msg)
    else:
        bot.send_message(msg.chat.id, START_ANSWER_FAIL)
        bot.register_next_step_handler(msg, start)


# -------------------------------------------------------------------------------------


@bot.message_handler(commands=["menu"])
def menu(msg: types.Message, edit=False):
    logging.info(f"{msg.chat.id} came")
    try:
        cart = api.get_cart(msg.chat.id)
    except FileNotFoundError:
        cart = []
    structure = []
    structure.append(
        [
            types.InlineKeyboardButton(
                MENU_BY_CATEGORY_BUTTON, callback_data="menu_by_cat&1"
            ),
            types.InlineKeyboardButton(
                MENU_BY_BRAND_BUTTON, callback_data="menu_by_brand&1"
            ),
        ]
    )
    structure.append(
        [
            types.InlineKeyboardButton(
                f"Корзина ({len(cart)}) {sum(tuple(item.sum for item in cart))}₽",
                callback_data="cart",
            )
        ]
    )
    keyboard = types.InlineKeyboardMarkup(structure)
    if edit:
        bot.edit_message_text(
            MENU_MESSAGE, msg.chat.id, msg.message_id, reply_markup=keyboard
        )
    else:
        bot.send_message(msg.chat.id, MENU_MESSAGE, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.split("&")[0] == "back")
def back(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    match data.data.split("&")[1]:
        case "menu":
            bot.answer_callback_query(data.id, "Меню")
            menu(data.message, True)
        case "menu_by_brand":
            data.data = "&".join(data.data.split("&")[1:])
            menu_by_brand(data)
        case "menu_by_cat":
            data.data = "&".join(data.data.split("&")[1:])
            menu_by_category(data)
        case "brand":
            data.data = "&".join(data.data.split("&")[1:])
            products_by_brand(data)
        case "category":
            data.data = "&".join(data.data.split("&")[1:])
            products_by_category(data)
        case "cart":
            data.data = "&".join(data.data.split("&")[1:])
            get_cart_by_callback(data)
        case _:
            raise ValueError(f'Unresolved for {data.data.split("&")[1]}')


@bot.callback_query_handler(func=lambda data: data.data.startswith("menu_by_brand"))
def menu_by_brand(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    brands = tuple(
        types.InlineKeyboardButton(brand.name, callback_data=f"brand&{brand.id}&1")
        for brand in api.get_brands()
    )
    keyboard = tools.get_inline_keyboard_page(
        brands, int(data.data.split("&")[1]), 2, "menu_by_brand&"
    )
    bot.answer_callback_query(data.id, BRAND_SUBMENU_BUTTON_ANSWER)
    bot.edit_message_text(
        BRAND_SUBMENU_MESSAGE,
        data.message.chat.id,
        data.message.message_id,
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda data: data.data.startswith("brand"))
def products_by_brand(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    brand_id = int(data.data.split("&")[1])
    page = int(data.data.split("&")[2])
    products = api.get_products(brand_id=brand_id)
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(
            product.name, callback_data=f"product&{product.id};{data.data}"
        )
        for product in products
    )
    keyboard = tools.get_inline_keyboard_page(
        keyboard_buttons,
        page,
        2,
        pagination_callback=f"brand&{brand_id}&",
        back_to="menu_by_brand&1",
    )
    bot.answer_callback_query(data.id, BRAND_SUBMENU_BUTTON_ANSWER)
    try:
        bot.edit_message_text(
            BRAND_SUBMENU_MESSAGE,
            data.message.chat.id,
            data.message.message_id,
            reply_markup=keyboard,
        )
    except telebot.apihelper.ApiTelegramException as exc:
        # logging.error('API TELEGRAM ERROR',exc)

        try:
            bot.delete_message(data.message.chat.id, data.message.message_id)
        except telebot.apihelper.ApiTelegramException:
            pass
        bot.send_message(
            data.message.chat.id, BRAND_SUBMENU_MESSAGE, reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda data: data.data.split("&")[0] == "menu_by_cat")
def menu_by_category(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    categories = tuple(
        types.InlineKeyboardButton(
            category.name, callback_data=f"category&{category.id}"
        )
        for category in api.get_categories()
    )
    keyboard = tools.get_inline_keyboard_page(
        categories, int(data.data.split("&")[1]), 2, "menu_by_cat&"
    )
    bot.answer_callback_query(data.id, CATEGORY_SUBMENU_BUTTON_ANSWER)
    bot.edit_message_text(
        CATEGORY_SUBMENU_MESSAGE,
        data.message.chat.id,
        data.message.message_id,
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda data: data.data.startswith("category"))
def products_by_category(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    category_id = int(data.data.split("&")[1])
    page = int(data.data.split("&")[2]) if len(data.data.split("&")) == 3 else 1
    products = api.get_products(category_id=category_id)
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(
            product.name, callback_data=f"product&{product.id};{data.data}"
        )
        for product in products
    )
    keyboard = tools.get_inline_keyboard_page(
        keyboard_buttons,
        page,
        2,
        "&".join(data.data.split("&")[:2]) + "&",
        back_to="menu_by_cat&1",
    )
    bot.answer_callback_query(data.id, PRODUCTS_BY_CATEGORY_BUTTON_ANSWER)
    try:
        bot.edit_message_text(
            PRODUCTS_BY_CATEGORY_MESSAGE,
            data.message.chat.id,
            data.message.message_id,
            reply_markup=keyboard,
        )
    except telebot.apihelper.ApiTelegramException as exc:
        # logging.error('API TELEGRAM ERROR',exc)
        try:
            bot.delete_message(data.message.chat.id, data.message.message_id)
        except telebot.apihelper.ApiTelegramException:
            pass
        bot.send_message(
            data.message.chat.id, PRODUCTS_BY_CATEGORY_MESSAGE, reply_markup=keyboard
        )


# -------------------------------------------------------------------------------------


@bot.callback_query_handler(func=lambda data: data.data.startswith("product"))
def product_card(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split(";")
    try:
        product = api.get_products(id=int(direct_data.split("&")[1]))[0]
    except FileNotFoundError:
        bot.edit_message_text(
            PRODUCT_NOT_FOUND_MESSAGE,
            data.message.chat.id,
            data.message.message_id,
            reply_markup=quick_markup({"Назад": {"callback_query": from_data}}),
        )
        return
    brand = product.get_brand_name()
    category = product.get_category_name()
    for char in BANNED_CHARS:
        product.name = product.name.replace(char, "\\" + char)
        brand = brand.replace(char, "\\" + char)
        # category=category.replace(char,'\\'+char)
        product.volume = product.volume.replace(char, "\\" + char)
    text = PRODUCT_CARD.format(price=product.price, brand=brand, name=product.name)
    if product.volume != "Безразмерный":
        text += "\n" + PRODUCT_CARD_SIZE.format(size=product.volume)
    keyboard = keyboard_for_product(
        chat_id=data.message.chat.id, product=product, from_data=from_data
    )
    photo = product.get_photo()
    bot.delete_message(data.message.chat.id, data.message.message_id)
    bot.send_photo(
        data.message.chat.id, photo, text, "MarkdownV2", reply_markup=keyboard
    )


def keyboard_for_product(chat_id: int, product: models.Product, from_data: str):
    other = api.get_products(name=product.name)
    keyboard = []
    if len(other) > 1:
        other.remove(product)
    for prod in other:
        if prod != product:
            logging.info(f"found different {prod=} {product=}")
            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        ANOTHER_SIZE_BUTTON,
                        callback_data=f"product&{prod.id}" + f";{from_data}"
                        if from_data is not None
                        else "",
                    )
                ]
            )
    keyboard.append(cart_buttons_for_product(product, chat_id, from_data))
    keyboard.append([types.InlineKeyboardButton("Назад", callback_data=from_data)])
    return types.InlineKeyboardMarkup(keyboard)


# -------------------------------------------------------------------------------------
@bot.message_handler(commands=["cart"])
def get_cart(msg: types.Message, edit=False):
    logging.info(f"{msg.chat.id} came")
    cart_text = [FIRST_CART_MESSAGE]
    try:
        cart_list = api.get_cart(msg.chat.id)
    except FileNotFoundError:
        cart_text = EMPTY_CART_MESSAGE
        keyboard = quick_markup(
            {
                "Обновить корзину": {"callback_data": "cart"},
                "В меню": {"callback_data": "back&menu"},
            },
            1,
        )
    else:
        sum_ = 0
        for index, item in enumerate(cart_list):
            for char in BANNED_CHARS:
                item.catalogue_item.name = item.catalogue_item.name.replace(
                    char, "\\" + char
                )
                item.catalogue_item.volume = item.catalogue_item.volume.replace(
                    char, "\\" + char
                )
            cart_text.append(
                ITEM_CART_MESSAGE.format(
                    number=index,
                    name=item.catalogue_item.name,
                    size=item.catalogue_item.volume
                    if item.catalogue_item.volume != "Безразмерный"
                    else " ",
                    price=item.catalogue_item.price,
                    quantity=item.quantity,
                    sum=item.sum,
                )
            )
            sum_ += item.sum
        cart_text.append(END_CART_MESSAGE.format(sum=sum_))
        cart_text = '\n'.join(cart_text)
        print(cart_text)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                EDIT_CART_BUTTON, callback_data="edit_cart"
            )
        )
        keyboard.add(
            types.InlineKeyboardButton("Обновить корзину", callback_data="cart")
        )
        keyboard.add(
            types.InlineKeyboardButton(
                CHECKOUT_BUTTON, callback_data="checkout"
            )
        )
        keyboard.add(types.InlineKeyboardButton("В меню", callback_data="back&menu"))
    if not edit:
        bot.send_message(
            msg.chat.id, cart_text, reply_markup=keyboard, parse_mode="MarkdownV2"
        )
    else:
        bot.edit_message_text(
            cart_text,
            msg.chat.id,
            msg.message_id,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )


@bot.callback_query_handler(lambda data: data.data == "cart")
def get_cart_by_callback(data):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    bot.answer_callback_query(data.id, "Корзина")
    get_cart(data.message, True)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "edit_cart")
def edit_cart(data: types.CallbackQuery, answer=True):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    page = int(data.data.split("&")[1]) if len(data.data.split("&")) > 1 else 1
    cart_text = [FIRST_CART_MESSAGE]
    try:
        cart_list = api.get_cart(data.message.chat.id)
    except FileNotFoundError:
        bot.edit_message_text(
            EMPTY_CART_MESSAGE,
            data.message.chat.id,
            data.message.message_id,
            reply_markup=quick_markup({"Назад": {"callback_data": "back&cart"}}),
        )
        return None
    sum_ = 0
    buttons = []
    for index, item in enumerate(cart_list):
        buttons.append(
            types.InlineKeyboardButton(
                f"{item.catalogue_item.name}",
                callback_data=item.catalogue_item.id,
            )
        )
        for char in BANNED_CHARS:
            item.catalogue_item.name = item.catalogue_item.name.replace(
                char, "\\" + char
            )
            item.catalogue_item.volume = item.catalogue_item.volume.replace(
                char, "\\" + char
            )
        cart_text.append(
            ITEM_CART_MESSAGE.format(
                number=index,
                name=item.catalogue_item.name,
                size=item.catalogue_item.volume
                if item.catalogue_item.volume != "Безразмерный"
                else " ",
                price=item.catalogue_item.price,
                quantity=item.quantity,
                sum=item.sum,
            )
        )
        sum_ += item.sum
        buttons.append(
            types.InlineKeyboardButton(
                "-",
                callback_data=f"edit_in_cart&{item.cart_id}&{item.quantity - 1}&{page}",
            )
        )
        buttons.append(
            types.InlineKeyboardButton(
                "+",
                callback_data=f"edit_in_cart&{item.cart_id}&{item.quantity + 1}&{page}",
            )
        )
        buttons.append(
            types.InlineKeyboardButton(
                f"{item.quantity}шт ❌", callback_data=f"remove&{item.cart_id}&{page}"
            )
        )
    cart_text.append(END_CART_MESSAGE.format(sum=sum_))
    cart_text = '\n'.join(cart_text)
    if answer:
        bot.answer_callback_query(data.id, EDIT_CART_BUTTON_ANSWER)
    keyboard = tools.get_inline_keyboard_page(
        buttons, page, 4, "edit_cart&", back_to="cart"
    )
    bot.edit_message_text(
        cart_text,
        data.message.chat.id,
        data.message.message_id,
        reply_markup=keyboard,
        parse_mode="MarkdownV2",
    )


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "edit_in_cart")
def edit_quantity(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    cart_id = int(data.data.split("&")[1])
    quantity = int(data.data.split("&")[2])
    page = int(data.data.split("&")[3])
    api.edit_cart(cart_id, data.message.chat.id, quantity)
    data.data = f"edit_cart&{page}"
    bot.answer_callback_query(
        data.id, CHANGE_QUANTITY_BUTTON_ANSWER.format(quantity=quantity)
    )
    edit_cart(data, False)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "remove")
def remove_from_cart(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    page = int(data.data.split("&")[2])
    try:
        api.edit_cart(int(data.data.split("&")[1]), data.message.chat.id, 0)
    except FileNotFoundError:
        bot.answer_callback_query(data.id, NO_PRODUCT_IN_CART_ON_EDIT_BUTTON_ANSWER)
    else:
        bot.answer_callback_query(data.id, DELETED_FROM_CART_BUTTON_ANSWER)
    data.data = f"edit_cart&{page}"
    edit_cart(data)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "add_to_cart")
def add_to_cart(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split(";")
    product = direct_data.split("&")[1]
    if api.add_to_cart(product_id=product, chat_id=data.message.chat.id):
        product = api.get_products(id=int(product))[0]
        bot.answer_callback_query(
            data.id, ADD_TO_CART_BUTTON_ANSWER.format(product_name=product.name)
        )
        keyboard = keyboard_for_product(data.message.chat.id, product, from_data)
        # try:
        bot.edit_message_reply_markup(
            data.message.chat.id, data.message.message_id, reply_markup=keyboard
        )
        # except telebot.apihelper.ApiTelegramException:
        #     product_card(data)

    else:
        bot.answer_callback_query(data.id, ADD_TO_CART_FAIL_BUTTON_ANSWER)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "edit")
def edit_product_cart(data: types.CallbackQuery):
    logging.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split(";")
    direct_data = direct_data.split("&")
    cart_id = int(direct_data[1])
    catalogue_id = int(direct_data[2])
    quantity = int(direct_data[3])

    try:
        if quantity:
            cart_item = api.edit_cart(cart_id, data.message.chat.id, quantity)
            assert cart_item.quantity == quantity
        else:
            cart_item = [
                item
                for item in api.get_cart(data.message.chat.id)
                if item.cart_id == cart_id
            ][0]
            api.edit_cart(cart_id, data.message.chat.id, quantity := int(quantity))
            cart_item.quantity = 0
    except FileNotFoundError:
        bot.answer_callback_query(data.id, NO_PRODUCT_IN_CART_ON_EDIT_BUTTON_ANSWER)
        cart_item = api.get_products(id=catalogue_id)[0]
        keyboard = keyboard_for_product(data.message.chat.id, cart_item, from_data)
    else:
        bot.answer_callback_query(
            data.id, str(quantity) if quantity else DELETED_FROM_CART_BUTTON_ANSWER
        )
        keyboard = keyboard_for_product(
            data.message.chat.id, cart_item.catalogue_item, from_data
        )
    try:
        bot.edit_message_reply_markup(
            data.message.chat.id, data.message.message_id, reply_markup=keyboard
        )
    except telebot.apihelper.ApiTelegramException as exc:
        logging.error("API TELEGRAM ERROR", exc)


@bot.callback_query_handler(lambda x: True)
def default_answer(data: types.CallbackQuery):
    logging.info(f"default callback query answer to {data.data}")
    if data.data.isdigit():
        bot.answer_callback_query(data.id, api.get_products(id=int(data.data))[0].name)
    bot.answer_callback_query(data.id, data.data)


def cart_buttons_for_product(
        product: models.Product, chat_id: int, from_data: str
) -> list[types.InlineKeyboardButton]:
    try:
        cart = api.get_cart(chat_id)
    except FileNotFoundError:
        return [
            types.InlineKeyboardButton(
                ADD_TO_CART_BUTTON,
                callback_data=f"add_to_cart&{product.id};{from_data}",
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
                ADD_TO_CART_BUTTON,
                callback_data=f"add_to_cart&{product.id};{from_data}",
            )
        ]
    return buttons


if __name__ == "__main__":
    bot.polling(non_stop=True)
