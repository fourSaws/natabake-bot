from dataclasses import dataclass

import api


@dataclass()
class Product:
    id: int
    volume: str
    category: int
    name: str
    price: int
    photo_url: str
    brand: int

    def get_category_name(self) -> str:
        for category in api.get_categories():
            if self.category == category.id:
                return category.name

    def get_brand_name(self) -> str:
        for brand in api.get_brands():
            if self.id == brand.id:
                return brand.name


@dataclass()
class CartItem:
    id: int
    volume: int
    catalogue_id: int
    name: str
    quantity: int
    price: int
    sum: int

    def get_catalogue_item(self) -> Product:
        return api.get_products(id=self.catalogue_id)[0]


@dataclass()
class Category:
    id: int
    name: str


@dataclass()
class Brand:
    id: int
    name: str
