class Player():
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


    def to_dict(self):
        res = {
            "player_id": self.player_id,
            "currencies": self.currencies,
            "inventory": self.inventory
        }

        return res


    @staticmethod
    def from_dict(d: dict):
        return Player(**d)
