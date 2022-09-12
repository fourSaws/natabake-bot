import logging

import requests

from models import CartItem, Product, Category, Brand


def get_cart(chat_id) -> list[CartItem]:
    return []


def get_brands() -> list[Brand]:
    response = requests.get('http://127.0.0.1:8000/api/getBrands')
    return sorted([Brand(brand['id'], brand['name']) for brand in response.json()], key=lambda
        brand: brand.name)


def get_categories() -> list[Category]:
    response = requests.get('http://127.0.0.1:8000/api/getCategory')
    return sorted([Category(category['id'], category['name']) for category in response.json()],
                  key=lambda category: category.name.replace("C", 'С'))


def get_products(id: int = None, name: str = None, category_id: int = None, brand_id: int = None) -> list[Product]:
    # TODO raise FileNotFoundException
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
    # TODO remove if
    if type(response.json()) is dict:
        response = [response.json()]
    else:
        response = response.json()
    products = [Product(product['id'], product['volume'], product['category_id'], product['name'], product['price'],
                        product.get('photo_url'), product.get('brand') or product.get('brand_id')) for product in
                response]
    return products
