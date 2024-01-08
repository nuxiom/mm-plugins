import json
import os

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

    """ Items (dict  drop_weight -> list[item_id]) """
    drop_weights: dict[int, list[str]] # eg: if weight is 1 and sum of weights is 3000, 1 among 3000 chances to get one in the list

    """ Pull cost """
    pull_cost: int

    _cumulative_weights = []

    def __init__(self, name: str, img: str, colour: int, pull_cost: int, drop_weights: dict = {}):
        self.name = name
        self.img = img
        self.colour = colour
        self.pull_cost = pull_cost
        self.drop_weights = drop_weights

        self._cumulative_weights = [0]
        for w in sorted(self.drop_weights.keys()):
            self._cumulative_weights.append(self._cumulative_weights[0] + w)
        self._cumulative_weights.pop(0)

    # def to_dict(self):
    #     new_drop_weights = {}
    #     for weight, lst in self.drop_weights.items():
    #         new_drop_weights[str(weight)] = lst

    #     return {
    #         "name": self.name,
    #         "pull_cost": self.pull_cost,
    #         "drop_weights": new_drop_weights
    #     }

    # @staticmethod
    # def from_dict(d: dict):
    #     new_drop_weights = {}
    #     for weight, lst in d["drop_weights"].items():
    #         new_drop_weights[int(weight)] = lst

    #     d["drop_weights"] = new_drop_weights
    #     return Banner(**d)

    def get_rates_text(self):
        text = f"### Pulls cost: {self.pull_cost} {CURRENCY_EMOJI}\n\n"

        sorted_rates = sorted(self.drop_weights.keys())
        total_weight = sum(sorted_rates)

        for weight in sorted_rates:
            rate = weight / total_weight * 100
            text += f"{rate:.2f}% chance to get one of the following:\n"

            for item_id in self.drop_weights[weight]:
                text += f"- {item_id}\n"

            text += "\n"

        return text.strip()


class Data:

    banners = [
        Banner(
            "Standard Banner",
            "https://media.discordapp.net/attachments/1106791361157541898/1193230143217479690/chloe_banner_6.png",
            0x669D96,
            100,
            {
                1: ["gatos.ExampleGato"],
                10: ["gatos.NormalGato"],
                20: ["gatos.NormalGato2"]
            }
        ),
        Banner(
            "The same banner lol",
            "https://media.discordapp.net/attachments/1106791361157541898/1193230143729188986/xiao_banner_2.png",
            0xA83319,
            100,
            {
                1: ["gatos.ExampleGato"],
                10: ["gatos.NormalGato"],
                20: ["gatos.NormalGato2"]
            }
        )
    ]

    animations: dict
    with open(os.path.join(DIR, "animations.json"), "r") as f:
        animations = json.load(f)
