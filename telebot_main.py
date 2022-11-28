import os
from dotenv import load_dotenv
import logging
import typing
from datetime import datetime
import telebot.apihelper
from telebot import TeleBot, types
from telebot.util import quick_markup
from keys import *
import api
import models
import tools

logging.basicConfig(
    filename=f"bot-from-{datetime.now().date()}.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] -  (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
)
NOTIFICATION_CHATS = (354640082, 847709370, -1001743990374)
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
FREE_DELIVERY_FROM = 1500
DELIVERY_COST = 150
MIN_ORDER_SUM = 500
bot = TeleBot(token=os.environ.get("teletoken"))
logger = logging.getLogger(__name__)
load_dotenv()


@bot.message_handler(commands=["start"])
def start(msg: types.Message):
    logger.info(f"{msg.chat.id} came")

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(START_BUTTON))
    bot.send_message(
        msg.chat.id,
        START_MESSAGE,
        reply_markup=keyboard,
    )
    bot.register_next_step_handler(msg, prove_18)


def prove_18(msg: types.Message):
    logger.info(f"{msg.chat.id} came")

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
    logger.info(f"{msg.chat.id} came")
    try:
        cart = api.get_cart(msg.chat.id)
    except FileNotFoundError:
        cart = []
    structure = []
    structure.append(
        [types.InlineKeyboardButton(TO_CATALOGUE_BUTTON, callback_data="menu_by_cat&1")]
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
    logger.info(f"{data.message.chat.id} came with {data.data}")
    match data.data.split("&")[1]:
        case "menu":
            bot.answer_callback_query(data.id, "Меню")
            menu(data.message, True)
        # case "menu_by_brand":
        #     data.data = "&".join(data.data.split("&")[1:])
        #     menu_by_brand(data)
        case "menu_by_cat":
            data.data = "&".join(data.data.split("&")[1:])
            menu_by_category(data)
        case "brand":
            data.data = "&".join(data.data.split("&")[1:])
            products_by_brand(data)
        case "category":
            data.data = "&".join(data.data.split("&")[1:])
            brands_by_category(data)
        case "cart":
            data.data = "&".join(data.data.split("&")[1:])
            get_cart_by_callback(data)
        case _:
            raise ValueError(f'Unresolved for {data.data.split("&")[1]}')


# @bot.callback_query_handler(func=lambda data: data.data.startswith("menu_by_brand"))
# def menu_by_brand(data: types.CallbackQuery):
#     logger.info(f"{data.message.chat.id} came with {data.data}")
#     brands = tuple(
#         types.InlineKeyboardButton(brand.name, callback_data=f"brand&{brand.id}&1")
#         for brand in api.get_brands()
#     )
#     keyboard = tools.get_inline_keyboard_page(
#         brands, int(data.data.split("&")[1]), 2, "menu_by_brand&"
#     )
#     bot.answer_callback_query(data.id, BRAND_SUBMENU_BUTTON_ANSWER)
#     bot.edit_message_text(
#         BRAND_SUBMENU_MESSAGE,
#         data.message.chat.id,
#         data.message.message_id,
#         reply_markup=keyboard,
#     )


@bot.callback_query_handler(func=lambda data: data.data.startswith("brand"))
def products_by_brand(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    dat, back_to = data.data.split(";")
    brand_id = int(dat.split("&")[1])
    category_id = int(back_to.split("&")[1])
    page = int(dat.split("&")[2])
    products_ = api.get_products(brand_id=brand_id, category_id=category_id)
    names = set()
    products = []
    for product in products_:
        if product.name not in names:
            names.add(product.name)
            products.append(product)
    products.sort(key=lambda prod: prod.name)
    keyboard_buttons = list(
        types.InlineKeyboardButton(
            product.name, callback_data=f"product&{product.id}*{data.data}"
        )
        for product in products
    )
    keyboard = tools.get_inline_keyboard_page(
        keyboard_buttons,
        page,
        2,
        pagination_callback=f"brand&{brand_id}&",
        back_to=back_to,
        add_to_pagination=";" + back_to,
    )
    bot.answer_callback_query(data.id, BRAND_SUBMENU_BUTTON_ANSWER)
    try:
        bot.edit_message_text(
            PRODUCTS_BY_CATEGORY_MESSAGE,
            data.message.chat.id,
            data.message.message_id,
            reply_markup=keyboard,
        )
    except telebot.apihelper.ApiTelegramException as exc:
        # logger.error('API TELEGRAM ERROR',exc)

        try:
            bot.delete_message(data.message.chat.id, data.message.message_id)
        except telebot.apihelper.ApiTelegramException:
            pass
        bot.send_message(
            data.message.chat.id, PRODUCTS_BY_CATEGORY_MESSAGE, reply_markup=keyboard
        )


@bot.callback_query_handler(func=lambda data: data.data.split("&")[0] == "menu_by_cat")
def menu_by_category(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
def brands_by_category(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    category_id = int(data.data.split("&")[1])
    page = int(data.data.split("&")[2]) if len(data.data.split("&")) == 3 else 1
    brands = api.get_brands(category_id=category_id)
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(
            brand.name, callback_data=f"brand&{brand.id}&1;{data.data}"
        )
        for brand in brands
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
            BRAND_SUBMENU_MESSAGE,
            data.message.chat.id,
            data.message.message_id,
            reply_markup=keyboard,
        )
    except telebot.apihelper.ApiTelegramException as exc:
        # logger.error('API TELEGRAM ERROR',exc)
        try:
            bot.delete_message(data.message.chat.id, data.message.message_id)
        except telebot.apihelper.ApiTelegramException:
            pass
        bot.send_message(
            data.message.chat.id, BRAND_SUBMENU_MESSAGE, reply_markup=keyboard
        )


# -------------------------------------------------------------------------------------


@bot.callback_query_handler(func=lambda data: data.data.startswith("product"))
def product_card(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split("*")
    product = api.get_products(id=int(direct_data.split("&")[1]))[0]
    if not product:
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
        text += PRODUCT_CARD_SIZE.format(size=product.volume)
    keyboard = tools.keyboard_for_product(
        chat_id=data.message.chat.id, product=product, from_data=from_data
    )
    photo = product.get_photo()
    try:
        bot.delete_message(data.message.chat.id, data.message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass
    bot.send_photo(
        data.message.chat.id, photo, text, "MarkdownV2", reply_markup=keyboard
    )


# -------------------------------------------------------------------------------------
@bot.message_handler(commands=["cart"])
def get_cart(msg: types.Message, edit=False):
    logger.info(f"{msg.chat.id} came")
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
                    number=index + 1,
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
        cart_text = "\n".join(cart_text)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(EDIT_CART_BUTTON, callback_data="edit_cart")
        )
        keyboard.add(
            types.InlineKeyboardButton("Обновить корзину", callback_data="cart")
        )
        keyboard.add(
            types.InlineKeyboardButton(CHECKOUT_BUTTON, callback_data="checkout")
        )
        keyboard.add(types.InlineKeyboardButton("В меню", callback_data="back&menu"))
    if not edit:
        bot.send_message(
            msg.chat.id, cart_text, reply_markup=keyboard, parse_mode="MarkdownV2"
        )
    else:
        try:
            bot.edit_message_text(
                cart_text,
                msg.chat.id,
                msg.message_id,
                reply_markup=keyboard,
                parse_mode="MarkdownV2",
            )
        except telebot.apihelper.ApiTelegramException:
            try:
                bot.delete_message(msg.chat.id, msg.message_id)
            except telebot.apihelper.ApiTelegramException:
                pass
            bot.send_message(
                msg.chat.id, cart_text, parse_mode="MarkdownV2", reply_markup=keyboard
            )


@bot.callback_query_handler(lambda data: data.data == "cart")
def get_cart_by_callback(data):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    bot.answer_callback_query(data.id, "Корзина")
    get_cart(data.message, True)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "edit_cart")
def edit_cart(data: types.CallbackQuery, answer=True):
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
                number=index + 1,
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
    cart_text = "\n".join(cart_text)
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
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
    direct_data, from_data = data.data.split("*")
    product = direct_data.split("&")[1]
    if api.add_to_cart(product_id=product, chat_id=data.message.chat.id):
        product = api.get_products(id=int(product))[0]
        bot.answer_callback_query(
            data.id, ADD_TO_CART_BUTTON_ANSWER.format(product_name=product.name)
        )
        keyboard = tools.keyboard_for_product(data.message.chat.id, product, from_data)
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
    logger.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split("*")
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
        keyboard = tools.keyboard_for_product(
            data.message.chat.id, cart_item, from_data
        )
    else:
        bot.answer_callback_query(
            data.id, str(quantity) if quantity else DELETED_FROM_CART_BUTTON_ANSWER
        )
        keyboard = tools.keyboard_for_product(
            data.message.chat.id, cart_item.catalogue_item, from_data
        )
    try:
        bot.edit_message_reply_markup(
            data.message.chat.id, data.message.message_id, reply_markup=keyboard
        )
    except telebot.apihelper.ApiTelegramException as exc:
        logger.error("API TELEGRAM ERROR", exc)


# --------------------------------------------------------------------------------------


@bot.callback_query_handler(lambda data: data.data == "checkout")
def checkout(data: typing.Union[types.CallbackQuery, types.Message]):
    message = data.message if isinstance(data, types.CallbackQuery) else data
    edit = isinstance(data, types.CallbackQuery)
    logger.info(f"{message.chat.id} came")
    user = api.get_user(message.chat.id)
    if not user:
        if isinstance(data, types.CallbackQuery):
            bot.answer_callback_query(data.id, UNREGISTERED_BUTTON_ANSWER)
        return register(message)
    message_text = [ORDER_FIRST_MESSAGE]
    try:
        cart_list = api.get_cart(message.chat.id)
    except FileNotFoundError:
        message_text = EMPTY_CART_MESSAGE
        keyboard = quick_markup(
            {
                "Обновить корзину": {"callback_data": "cart"},
                "В меню": {"callback_data": "back&menu"},
            },
            1,
        )
    else:
        order = models.Order(
            message.chat.id, "", 0, user.address, models.Status.IN_CART, user.comment
        )
        for index, item in enumerate(cart_list):
            for char in BANNED_CHARS:
                item.catalogue_item.name = item.catalogue_item.name.replace(
                    char, "\\" + char
                )
                item.catalogue_item.volume = item.catalogue_item.volume.replace(
                    char, "\\" + char
                )
                brand_name = item.catalogue_item.get_brand_name().replace(
                    char, "\\" + char
                )
            order.cart += f"{index + 1}\\)*{brand_name}*  _{item.catalogue_item.name}_ {'__' + item.catalogue_item.volume + '__' if item.catalogue_item.volume != 'Безразмерный' else ''} {item.quantity}шт⋅{item.catalogue_item.price}₽ \\= *{item.sum}₽*\n "
            order.sum += item.sum

        if order.sum < MIN_ORDER_SUM:
            bot.send_message(
                data.message.chat.id,
                f"До минимальной суммы заказа не хватает {MIN_ORDER_SUM - order.sum}₽",
            )
            menu(data.message)
            return
        if order.sum < FREE_DELIVERY_FROM:
            order.sum += DELIVERY_COST
            order.free_delivery = False
            order.cart += f"\nДоставка: {DELIVERY_COST}₽"
        message_text.append(
            ITEM_CART_MESSAGE.format(
                number=index + 1,
                name=item.catalogue_item.name,
                size=item.catalogue_item.volume
                if item.catalogue_item.volume != "Безразмерный"
                else " ",
                price=item.catalogue_item.price,
                quantity=item.quantity,
                sum=item.sum,
            )
        )
        message_text = "\n".join(message_text)
        message_text += END_CART_MESSAGE.format(sum=order.sum)
        if order.sum < FREE_DELIVERY_FROM:
            message_text += (
                f"Ещё {order.sum - FREE_DELIVERY_FROM}₽ и доставка будет бесплатной"
            )
        else:
            message_text += "Поздравляем, вам доставка бесплатна!"
        order = api.create_order(order)
        for char in BANNED_CHARS:
            user.address.replace(char, "\\" + char)
            user.comment.replace(char, "\\" + char)
        user.address = user.address.replace("\n", "\n\t\t")
        message_text += f"\n\nНомер телефона: \\{user.phone_number}\n{ORDER_ADDRESS_MESSAGE}\n\t\t{user.address}\nКомментарий: {user.comment}"
        keyboard = types.InlineKeyboardMarkup(
            [
                [types.InlineKeyboardButton("Обновить", callback_data="checkout")],
                [
                    types.InlineKeyboardButton(
                        "Изменить номер телефона", callback_data="contacts&phone"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "Изменить адрес", callback_data="contacts&address"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "Изменить комментарий", callback_data="contacts&comment"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "Оплатить картой", callback_data=f"pay&{order.id}&card"
                    )
                ],
                [
                    types.InlineKeyboardButton(
                        "Оплатить наличными", callback_data=f"pay&{order.id}&cash"
                    )
                ],
                [types.InlineKeyboardButton("Назад", callback_data="back&cart")],
            ]
        )
    if edit:
        bot.edit_message_text(
            message_text,
            message.chat.id,
            message.message_id,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )
    else:
        bot.send_message(
            message.chat.id,
            message_text,
            reply_markup=keyboard,
            parse_mode="MarkdownV2",
        )


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "contacts")
def edit_user(data: types.CallbackQuery):
    action = data.data.split("&")[1]
    match action:
        case "phone":
            begin_phone_number(data.message, False, checkout)
        case "address":
            begin_address(data.message, False, checkout)
        case "comment":
            begin_comment(data.message, checkout)


def register(message: types.Message):
    try:
        bot.edit_message_text(UNREGISTERED_MESSAGE, message.chat.id, message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass
    begin_phone_number(message, True)


def begin_phone_number(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.add(types.KeyboardButton(REGISTRATION_PHONE_BUTTON, request_contact=True))
    bot.send_message(msg.chat.id, REGISTRATION_PHONE_MESSAGE, reply_markup=keyboard)
    bot.register_next_step_handler_by_chat_id(
        msg.chat.id,
        lambda message: phone_number_enter(message, registration, on_complete),
    )


def phone_number_enter(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[
        [
            types.Message,
        ],
        typing.Any,
    ] = None,
):
    logger.info(f"{msg.chat.id} came")
    try:
        number = msg.text or msg.contact.phone_number
        user = api.get_user(msg.chat.id) or models.User(
            chat_id=msg.chat.id, phone_number=number, address="", comment=""
        )
        user.phone_number = number
    except ValueError as exc:
        bot.reply_to(msg, text=str(exc) + "\nПопробуйте ещё раз")
        bot.register_next_step_handler(
            msg, lambda message: phone_number_enter(message, registration, on_complete)
        )
    else:
        assert api.create_user(user) == user
        if registration:
            begin_address(msg, True)
        else:
            on_complete(msg)


def begin_address(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    user = api.get_user(msg.chat.id)
    user.address = ""
    assert api.create_user(user) == user
    bot.send_message(
        msg.chat.id,
        REGISTRATION_STREET_MESSAGE,
        reply_markup=types.ReplyKeyboardRemove(),
    )
    bot.register_next_step_handler(
        msg, lambda message: street_enter(message, registration, on_complete)
    )


def street_enter(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    user.address += f"Улица: {msg.text}"
    assert api.create_user(user) == user
    bot.send_message(msg.chat.id, REGISTRATION_HOUSE_MESSAGE)
    bot.register_next_step_handler(
        msg, lambda message: house_enter(message, registration, on_complete)
    )


def house_enter(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    user.address += f"\nДом: {msg.text}"
    assert api.create_user(user) == user
    bot.send_message(msg.chat.id, REGISTRATION_ENTRANCE_MESSAGE)
    bot.register_next_step_handler(
        msg, lambda message: entrance_enter(message, registration, on_complete)
    )


def entrance_enter(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    user.address += f"\nПодъезд: {msg.text}"
    assert api.create_user(user) == user
    bot.send_message(msg.chat.id, REGISTRATION_FLOOR_MESSAGE)
    bot.register_next_step_handler(
        msg, lambda message: floor_enter(message, registration, on_complete)
    )


def floor_enter(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    user.address += f"\nЭтаж: {msg.text}"
    assert api.create_user(user) == user
    bot.send_message(msg.chat.id, REGISTRATION_APARTMENT_MESSAGE)
    bot.register_next_step_handler(
        msg, lambda message: apartment_enter(message, registration, on_complete)
    )


def apartment_enter(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    user.address += f"\nКвартира: {msg.text}"
    assert api.create_user(user) == user
    if registration:
        begin_comment(msg, on_complete=checkout)
    else:
        on_complete(msg)


def begin_comment(
    msg: types.Message, on_complete: typing.Callable[[types.Message], typing.Any] = None
):
    logger.info(f"{msg.chat.id} came")
    bot.send_message(msg.chat.id, REGISTRATION_COMMENT_MESSAGE)
    bot.register_next_step_handler(
        msg, lambda message: comment_enter(message, on_complete)
    )


def comment_enter(
    msg: types.Message, on_complete: typing.Callable[[types.Message], typing.Any] = None
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    user.comment = msg.text
    assert api.create_user(user) == user
    on_complete(msg)


# --------------------------------------------------------------------------------------


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "pay")
def pay(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    order_id = int(data.data.split("&")[1])
    method = data.data.split("&")[2]
    order = api.get_order(order_id)
    if method == "cash":
        order.status = models.Status.CASH
        tools.order_paid(
            order.id, chat_id=data.message.chat.id, notify=NOTIFICATION_CHATS
        )
        bot.answer_callback_query(data.id, ORDER_COMPLETE_BUTTON_ANSWER)
        bot.edit_message_text(
            ORDER_COMPLETE_MESSAGE, data.message.chat.id, data.message.message_id
        )

    menu(data.message)


@bot.callback_query_handler(lambda x: True)
def default_answer(data: types.CallbackQuery):
    logger.info(f"default callback query answer to {data.data}")
    if data.data.isdigit():
        bot.answer_callback_query(data.id, api.get_products(id=int(data.data))[0].name)
    bot.answer_callback_query(data.id, data.data)


if __name__ == "__main__":
    print(f"Running bot name {bot.get_me().username}")
    bot.polling()
