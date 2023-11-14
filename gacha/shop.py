from pydantic import BaseModel


class Shop(BaseModel):
    """ Currency name """
    currency: str

    """ Shop name """
    name: str

    """ Items you can buy (dict  item_id -> price) """
    to_buy: dict[str, int]

    """ Items you can sell (dict  item_id -> price) """
    to_sell: dict[str, int]


    def __init__(self, currency: str, name: str = None, to_buy: dict = {}, to_sell: dict = {}):
        self.currency = currency
        
        if name is None:
            self.name = f"{self.currency} shop"
        else:
            self.name = name

        self.to_buy = to_buy
        self.to_sell = to_sell
