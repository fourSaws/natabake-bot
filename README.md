# Чат-бот натабаке
https://artempas.atlassian.net/browse/SP-1

## Тз для админки:

getCart(chat_id:int)->list[CartItem]

clearCart(chat_id:int)->response

editCart(id:int, quantity:int,chat_id=int) -> CartItem  # если quantity=0 - удалить и вернуть пустой ответ - ?

addToCart(chat_id:int,id_product:int)->response

getProducts(brand:str=None,category:str,id:int)->list[Product] 

getBrands()->list[Brand] 

getCategories()->list[Category]


class CartItem:
    id: int
    catalogue_id: int    
    name: str    
    quantity: int    
    price: int    
    sum: int
    
class Product:
    id: int
    category:int  # id
    name: str
    price: int
    photo_url: str
    brand: int # id
    
class Category:
    id: int
    name: str

class Brand:
    id:int 
    name: str
