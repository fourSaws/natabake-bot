import logging
import typing
from dataclasses import dataclass, field
from enum import Enum
import api

logger = logging.getLogger(__name__)


class Status(Enum):
    IN_CART = 0
    CASH = 1
    WAITING_FOR_PAYMENT = 2
    PAID = 3


@dataclass()
class Product:
    id: int
    volume: str
    category: int
    name: str
    price: int
    photo_url: str
    brand: int

    def __post_init__(self):
        if self.photo_url is None:
            self.photo_url = ""

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
    sum: int = field(init=False)
    cart_id: int

    def __post_init__(self):
        self.sum = self.quantity * self.catalogue_item.price


@dataclass()
class Category:
    id: int
    name: str


@dataclass()
class Brand:
    id: int
    name: str


@dataclass()
class User:
    chat_id: int
    phone_number: str
    address: str
    comment: str

    def __setattr__(self, name, value):
        logger.info(f"{name=} {value=}")
        if name == "phone_number":
            super().__setattr__(name, self.__validate_phone(value))
        else:
            return super().__setattr__(name, value)

    def __validate_phone(self, value=None):
        number = value or self.__dict__.get("phone_number")
        if number.startswith("+"):
            if number[1] != "7":
                raise ValueError("Поддерживаются только номера из России")

        elif not number.isdigit():
            print(f"{number=}")
            raise ValueError("Неправильный формат номера")
        else:
            if number[0] == "8":
                number = "+7" + number[1:]
            elif number[0] == "7":
                number = "+" + number
            elif len(number) == 10:
                number = "+7" + number
            else:
                raise ValueError("Поддерживаются только номера из России")
        if not number[1:].isdigit() or len(number) != 12:
            raise ValueError("Неправильный формат номера")
        return number


@dataclass()
class Order:
    client: int  # foreign key to User (chat_id)
    cart: str
    sum: float
    address: str
    status: Status
    comment: str
    id: int = None
    free_delivery: bool = True
