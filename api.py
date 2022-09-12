from typing import BinaryIO
from urllib.request import urlopen

import requests

from io import BytesIO
from models import CartItem, Brand, Category, Product


def get_cart(chat_id) -> list[CartItem]:
    response = requests.get('http://127.0.0.1:8000/api/getCart', params={'chat_id': chat_id})
    if response.status_code == 404:
        return []
    cart = []
    for i in response.json():
        cart.append(CartItem(cart_id=int(i['id']),
                             sum=int(i['sum']),
                             quantity=int(i['quantity']),
                             catalogue_item=get_products(id=i['product_id'])[0]))


def get_brands() -> list[Brand]:
    response = requests.get('http://127.0.0.1:8000/api/getBrands')
    return sorted([Brand(brand['id'], brand['name']) for brand in response.json()], key=lambda
        brand: brand.name)


def get_categories() -> list[Category]:
    response = requests.get('http://127.0.0.1:8000/api/getCategory')
    return sorted([Category(category['id'], category['name']) for category in response.json()],
                  key=lambda category: category.name)


def get_products(id: int = None, name: str = None, category_id: int = None, brand_id: int = None) -> list[Product]:
    payload = {}
    if id:
        payload['id'] = id
    if name:
        payload['name'] = name
    if category_id:
        payload['category'] = category_id
    if brand_id:
        payload['brand'] = brand_id
    response = requests.get('http://127.0.0.1:8000/api/getProducts', params=payload)
    if not response.json():
        raise FileNotFoundError(f"No file objects found for given params {payload=}")
    else:
        response = response.json()
    products = [Product(product['id'], product['volume'], product['category_id'], product['name'], product['price'],
                        product.get('photo_url'), product.get('brand') or product.get('brand_id')) for product in
                response]
    return products


def get_photo(url: str) -> BinaryIO:
    return urlopen('http://127.0.0.1:8000/media/'+url).read()
