import typing
from dataclasses import dataclass
from io import BytesIO
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
            if self.brand == brand.id:
                return brand.name

    def get_photo(self) -> typing.BinaryIO:
        if self.photo_url:
            photo = api.get_photo(self.photo_url)
        else:
            photo = open("no_image.jpg", "rb")
        return photo


@dataclass()
class CartItem:
    catalogue_item: Product
    quantity: int
    sum: int
    cart_id: int


@dataclass()
class Category:
    id: int
    name: str


@dataclass()
class Brand:
    id: int
    name: str
