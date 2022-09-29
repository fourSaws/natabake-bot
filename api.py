from typing import BinaryIO
from urllib.request import urlopen
from random import randint
import requests

from models import *

users = {}
orders = {}


def get_cart(chat_id) -> list[CartItem]:
    response = requests.get("http://127.0.0.1:8000/api/getCart", params={"chat_id": chat_id})
    if response.status_code == 404:
        raise FileNotFoundError("Cart is empty")
    cart = []
    for i in response.json():
        cart.append(
            CartItem(
                cart_id=int(i["id"]),
                quantity=int(i["quantity"]),
                catalogue_item=get_products(id=i["product_id"])[0],
            )
        )
    return cart


def get_brands() -> list[Brand]:
    response = requests.get("http://127.0.0.1:8000/api/getBrands")
    if response.status_code == 200:
        return sorted(
            [Brand(brand["id"], brand["name"]) for brand in response.json()],
            key=lambda brand: brand.name,
        )
    elif response.status_code == 404:
        return []
    else:
        logging.error(f"getBrands returned code {response.status_code}")


def get_categories() -> list[Category]:
    response = requests.get("http://127.0.0.1:8000/api/getCategory")
    return sorted(
        [Category(category["id"], category["name"]) for category in response.json()],
        key=lambda category: category.name,
    )


def get_products(id: int = None, name: str = None, category_id: int = None, brand_id: int = None) -> list[Product]:
    payload = {}
    if id:
        payload["id"] = id
    if name:
        payload["name"] = name
    if category_id:
        payload["category"] = category_id
    if brand_id:
        payload["brand"] = brand_id
    response = requests.get("http://127.0.0.1:8000/api/getProducts", params=payload)
    if not response.json():
        raise FileNotFoundError(f"No file objects found for given params {payload=}")
    else:
        response = response.json()
    products = [
        Product(
            product["id"],
            product["volume"],
            product["category_id"],
            product["name"],
            product["price"],
            product.get("photo_url"),
            product.get("brand") or product.get("brand_id"),
        )
        for product in response
    ]
    return products


def get_photo(url: str) -> BinaryIO:
    return urlopen("http://127.0.0.1:8000/media/" + url).read()


def add_to_cart(chat_id: int, product_id: int) -> bool:
    response = requests.get(
        "http://127.0.0.1:8000/api/addToCart",
        params={"id": product_id, "chat_id": chat_id},
    )
    if response.status_code != 200:
        logging.error(f"addToCart returned code {response.status_code}")
        return False
    return True


def edit_cart(cart_id: int, chat_id: int, quantity: int) -> CartItem:
    response = requests.get(
        "http://127.0.0.1:8000/api/editCart",
        params={"product_id": cart_id, "chat_id": chat_id, "quantity": quantity},
    )
    if response.status_code != 200:
        logging.error(f"editCart returned code {response.status_code}")
        if response.status_code == 404:
            raise FileNotFoundError("Not found in cart")
        raise Exception(f"editCart returned code {response.status_code}")
    if not response.json():
        return []
    product = response.json()["product"]
    return CartItem(
        Product(
            product["id"],
            product["volume"],
            product["category"],
            product["name"],
            product["price"],
            product.get("photo_url"),
            product.get("brand"),
        ),
        response.json()["quantity"],
        cart_id,
    )


def create_user(user: User) -> User:
    global users
    users[user.chat_id] = user
    return users[user.chat_id]


def get_user(chat_id: int) -> User:
    global users
    return users.get(chat_id)


def create_order(order: Order) -> Order:
    global orders
    while (id_ := randint(0, 100)) in orders:
        pass
    order.id = id_
    orders[order.id] = order
    return orders[order.id]


def change_status(order_id: int, status: Status) -> Order:
    global orders
    order = orders[order_id]
    order.status = status
    orders[order_id] = order
    return orders[order_id]


def get_order(order_id: int) -> Order:
    global orders
    return orders[order_id]


def get_orders(chat_id: int) -> list[Order]:
    raise NotImplementedError
