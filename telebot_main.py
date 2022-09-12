from telebot import TeleBot, types, formatting
import secure
import api
import logging
from inspect import currentframe
import tools
from telebot.util import quick_markup

logging.basicConfig(level=logging.INFO)

bot = TeleBot(token=secure.teletoken)


@bot.message_handler(commands=['start'])
def start(msg: types.Message):
    logging.info(f'{msg.chat.id} got into {currentframe().f_code.co_name} function')

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Мне уже есть 18'))
    bot.send_message(msg.chat.id, 'Привет, давай знакомиться! Для начала подтверди, что тебе уже есть 18',
                     reply_markup=keyboard)
    bot.register_next_step_handler(msg, prove_18)


def prove_18(msg: types.Message):
    logging.info(f'{msg.chat.id} got into {currentframe().f_code.co_name} function')

    if msg.text == 'Мне уже есть 18':
        bot.send_message(msg.chat.id, 'Круто, погнали выбирать', reply_markup=types.ReplyKeyboardRemove())
        menu(msg)
    else:
        bot.send_message(msg.chat.id, 'Жаль, тогда приходи попозже')
        bot.register_next_step_handler(msg, start)


@bot.message_handler(commands=['menu'])
def menu(msg: types.Message, edit=False):
    logging.info(f'{msg.chat.id} got into {currentframe().f_code.co_name} function')
    cart = api.get_cart(msg.chat.id)
    structure = []
    structure.append([types.InlineKeyboardButton('КАТАЛОГ', callback_data='попа')])
    structure.append([types.InlineKeyboardButton("По категориям", callback_data='menu_by_cat&1'),
                      types.InlineKeyboardButton("По брендам", callback_data='menu_by_brand&1')])
    structure.append([types.InlineKeyboardButton(f"Корзина ({len(cart)}) {sum(tuple(item.sum for item in cart))}₽",
                                                 callback_data='cart')])
    keyboard = types.InlineKeyboardMarkup(structure)
    if edit:
        bot.edit_message_text('Это меню', msg.chat.id, msg.message_id, reply_markup=keyboard)
    else:
        bot.send_message(msg.chat.id, 'Это меню', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.split('&')[0] == 'back')
def back(data: types.CallbackQuery):
    logging.info(f'{data.message.chat.id} got into {currentframe().f_code.co_name} function')
    match data.data.split('&')[1]:
        case 'menu':
            menu(data.message, True)
        case 'menu_by_brand':
            data.data = '&'.join(data.data.split('&')[1:])
            menu_by_brand(data)
        case 'menu_by_cat':
            data.data = '&'.join(data.data.split('&')[1:])
            menu_by_category(data)
        case 'brand':
            data.data = '&'.join(data.data.split('&')[1:])
            products_by_brand(data)
        case 'category':
            data.data = '&'.join(data.data.split('&')[1:])
            products_by_category(data)

        case _:
            raise ValueError(f'Unresolved for {data.data.split("&")[1]}')


@bot.callback_query_handler(func=lambda data: data.data.startswith('menu_by_brand'))
def menu_by_brand(data: types.CallbackQuery):
    logging.info(f'{data.message.chat.id} got into {currentframe().f_code.co_name} function')
    brands = tuple(
        types.InlineKeyboardButton(brand.name, callback_data=f'brand&{brand.id}&1') for brand in api.get_brands())
    keyboard = tools.get_inline_keyboard_page(brands, int(data.data.split('&')[1]), 2, 'menu_by_brand')
    bot.answer_callback_query(data.id, "Бренды")
    bot.edit_message_text('Выберите бренд', data.message.chat.id, data.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.startswith('brand'))
def products_by_brand(data: types.CallbackQuery):
    logging.info(f'{data.message.chat.id} got into {currentframe().f_code.co_name} function')
    products = api.get_products(brand_id=int(data.data.split('&')[1]))
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(product.name, callback_data=f'product&{product.id};{data.data}') for product in
        products)
    print(*keyboard_buttons)
    keyboard = tools.get_inline_keyboard_page(keyboard_buttons, int(data.data.split('&')[1]), 2, 'brand&',
                                              back_to='menu_by_brand&1')
    bot.answer_callback_query(data.id, 'Товары')
    bot.edit_message_text('Выберите товар', data.message.chat.id, data.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.split('&')[0] == 'menu_by_cat')
def menu_by_category(data: types.CallbackQuery):
    logging.info(f'{data.message.chat.id} got into {currentframe().f_code.co_name} function')
    logging.info(f'{data.data=}')
    categories = tuple(
        types.InlineKeyboardButton(category.name, callback_data=f'category&{category.id}') for category in
        api.get_categories())
    keyboard = tools.get_inline_keyboard_page(categories, int(data.data.split('&')[1]), 2, 'menu_by_cat&')
    bot.answer_callback_query(data.id, 'Категории')
    bot.edit_message_text('Выберите категорию', data.message.chat.id, data.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.startswith('category'))
def products_by_category(data: types.CallbackQuery):
    logging.info(f'{data.message.chat.id} got into {currentframe().f_code.co_name} function')
    products = api.get_products(category_id=data.data.split('&')[1])
    keyboard_buttons = tuple(
        types.InlineKeyboardButton(product.name, callback_data=f'product&{product.id};{data.data}') for product in
        products)
    keyboard = tools.get_inline_keyboard_page(keyboard_buttons, int(data.data.split('&')[1]), 2,
                                              ''.join(data.data.split('&')[:2]), back_to=data.data)
    bot.answer_callback_query(data.id, 'Товары')
    bot.edit_message_text('Выберите товар', data.message.chat.id, data.message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda data: data.data.startswith('product'))
def product_card(data: types.CallbackQuery):
    direct_data, from_data = data.data.split(';')
    try:
        product = api.get_products(id=int(direct_data.split('&')[1]))[0]
    except FileNotFoundError:
        bot.edit_message_text("Товар не найден", data.message.chat.id, data.message.message_id,
                              reply_markup=quick_markup({'Назад': {'callback_query': from_data}}))
        return
    text = formatting.format_text(
        formatting.mbold('Производитель: '), product.get_brand_name(), '\n',
        formatting.mbold('Наименование: '), product.name, '\n',
        formatting.mbold('Размер: '), product.volume, '\n',
        formatting.mbold("Цена: "), f'{product.price} ₽',
        separator='',
    )
    other = api.get_products(name=product.name)
    keyboard = types.InlineKeyboardMarkup()
    if len(other) > 1:
        other.remove(product)
        for prod in other:
            keyboard.add(types.InlineKeyboardButton(prod.volume, callback_data=f'product&{prod.id};{from_data}'))
    keyboard.add('')  # TODO клавиатура, фото


@bot.message_handler(commands=['cart'])
def get_cart(msg: types.Message):
    logging.info(f'{msg.chat.id} got into {currentframe().f_code.co_name} function')

    cart_list = api.get_cart(msg.chat.id)
    keyboard = types.InlineKeyboardMarkup()
    if not cart_list:
        keyboard.add(types.InlineKeyboardButton("Обновить корзину", callback_data='refresh_cart'))
        bot.send_message(msg.chat.id, 'Корзина пуста', reply_markup=keyboard)


@bot.callback_query_handler(lambda data: data.data == 'refresh_cart')
def refresh_cart(data: types.CallbackQuery):
    logging.info(f'{data.message.chat.id} got into {currentframe().f_code.co_name} function')

    bot.send_message(data.message.chat.id, f'{data.message.chat.id=} {data.chat_instance}')
    # cart_list = api.get_cart(msg.chat.id)
    # keyboard = types.InlineKeyboardMarkup()
    # if not cart_list:
    #     keyboard.add(types.InlineKeyboardButton("Обновить корзину", callback_data='refesh_cart'))
    #     bot.send_message(msg.chat.id, 'Корзина пуста')


@bot.callback_query_handler(lambda x: True)
def default_answer(data: types.CallbackQuery):
    logging.info(f'default callback query answer to {data.data}')
    bot.answer_callback_query(data.id)


if __name__ == '__main__':
    bot.polling(non_stop=True)
