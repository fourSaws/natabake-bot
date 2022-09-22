from telebot import TeleBot, types, apihelper

import secure
import api
import models
import logging
from inspect import currentframe
import tools
from telebot.util import quick_markup

logging.basicConfig(level=logging.INFO)

bot = TeleBot(token=secure.teletoken)


@bot.message_handler(commands=["start"])
def start(msg: types.Message):
    logging.info(f"{msg.chat.id} got into {currentframe().f_code.co_name} function")
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Мне уже есть 18"))
    bot.send_message(
        msg.chat.id,
        "Привет, давай знакомиться! Для начала подтверди, что тебе уже есть 18",
        reply_markup=keyboard,
    )
    bot.register_next_step_handler(msg, prove_18)


def prove_18(msg: types.Message):
    logging.info(f"{msg.chat.id} got into {currentframe().f_code.co_name} function")

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


@bot.message_handler(commands=["menu"])
def menu(msg: types.Message, edit=False):
    logging.info(f"{msg.chat.id} got into {currentframe().f_code.co_name} function")
    cart = api.get_cart(msg.chat.id)
    structure = [
        [
            types.InlineKeyboardButton(
                "КАТАЛОГ", callback_data="Выберите как показать каталог"
            )
        ],
        [
            types.InlineKeyboardButton("По категориям", callback_data="menu_by_cat&1"),
            types.InlineKeyboardButton("По брендам", callback_data="menu_by_brand&1"),
        ],
        [
            types.InlineKeyboardButton(
                f"Корзина ({len(cart)}) {sum(tuple(item.sum for item in cart))}₽",
                callback_data="cart",
            )
        ],
    ]
    keyboard = types.InlineKeyboardMarkup(structure)
    if edit:
        bot.edit_message_text(
            "Это меню", msg.chat.id, msg.message_id, reply_markup=keyboard
        )
    else:
        bot.send_message(msg.chat.id, "Это меню", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.split("&")[0] == "back")
def back(data: types.CallbackQuery):
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function with {data.data}"
    )
    match data.data.split("&")[1]:
        case "menu":
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

        case _:
            raise ValueError(f'Unresolved for {data.data.split("&")[1]}')


@bot.callback_query_handler(func=lambda data: data.data.startswith("menu_by_brand"))
def menu_by_brand(data: types.CallbackQuery):
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )
    brands = tuple(
        types.InlineKeyboardButton(brand.name, callback_data=f"brand&{brand.id}&1")
        for brand in api.get_brands()
    )
    keyboard = tools.get_inline_keyboard_page(
        brands, int(data.data.split("&")[1]), 2, "menu_by_brand"
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
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )
    products = api.get_products(brand_id=int(data.data.split("&")[1]))
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(
            product.name, callback_data=f"product&{product.id};{data.data}"
        )
        for product in products
    )
    print(*keyboard_buttons)
    keyboard = tools.get_inline_keyboard_page(
        keyboard_buttons,
        int(data.data.split("&")[1]),
        2,
        "brand&",
        back_to="menu_by_brand&1",
    )
    bot.answer_callback_query(data.id, "Товары")
    bot.edit_message_text(
        "Выберите товар",
        data.message.chat.id,
        data.message.message_id,
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda data: data.data.split("&")[0] == "menu_by_cat")
def menu_by_category(data: types.CallbackQuery):
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )
    logging.info(f"{data.data=}")
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
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )
    products = api.get_products(id=int(data.data.split("&")[1]))
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(
            product.name, callback_data=f"product&{product.id};{data.data}"
        )
        for product in products
    )
    keyboard = tools.get_inline_keyboard_page(
        keyboard_buttons,
        int(data.data.split("&")[1]),
        2,
        "".join(data.data.split("&")[:2]),
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
    except telebot.apihelper.ApiTelegramException:
        bot.delete_message(data.message.chat.id, data.message.message_id)
        bot.send_message(data.message.chat.id, "Выберите товар", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.startswith("product"))
def product_card(data: types.CallbackQuery):
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )
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
                        prod.volume, callback_data=f"product&{prod.id};{from_data}"
                    )
                ]
            )
    keyboard.append(cart_buttons_for_product(product, data.message.chat.id))
    keyboard.append([types.InlineKeyboardButton("Назад", callback_data=from_data)])
    photo = product.get_photo()
    try:
        bot.delete_message(data.message.chat.id, data.message.message_id)
    except telebot.apihelper.ApiTelegramException:
        pass
    bot.send_photo(
        data.message.chat.id,
        photo,
        text,
        "Markdown",
        reply_markup=types.InlineKeyboardMarkup(keyboard),
    )


@bot.callback_query_handler(lambda data: data.data.split("&")[0] == "add_to_cart")
def add_to_cart(data: types.CallbackQuery):
    product = api.get_products(int(data.data.split("&")[1]))[0]
    if api.add_to_cart(data.message.chat.id, product):
        bot.answer_callback_query(data.id, f"{product.name} в корзине")
        cart_buttons_for_product(product, data.message.chat.id)
    else:
        bot.answer_callback_query(data.id, f"Ошибка сервера")


def get_cart_text(cart_list: list[models.CartItem]) -> str:
    text = f"В корзине ({len(cart_list)}):\n"
    sum_ = 0
    for i, item in enumerate(cart_list):
        text += f"{i}) {item.catalogue_item.name} _{item.catalogue_item.volume}_ {item.catalogue_item.price}₽ * {item.quantity} = {item.sum}"
        sum_ += item.sum
    text += f"Итого: {sum_}"
    return text


@bot.callback_query_handler(lambda data: data.data == "cart")
def get_cart(data: types.CallbackQuery):
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )

    cart_list = api.get_cart(data.message.chat.id)
    cart_text = get_cart_text(cart_list)
    cart_keyboard = types.InlineKeyboardMarkup(
        [
            types.InlineKeyboardButton("Оформить заказ", callback_data="checkout"),
            types.InlineKeyboardButton(
                "Редактировать корзину", callback_data="edit_cart"
            ),
            types.InlineKeyboardButton("Очистить корзину", callback_data="clear_cart"),
            types.InlineKeyboardButton(
                "Обновить корзину", callback_data="refresh_cart"
            ),
            types.InlineKeyboardButton("В меню", callback_data="back&menu"),
        ]
    )
    if not cart_list:
        cart_text = ""
        cart_keyboard = types.InlineKeyboardMarkup(
            [
                types.InlineKeyboardButton(
                    "Обновить корзину", callback_data="refresh_cart"
                ),
                types.InlineKeyboardButton("В меню", callback_data="back&menu"),
            ]
        )
    bot.answer_callback_query(data.id, "Корзина")
    print(data.message.content_type)


@bot.callback_query_handler(lambda data: data.data == "refresh_cart")
def refresh_cart(data: types.CallbackQuery):
    logging.info(
        f"{data.message.chat.id} got into {currentframe().f_code.co_name} function"
    )

    bot.send_message(
        data.message.chat.id, f"{data.message.chat.id=} {data.chat_instance}"
    )
    # cart_list = api.get_cart(msg.chat.id)
    # keyboard = types.InlineKeyboardMarkup()
    # if not cart_list:
    #     keyboard.add(types.InlineKeyboardButton("Обновить корзину", callback_data='refesh_cart'))
    #     bot.send_message(msg.chat.id, 'Корзина пуста')


@bot.callback_query_handler(lambda x: True)
def default_answer(data: types.CallbackQuery):
    logging.info(f"default callback query answer to {data.data}")
    bot.answer_callback_query(data.id, data.data)


def cart_buttons_for_product(
    product: models.Product, chat_id: int
) -> list[types.InlineKeyboardButton]:
    cart = api.get_cart(chat_id)
    in_cart = False
    buttons = []
    for prod_in_cart in cart:
        if prod_in_cart == product:
            in_cart = True
            if prod_in_cart.quantity > 1:
                buttons.append(
                    types.InlineKeyboardButton(
                        "-",
                        callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.quantity - 1}",
                    )
                )
            buttons.append(
                types.InlineKeyboardButton(
                    str(prod_in_cart.quantity), callback_data=f"cart"
                )
            )
            buttons.append(
                types.InlineKeyboardButton(
                    "+",
                    callback_data=f"edit&{prod_in_cart.cart_id}&{prod_in_cart.quantity + 1}",
                )
            )
            break
    if not in_cart:
        buttons = [
            types.InlineKeyboardButton(
                "В корзину", callback_data=f"add_to_cart&{product.id}"
            )
        ]
    return buttons


if __name__ == "__main__":
    bot.polling(non_stop=True)
