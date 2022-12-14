from typing import BinaryIO
from urllib.request import urlopen
from random import randint
import requests
import logging
from models import *
from models import User

users = {}
orders = {}

server_url = "http://127.0.0.1:8000"
logger = logging.getLogger(__name__)

def log_event(func):
    def wrapper(*args, **kwargs):
        logger.info(f"AGRS: {args}",stacklevel=2)
        result = func(*args, **kwargs)
        if func.__name__!='get_photo':
            logger.info(f"RESPONSE:{result if type(result) is not list or type(result) is not BinaryIO else f'list({len(result)} items)'}",stacklevel=2)
        return result
    return wrapper

@log_event
def get_cart(chat_id) -> list[CartItem]:
    response = requests.get(server_url + "/api/getCart", params={"chat_id": chat_id})
    if response.status_code == 404:
        raise FileNotFoundError("Cart is empty")
    cart = []
    print(response.url)
    for i in response.json():
        cart.append(
            CartItem(
                cart_id=int(i["id"]),
                quantity=int(i["quantity"]),
                catalogue_item=get_products(id=i["product_id"])[0],
            )
        )
    logger.info(f'{cart=}')
    return cart

@log_event
def get_brands(category_id: int = None) -> list[Brand]:
    response = requests.get(server_url + "/api/getBrands")
    if response.status_code == 200:
        if not category_id:
            return sorted(
                [Brand(brand["id"], brand["name"]) for brand in response.json()],
                key=lambda brand: brand.name,
            )
        else:
            return sorted(
                [
                    Brand(brand["id"], brand["name"])
                    for brand in response.json()
                    if get_products(category_id=category_id, brand_id=brand["id"])
                ],
                key=lambda brand: brand.name,
            )
    elif response.status_code == 404:
        return []
    else:
        logging.error(f"getBrands returned code {response.status_code}")

@log_event
def get_categories() -> list[Category]:
    response = requests.get(server_url + "/api/getCategory")
    return sorted(
        [Category(category["id"], category["name"]) for category in response.json()],
        key=lambda category: category.name,
    )

@log_event
def get_products(
    id: int = None, name: str = None, category_id: int = None, brand_id: int = None
) -> list[Product]:
    payload = {}
    if id:
        payload["id"] = id
    if name:
        payload["name"] = name
    if category_id:
        payload["category"] = category_id
    if brand_id:
        payload["brand"] = brand_id
    response = requests.get(server_url + "/api/getProducts", params=payload)
    if not response.json():
        return []
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

@log_event
def get_photo(url: str) -> BinaryIO:
    return urlopen(server_url + "/media/" + url).read()

@log_event
def add_to_cart(chat_id: int, product_id: int) -> bool:
    response = requests.get(
        server_url + "/api/addToCart",
        params={"id": product_id, "chat_id": chat_id},
    )
    if response.status_code != 200:
        logging.error(
            f"addToCart returned code {response.status_code}. Url was {response.url}"
        )
        return False
    return True

@log_event
def edit_cart(cart_id: int, chat_id: int, quantity: int) -> CartItem:
    response = requests.get(
        server_url + "/api/editCart",
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

@log_event
def create_user(user: User) -> User:
    response = requests.get(
        server_url + "/api/createUser",
        params={
            "chat_id": user.chat_id,
            "phone_number": user.phone_number,
            "address": user.address,
            "comment": user.comment,
        },
    )
    json = response.json()[0]
    return User(
        chat_id=int(json["chat_id"]),
        phone_number=json["phone_number"],
        address=json["address"],
        comment=json["comment"],
    )

@log_event
def get_user(chat_id: int) -> User | bool:
    response = requests.get(
        server_url + "/api/getUser",
        params={"chat_id": chat_id},
    )
    json = response.json()
    if json:
        json = json[0]
        return User(
            chat_id=int(json["chat_id"]),
            phone_number=json["phone_number"],
            address=json["address"],
            comment=json["comment"],
        )
    return False

@log_event
def create_order(order: Order) -> Order:
    data=requests.get(server_url+'/api/createOrder',params={
        "chat_id":order.client,
        "cart":order.cart,
        "free_delivery":order.free_delivery,
        "sum":order.sum,
        "address":order.address,
        "status":order.status.name,
        "comment":order.comment,
    })
    print(data.url)
    print(data.json())
    return Order.from_json(data.json()[0])

@log_event
def change_status(order_id: int, status: Status) -> bool:
    a=requests.get(server_url+'/api/changeStatus',params={
        "order_id":order_id,
        "new_status":status.name
    })
    return a.status_code==200

@log_event
def get_order(order_id: int) -> Order:
    response = requests.get(
        server_url + "/api/getOrder",
        params={
            "order_id":order_id
        },
    )
    if response.status_code==200:
        data=response.json()[0]
        res=Order.from_json(data)
        return res
@log_event
def get_orders(chat_id: int) -> list[Order]:
    response = requests.get(
        server_url + "/api/getOrders",
        params={
            "chat_id": chat_id
        },
    )
    if response.status_code == 200:
        data = response.json()
        return [Order.from_json(i) for i in data]

@log_event
def clear_cart(chat_id: int):
    requests.get(server_url + "/api/clearCart", params={"chat_id": chat_id})
