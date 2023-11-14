from pydantic import BaseModel


class Player(BaseModel):
    """ Player id """
    player_id: int

    """ Currencies (dict  name -> amount) """
    currencies: dict[str, int]

    """ Inventory (dict  item_id -> amount) """
    inventory: dict[str, int]


    def __init__(self, player_id: int, currencies: dict = {}, inventory: dict = {}):
        self.player_id = player_id
        self.currencies = currencies
        self.inventory = inventory
