import json
import os
import random

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

    fiftyfifty: bool
    pities: dict[int, int]
    tag: str

    _cumulative_weights = []
    _items_by_rarity: dict[int, list[Item]] = {}
    _offrates_by_rarity: dict[int, list[Item]] = {}

    def __init__(self, name: str, tag: str, img: str, colour: int, pull_cost: int, items: list[Item], offrates: list[Item] = [], drop_weights: dict = {}, fiftyfifty: bool = False, pities: dict = {}):
        self.name = name
        self.tag = tag
        self.img = img
        self.colour = colour
        self.pull_cost = pull_cost
        self.drop_weights = drop_weights
        self.fiftyfifty = fiftyfifty
        self.pities = pities

        self._cumulative_weights = [0]
        for w in self.drop_weights.values():
            self._cumulative_weights.append(self._cumulative_weights[-1] + w)
        self._cumulative_weights.pop(0)

        self._items_by_rarity = {rarity: [] for rarity in drop_weights.keys()}
        for itm in items:
            if itm.RARITY in self._items_by_rarity:
                self._items_by_rarity[itm.RARITY].append(itm)

        self._offrates_by_rarity = {rarity: [] for rarity in drop_weights.keys()}
        for itm in offrates:
            if itm.RARITY in self._offrates_by_rarity:
                self._offrates_by_rarity[itm.RARITY].append(itm)

    def get_pulls_results(self, pull_count: int, player):
        pull_results = []
        for _ in range(pull_count):
            rnd = random.randint(0, self._cumulative_weights[-1] - 1)
            for i in range(len(self._cumulative_weights)):
                if rnd < self._cumulative_weights[i]:
                    rarity = list(self.drop_weights.keys())[i]
                    for r in sorted(player.pulls_status.pities[self.tag].keys()):
                        if player.pulls_status.pities[self.tag][r] == self.pities[r] - 1:
                            rarity = r
                    for r in player.pulls_status.pities[self.tag]:
                        if rarity == r:
                            player.pulls_status.pities[self.tag][r] = 0
                        else:
                            player.pulls_status.pities[self.tag][r] += 1

                    if self.fiftyfifty and len(self._offrates_by_rarity[rarity]) > 0:
                        if player.pulls_status.fiftyfifties[self.tag][rarity]:
                            win = (random.random() > 0.5)
                        else:
                            win = True
                        if win:
                            item = random.choice(self._items_by_rarity[rarity])
                            player.pulls_status.fiftyfifties[self.tag][rarity] = True
                        else:
                            item = random.choice(self._offrates_by_rarity[rarity])
                            player.pulls_status.fiftyfifties[self.tag][rarity] = False
                    else:
                        item = random.choice(self._items_by_rarity[rarity])
                    pull_results.append(item)
                    break
        return pull_results

    def get_rates_text(self):
        text = f"### Pulls cost: {self.pull_cost} {CURRENCY_EMOJI}\n"

        text += "### Guarantees:\n"
        if len(self.pities) > 0:
            for rarity, pulls in self.pities.items():
                text += f"- Guaranteed to get a **{rarity}⭐️ item** every **{pulls} pulls**\n"
        else:
            text += "*No guarantees*\n"

        text += "### Uprate items\n"

        for r, i in self._items_by_rarity.items():
            itms = ", ".join([itm.DISPLAY_NAME for itm in i])
            if len(itms) > 0:
                text += f"- {r}⭐ items: **{itms}**\n"

        if self.fiftyfifty:
            text += "### Offrate items\n"

            for r, i in self._offrates_by_rarity.items():
                itms = ", ".join([itm.DISPLAY_NAME for itm in i])
                if len(itms) > 0:
                    text += f"- {r}⭐ items: **{itms}**\n"

            text += "### 50/50\nEverytime you get a 4⭐️ or 5⭐️, there's a 50% chance to get an uprate item, and a 50% chance to get an offrate item.\n"

        text += "### Drop rates\n"

        total_weight = sum(self.drop_weights.values())

        for r, weight in self.drop_weights.items():
            rate = weight / total_weight * 100
            text += f"- {rate:.2f}% chance to get a {r}⭐ item\n"

        return text.strip()


class Data:

    FOUR_STAR_GATOS = [g for g in GATOS if g.RARITY == 4]
    SIX_STAR_GATOS = [g for g in GATOS if g.RARITY == 6]
    PERMANENT_FIVE_STARS = [
        ExampleGato
    ]
    ALL_ITEMS = CONSUMABLES+EQUIPMENTS+TEAM_EQUIPMENTS+GATOS
    THREE_STARS = [i for i in ALL_ITEMS if i.RARITY == 3]

    banners = [
        Banner(
            name="Lunar New Year Banner",
            tag="limited",
            img="https://media.discordapp.net/attachments/1174877208377036884/1195010321820176525/critter_banner_mockups_2.png",
            colour=0x8ac7a4,
            pull_cost=1000,
            fiftyfifty=True,
            pities={
                4: 10,
                5: 90
            },
            items=[
                LNYGato,
                FuxuanGato,
                QingqueGato
            ]+SIX_STAR_GATOS+THREE_STARS,
            offrates=FOUR_STAR_GATOS+PERMANENT_FIVE_STARS,
            drop_weights={
                6: 1,
                5: 12,
                4: 102,
                3: 1885
            }
        ),
        Banner(
            name="Permanent Banner",
            tag="permanent",
            img="https://media.discordapp.net/attachments/1174877208377036884/1195380679664467988/critter_banner_mockups_4.png",
            colour=0x6a9b98,
            pull_cost=1000,
            pities={
                4: 10,
                5: 90
            },
            items=SIX_STAR_GATOS+PERMANENT_FIVE_STARS+FOUR_STAR_GATOS+THREE_STARS,
            drop_weights={
                6: 1,
                5: 12,
                4: 102,
                3: 1885
            }
        )
    ]

    animations: dict
    with open(os.path.join(DIR, "animations.json"), "r") as f:
        animations = json.load(f)
