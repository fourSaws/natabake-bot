import logging
import typing
from datetime import datetime
import telebot.apihelper
from telebot import TeleBot, types
from telebot.util import quick_markup

import api
import models
from os import environ
import tools

logging.basicConfig(
    filename=f"bot-from-{datetime.now().date()}.log",
    filemode="w",
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
FREE_DELIVERY_FROM = 1200
DELIVERY_COST = 150
bot = TeleBot(token=environ.get("teletoken"))
logger = logging.getLogger(__name__)


@bot.message_handler(commands=["start"])
def start(msg: types.Message):
    logger.info(f"{msg.chat.id} came")

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Мне уже есть 18"))
    bot.send_message(
        msg.chat.id,
        "Привет, давай знакомиться! Для начала подтверди, что тебе уже есть 18",
        reply_markup=keyboard,
    )
    bot.register_next_step_handler(msg, prove_18)


def prove_18(msg: types.Message):
    logger.info(f"{msg.chat.id} came")

    if msg.text == "Мне уже есть 18":
        bot.send_message(
            msg.chat.id,
            "Круто, погнали выбирать",
            reply_markup=types.ReplyKeyboardRemove(),
        )
        menu(msg)
    else:
        bot.send_message(msg.chat.id, "Жаль, тогда приходи попозже")
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
        [
            types.InlineKeyboardButton("По категориям", callback_data="menu_by_cat&1"),
            types.InlineKeyboardButton("По брендам", callback_data="menu_by_brand&1"),
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
            "Это меню", msg.chat.id, msg.message_id, reply_markup=keyboard
        )
    else:
        bot.send_message(msg.chat.id, "Это меню", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.split("&")[0] == "back")
def back(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
    logger.info(f"{data.message.chat.id} came with {data.data}")
    brands = tuple(
        types.InlineKeyboardButton(brand.name, callback_data=f"brand&{brand.id}&1")
        for brand in api.get_brands()
    )
    keyboard = tools.get_inline_keyboard_page(
        brands, int(data.data.split("&")[1]), 2, "menu_by_brand&"
    )
    bot.answer_callback_query(data.id, "Бренды")
    bot.edit_message_text(
        "Выберите бренд",
        data.message.chat.id,
        data.message.message_id,
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda data: data.data.startswith("brand"))
def products_by_brand(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
    bot.answer_callback_query(data.id, "Товары")
    try:
        bot.edit_message_text(
            "Выберите товар",
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
        bot.send_message(data.message.chat.id, "Выберите товар", reply_markup=keyboard)


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
    bot.answer_callback_query(data.id, "Категории")
    bot.edit_message_text(
        "Выберите категорию",
        data.message.chat.id,
        data.message.message_id,
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda data: data.data.startswith("category"))
def products_by_category(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    category_id = data.data.split("&")[1]
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
    bot.answer_callback_query(data.id, "Товары")
    try:
        bot.edit_message_text(
            "Выберите товар",
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
        bot.send_message(data.message.chat.id, "Выберите товар", reply_markup=keyboard)


# -------------------------------------------------------------------------------------


@bot.callback_query_handler(func=lambda data: data.data.startswith("product"))
def product_card(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split(";")
    try:
        product = api.get_products(id=int(direct_data.split("&")[1]))[0]
    except FileNotFoundError:
        bot.edit_message_text(
            "Товар не найден",
            data.message.chat.id,
            data.message.message_id,
            reply_markup=quick_markup({"Назад": {"callback_query": from_data}}),
        )
        return
    text = "*Производитель:* "
    text += product.get_brand_name() + "\n"
    text += "*Наименование:* " + product.name + "\n"
    text += (("*Размер:* " + product.volume) if product.volume else "") + "\n"
    text += "*Цена:* " + f"{product.price} ₽"
    keyboard = tools.keyboard_for_product(
        chat_id=data.message.chat.id, product=product, from_data=from_data
    )
    photo = product.get_photo()
    bot.delete_message(data.message.chat.id, data.message.message_id)
    bot.send_photo(data.message.chat.id, photo, text, "Markdown", reply_markup=keyboard)


# -------------------------------------------------------------------------------------
@bot.message_handler(commands=["cart"])
def get_cart(msg: types.Message, edit=False):
    logger.info(f"{msg.chat.id} came")
    cart_text = "В корзине: \n"
    try:
        cart_list = api.get_cart(msg.chat.id)
    except FileNotFoundError:
        cart_text = "Корзина пуста"
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
            cart_text += f"{index + 1}\\) _{item.catalogue_item.name}_ {'__' + item.catalogue_item.volume + '__' if item.catalogue_item.volume != 'Безразмерный' else ''} {item.quantity}шт⋅{item.catalogue_item.price}₽ \\= *{item.sum}₽*\n"
            sum_ += item.sum
        cart_text += f"\n*Итого: {sum_}₽*"
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                "Редактировать корзину", callback_data="edit_cart"
            )
        )
        keyboard.add(
            types.InlineKeyboardButton("Обновить корзину", callback_data="cart")
        )
        keyboard.add(
            types.InlineKeyboardButton(
                "Перейти к оформлению заказа", callback_data="checkout"
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
    logger.info(f"{data.message.chat.id} came with {data.data}")
    bot.answer_callback_query(data.id, "Корзина")
    get_cart(data.message, True)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "edit_cart")
def edit_cart(data: types.CallbackQuery, answer=True):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    page = int(data.data.split("&")[1]) if len(data.data.split("&")) > 1 else 1
    cart_text = "В корзине: \n"
    try:
        cart_list = api.get_cart(data.message.chat.id)
    except FileNotFoundError:
        bot.edit_message_text(
            "Корзина пуста",
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
        cart_text += f"{index + 1}\\) _{item.catalogue_item.name}_ {'__' + item.catalogue_item.volume + '__' if item.catalogue_item.volume != 'Безразмерный' else ''} {item.quantity}шт⋅{item.catalogue_item.price}₽ \\= *{item.sum}₽*\n"
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
    cart_text += f"\n*Итого: {sum_}₽*"
    if answer:
        bot.answer_callback_query(
            data.id, "Выберите товар, который хотите отредактировать"
        )
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
    bot.answer_callback_query(data.id, str(quantity))
    edit_cart(data, False)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "remove")
def remove_from_cart(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    page = int(data.data.split("&")[2])
    try:
        api.edit_cart(int(data.data.split("&")[1]), data.message.chat.id, 0)
    except FileNotFoundError:
        bot.answer_callback_query(data.id, "Товара в корзине не было")
    else:
        bot.answer_callback_query(data.id, "Удалено из корзины")
    data.data = f"edit_cart&{page}"
    edit_cart(data)


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "add_to_cart")
def add_to_cart(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
    direct_data, from_data = data.data.split(";")
    product = direct_data.split("&")[1]
    if api.add_to_cart(product_id=product, chat_id=data.message.chat.id):
        product = api.get_products(id=int(product))[0]
        bot.answer_callback_query(data.id, f"{product.name} в корзине")
        keyboard = tools.keyboard_for_product(data.message.chat.id, product, from_data)
        # try:
        bot.edit_message_reply_markup(
            data.message.chat.id, data.message.message_id, reply_markup=keyboard
        )
        # except telebot.apihelper.ApiTelegramException:
        #     product_card(data)

    else:
        bot.answer_callback_query(data.id, "Произошла ошибка")


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "edit")
def edit_product_cart(data: types.CallbackQuery):
    logger.info(f"{data.message.chat.id} came with {data.data}")
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
        bot.answer_callback_query(data.id, "Товара в корзине нет")
        cart_item = api.get_products(id=catalogue_id)[0]
        keyboard = tools.keyboard_for_product(
            data.message.chat.id, cart_item, from_data
        )
    else:
        bot.answer_callback_query(
            data.id, str(quantity) if quantity else "Удалено из корзины"
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
    if user is None:
        if isinstance(data, types.CallbackQuery):
            bot.answer_callback_query(data.id, "Необходимо пройти регистрацию")
        return register(message)
    message_text = "Заказ: \n"
    try:
        cart_list = api.get_cart(message.chat.id)
    except FileNotFoundError:
        message_text = "Корзина пуста"
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
            order.cart += f"{index + 1}\\) _{item.catalogue_item.name}_ {'__' + item.catalogue_item.volume + '__' if item.catalogue_item.volume != 'Безразмерный' else ''} {item.quantity}шт⋅{item.catalogue_item.price}₽ \\= *{item.sum}₽*\n "
            order.sum += item.sum
        message_text += order.cart
        if order.sum < FREE_DELIVERY_FROM:
            order.sum += DELIVERY_COST
            order.free_delivery = False
            message_text += f"\nДоставка: {DELIVERY_COST}₽"
        message_text += f"\n*Итого: {order.sum}₽*"
        order = api.create_order(order)
        for char in BANNED_CHARS:
            user.address.replace(char, "\\" + char)
            user.comment.replace(char, "\\" + char)
        user.address = user.address.replace("\n", "\n\t\t")
        message_text += f"\n\nНомер телефона: \\{user.phone_number}\nАдрес:\n\t\t{user.address}\nКомментарий: {user.comment}"
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
        bot.edit_message_text(
            "Вы не зарегистрированы", message.chat.id, message.message_id
        )
    except telebot.apihelper.ApiTelegramException:
        pass
    begin_phone_number(message, True)


def begin_phone_number(
    msg: types.Message,
    registration: bool,
    on_complete: typing.Callable[[types.Message], typing.Any] = None,
):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.add(
        types.KeyboardButton("Поделиться номером телефона", request_contact=True)
    )
    bot.send_message(msg.chat.id, "Введите номер телефона", reply_markup=keyboard)
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
        msg.chat.id, "Введите улицу:", reply_markup=types.ReplyKeyboardRemove()
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
    bot.send_message(msg.chat.id, "Введите дом")
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
    bot.send_message(msg.chat.id, "Введите подъезд")
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
    bot.send_message(msg.chat.id, "Введите этаж")
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
    bot.send_message(msg.chat.id, "Введите квартиру")
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
    bot.send_message(msg.chat.id, "Комментарий: (код подъезда, например)")
    bot.register_next_step_handler(
        msg, lambda message: comment_enter(message, on_complete)
    )


def comment_enter(
    msg: types.Message, on_complete: typing.Callable[[types.Message], typing.Any] = None
):
    logger.info(f"{msg.chat.id} came")
    user = api.get_user(msg.chat.id)
    print(msg.text)
    user.comment = msg.text
    print(user)
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
        tools.order_paid(order.id)
        bot.answer_callback_query(data.id, "Заказ отправлен")
        bot.edit_message_text(
            "Спасибо за заказ", data.message.chat.id, data.message.message_id
        )


@bot.callback_query_handler(lambda x: True)
def default_answer(data: types.CallbackQuery):
    logger.info(f"default callback query answer to {data.data}")
    if data.data.isdigit():
        bot.answer_callback_query(data.id, api.get_products(id=int(data.data))[0].name)
    bot.answer_callback_query(data.id, data.data)


if __name__ == "__main__":
    bot.polling(non_stop=True)
