import json
import os

from gatos import *

DIR = os.path.dirname(__file__)
CURRENCY_NAME = "Plum Blossom"
CURRENCY_EMOJI = "🌸"

class Banner():
    """ Banner/event name """
    name: str

    """ Banner art """
    img: str

    """ Banner colour """
    colour: int

    """ Chances to drop depending on rarity (dict  rarity -> drop_weight) """
    drop_weights: dict[int, int] # eg: if weight is 1 and sum of weights is 3000, 1 among 3000 chances to get one in the list

    """ Pull cost """
    pull_cost: int

    _cumulative_weights = []
    _item_by_rarity: dict[int, list[Gato]] = {}

    def __init__(self, name: str, img: str, colour: int, pull_cost: int, items: list[Gato], drop_weights: dict = {}):
        self.name = name
        self.img = img
        self.colour = colour
        self.pull_cost = pull_cost
        self.drop_weights = drop_weights

        self._cumulative_weights = [0]
        for w in sorted(self.drop_weights.values()):
            self._cumulative_weights.append(self._cumulative_weights[0] + w)
        self._cumulative_weights.pop(0)

        self._item_by_rarity = {rarity: [] for rarity in drop_weights.keys()}
        for itm in items:
            if itm.RARITY in self._item_by_rarity:
                self._item_by_rarity[itm.RARITY].append(itm)

    def get_rates_text(self):
        text = f"### Pulls cost: {self.pull_cost} {CURRENCY_EMOJI}\n"

        text += "### Items\n"

        for r, i in self._item_by_rarity.items():
            itms = ", ".join([itm.DISPLAY_NAME for itm in i])
            text += f"- {r}⭐ items: **{itms}**\n"

        text += "### Drop rates\n"

        total_weight = sum(self.drop_weights.values())

        for r, weight in self.drop_weights.items():
            rate = weight / total_weight * 100
            text += f"- {rate:.2f}% chance to get a {r}⭐ item\n"

        return text.strip()


class Data:

    banners = [
        Banner(
            name="Standard Banner",
            img="https://media.discordapp.net/attachments/1106791361157541898/1193230143217479690/chloe_banner_6.png",
            colour=0x669D96,
            pull_cost=100,
            items=[
                ExampleGato,
                NormalGato,
                NormalGato2
            ],
            drop_weights={
                5: 1,
                4: 10,
                3: 20
            }
        ),
        Banner(
            name="The same banner lol",
            img="https://media.discordapp.net/attachments/1106791361157541898/1193230143217479690/chloe_banner_6.png",
            colour=0x669D96,
            pull_cost=100,
            items=[
                ExampleGato,
                NormalGato,
                NormalGato2
            ],
            drop_weights={
                5: 1,
                4: 10,
                3: 20
            }
        )
    ]

    animations: dict
    with open(os.path.join(DIR, "animations.json"), "r") as f:
        animations = json.load(f)
