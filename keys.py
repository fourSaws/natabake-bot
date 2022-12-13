START_MESSAGE = (
    "Привет, Это Чат-бот НАТАБАКЕ! Для начала подтверди, что тебе уже есть 18"
)
START_BUTTON = "Мне уже есть 18"
START_ANSWER_SUCCESS = "Круто, погнали выбирать"
START_ANSWER_FAIL = "Жаль, тогда приходи попозже"

MENU_MESSAGE = (
    "Витрина продаж. Здесь можно выбрать электронные сигареты, кальяны и комплектующие"
)
TO_CATALOGUE_BUTTON = "Начать заказ"


MENU_BY_CATEGORY_BUTTON = "Категории"
MENU_BY_BRAND_BUTTON = "Бренды"

BRAND_SUBMENU_BUTTON_ANSWER = "Бренды"
BRAND_SUBMENU_MESSAGE = "Выберите бренд"

PRODUCTS_BY_BRAND_BUTTON_ANSWER = "Товары"
PRODUCTS_BY_BRAND_MESSAGE = "Выберите товар"

CATEGORY_SUBMENU_BUTTON_ANSWER = "Категории"
CATEGORY_SUBMENU_MESSAGE = "Выберите категорию"

PRODUCTS_BY_CATEGORY_BUTTON_ANSWER = "Товары"
PRODUCTS_BY_CATEGORY_MESSAGE = "Выберите товар"

# С МАРКДАУНОМ
PRODUCT_CARD = """
*Бренд:* {brand}
*Вкус:* {name}
*Цена:* {price} ₽
"""
PRODUCT_CARD_SIZE = "*Информация:* {size}"  # ОПЦИОНАЛЬНОЕ
# КОНЕЦ С МАРКДАУНОМ
ANOTHER_SIZE_BUTTON = "Ещё есть на {size}"


CHECKOUT_BUTTON = "Перейти к оформлению заказа"
EDIT_CART_BUTTON = "Редактировать корзину"
EDIT_CART_BUTTON_ANSWER = "Выберите товар, который хотите отредактировать"
CHANGE_QUANTITY_BUTTON_ANSWER = "В корзине {quantity}шт"
# С МАРКДАУНОМ
EMPTY_CART_MESSAGE = "Корзина пуста"
FIRST_CART_MESSAGE = "В корзине:"
ITEM_CART_MESSAGE = "{number}\\) _{name}_ __{size}__ {quantity}шт⋅{price}₽ \\= *{sum}₽*"
END_CART_MESSAGE = "Итого: {sum}"
# КОНЕЦ С МАРКДАУНОМ
ADD_TO_CART_BUTTON = "В корзину"

ADD_TO_CART_BUTTON_ANSWER = "{product_name} в корзине"
DELETED_FROM_CART_BUTTON_ANSWER = "Удалено из корзины"

ORDER_PAY_WITH_CARD="Для оплаты перейдите по ссылке"

ORDER_COMPLETE_BUTTON_ANSWER = "Заказ отправлен"
ORDER_COMPLETE_MESSAGE = "Спасибо за заказ, мы свяжемся с вами для подтверждения"

UNREGISTERED_MESSAGE = "Вы не зарегистрированы"
UNREGISTERED_BUTTON_ANSWER = "Необходимо пройти регистрацию"
REGISTRATION_COMMENT_MESSAGE = "Комментарий (код подъезда, например)"
REGISTRATION_APARTMENT_MESSAGE = "Введите квартиру"
REGISTRATION_FLOOR_MESSAGE = "Введите этаж"
REGISTRATION_ENTRANCE_MESSAGE = "Введите подъезд"
REGISTRATION_HOUSE_MESSAGE = "Введите дом"
REGISTRATION_STREET_MESSAGE = "Введите улицу"
REGISTRATION_PHONE_MESSAGE = "Введите номер телефона"
REGISTRATION_PHONE_BUTTON = "Поделиться номером телефона"

ORDER_FIRST_MESSAGE = "Заказ:"
ORDER_ADDRESS_MESSAGE = "Адрес:"

"""
ОШИБКИ
"""
PRODUCT_NOT_FOUND_MESSAGE = "Товар не найден"
NO_PRODUCT_IN_CART_ON_EDIT_BUTTON_ANSWER = "Товара в корзине нет"
ADD_TO_CART_FAIL_BUTTON_ANSWER = "Произошла ошибка"
