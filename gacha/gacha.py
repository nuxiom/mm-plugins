import datetime
import hashlib
import json
import os
import subprocess
import sys
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands

from core.paginator import EmbedPaginatorSession


COG_NAME = "Gacha"
DIR = os.path.dirname(__file__)
GACHA_FILE = os.path.join(os.path.expanduser("~"), "gacha.json")
CURRENCY_NAME = "Cosmic Fragment"
CURRENCY_EMOJI = "cosmic.png"


def hash(s: str):
    return hashlib.md5(s.encode()).hexdigest()


class Item():

    """ Name of the item """
    name: str

    """ Description in shop """
    description: str

    """ Icon in shop / collection """
    image: str

    """ Role (optional) """
    role: Optional[str]


    def __init__(self, name: str, description: str, image: str, role: Optional[str] = None) -> None:
        self.name = name
        self.description = description
        self.image = image
        self.role = role

    def to_dict(self):
        res = {
            "name": self.name,
            "description": self.description,
            "image": self.image
        }

        if self.role is not None:
            res["role"] = self.role

        return res

    @staticmethod
    def from_dict(d: dict):
        return Item(**d)


class Player():
    """ Player id """
    player_id: int

    """ Pull currency """
    pull_currency: int

    """ Shop currencies (dict  name -> amount) """
    currencies: dict[str, int]

    """ Inventory (dict  item_id -> amount) """
    inventory: dict[str, int]

    # Internal variables
    _last_talked: datetime.datetime
    _talked_this_minute: int

    def __init__(self, player_id: int, pull_currency: int = 0, currencies: dict = {}, inventory: dict = {}):
        self.player_id = player_id
        self.pull_currency = pull_currency
        self.currencies = currencies
        self.inventory = inventory

        self._last_talked = datetime.datetime.now()
        self._talked_this_minute = 0

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "pull_currency": self.pull_currency,
            "currencies": self.currencies,
            "inventory": self.inventory
        }

    @staticmethod
    def from_dict(d: dict):
        return Player(**d)


class Shop():
    """ Currency name """
    currency: str

    """ Currency emoji """
    currency_emoji: str

    """ Shop name """
    name: str

    """ Items you can buy (dict  item_id -> price) """
    to_buy: dict[str, int]

    """ Items you can sell (dict  item_id -> price) """
    to_sell: dict[str, int]


    def __init__(self, currency: str, currency_emoji: str, name: str = None, to_buy: dict = {}, to_sell: dict = {}):
        if name is None:
            name = f"{currency.title()} shop"

        self.currency = currency
        self.currency_emoji = currency_emoji
        self.name = name
        self.to_buy = to_buy
        self.to_sell = to_sell

    def to_dict(self):
        return {
            "currency": self.currency,
            "currency_emoji": self.currency_emoji,
            "name": self.name,
            "to_buy": self.to_buy,
            "to_sell": self.to_sell
        }

    @staticmethod
    def from_dict(d: dict):
        return Shop(**d)


class Banner():
    """ Banner/event name """
    name: str

    """ Items (dict  drop_weight -> list[item_id]) """
    drop_weights: dict[int, list[str]] # eg: if weight is 1 and sum of weights is 3000, 1 among 3000 chances to get one in the list

    """ Pull cost """
    pull_cost: int


    def __init__(self, name: str, pull_cost: int, drop_weights: dict = {}):
        self.name = name
        self.pull_cost = pull_cost
        self.drop_weights = drop_weights

    def to_dict(self):
        new_drop_weights = {}
        for weight, lst in self.drop_weights.items():
            new_drop_weights[str(weight)] = lst

        return {
            "name": self.name,
            "pull_cost": self.pull_cost,
            "drop_weights": new_drop_weights
        }

    @staticmethod
    def from_dict(d: dict):
        new_drop_weights = {}
        for weight, lst in d["drop_weights"].items():
            new_drop_weights[int(weight)] = lst

        d["drop_weights"] = new_drop_weights
        return Banner(**d)

    def get_rates_text(self, items: dict[str, Item]):
        text = f"### Pulls cost: {self.pull_cost} {CURRENCY_NAME}{'s' if self.pull_cost > 1 else ''}\n\n"

        sorted_rates = sorted(self.drop_weights.keys())
        total_weight = sum(sorted_rates)

        for weight in sorted_rates:
            rate = weight / total_weight * 100
            text += f"{rate:.2f}% chance to get one of the following:\n"

            for item_id in self.drop_weights[weight]:
                text += f"- {items[item_id].name}\n"

            text += "\n"

        return text.strip()


class Data:

    items = {}

    shops = []

    banners = []

    with open(os.path.join(DIR, "data.json"), encoding='utf8') as f:
        o = json.load(f)

        for k, v in o["items"].items():
            items[k] = Item.from_dict(v)

        for s in o["shops"]:
            shops.append(Shop.from_dict(s))

        for b in o["banners"]:
            banners.append(Banner.from_dict(b))


class Gacha(commands.Cog, name=COG_NAME):
    """Earn currency, gacha-it, and win roles!"""

    save: dict[int, Player]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if os.path.exists(GACHA_FILE):
            self.load_conf()
        else:
            self.save = {}

        subprocess.run([sys.executable, os.path.join(DIR, 'generate_shop.py')])

        self.footer = ""  # TODO: added just in case we do something with it someday


    def load_conf(self):
        with open(GACHA_FILE, "r") as f:
            save = json.load(f)

        for k, v in save.items():
            self.save[int(k)] = Player.from_dict(v)


    def save_conf(self):
        save = {}
        for k, v in self.save.items():
            save[str(k)] = v.to_dict()

        with open(GACHA_FILE, "w+") as f:
            json.dump(save, f)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id in self.save:
            player = self.save[message.author.id]
        else:
            player = Player(message.author.id)
            self.save[message.author.id] = player

        t = datetime.datetime.now()
        if player._last_talked.minute != t.minute or player._last_talked.hour != t.hour or player._last_talked.date != t.date:
            player._last_talked = t
            player._talked_this_minute = 0

        msg: str = message.content
        if not msg.startswith("?") and player._talked_this_minute < 10:
            score = len(msg.split())
            player.pull_currency += score
            self.save_conf()
            player._talked_this_minute += 1


    @commands.group(invoke_without_command=True)
    async def gacha(self, ctx):
        """
        Ruan Mei Mains' gacha system!
        """

        await ctx.send_help(ctx.command)


    # Get gacha drop rates
    @gacha.command(name="details", aliases=["rates"])
    async def details(self, ctx: commands.Context, *, banner: str = None):
        """Display gacha drop rates for current banner"""

        bann: Banner = None
        if banner is None:
            if len(Data.banners) == 1:
                bann = Data.banners[0]
        else:
            if banner.isnumeric() and int(banner) > 0 and int(banner) <= len(Data.banners):
                bann = Data.banners[int(banner) - 1]
            else:
                for b in Data.banners:
                    if b.name == banner:
                        bann = b
                        break

        if bann is None:
            description = f'Banner "{banner}" not found!'
            colour = discord.Colour.red()
        else:
            bann_description = bann.get_rates_text(Data.items)
            description = f"# {bann.name}\n\n{bann_description}"
            colour = discord.Colour.green()


        embed = discord.Embed(
            title="Banner details",
            description=f"{description}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # List items in shop
    @gacha.command(name="shop")
    async def shop(self, ctx: commands.Context):
        """Lists upcoming questions of the day"""
        shop = Data.shops[0]
        filename = f"to_buy_{hash(json.dumps(shop.to_dict()))}.png"
        path = os.path.join(DIR, "img", "shops", filename)
        with open(path, "rb") as f:
            await ctx.send("# Items to buy", file=discord.File(fp=f, filename='shop.png'))

        filename = f"to_sell_{hash(json.dumps(shop.to_dict()))}.png"
        path = os.path.join(DIR, "img", "shops", filename)
        with open(path, "rb") as f:
            await ctx.send("# Items to sell", file=discord.File(fp=f, filename='shop.png'))


    # Get player balance
    @gacha.command(name="balance", aliases=["money"])
    async def balance(self, ctx: commands.Context, *, member: commands.MemberConverter = None):
        """Shows a user's currency balance"""

        if member is None:
            member = ctx.author

        if member.id in self.save:
            player = self.save[member.id]

            description = "## Pull currency:\n"
            description += f"{player.pull_currency} {CURRENCY_NAME}{'s' if player.pull_currency > 1 else ''}"
            colour = discord.Colour.green()
        else:
            description = f"{member.display_name} isn't in our database. Have they ever talked??"
            colour = discord.Colour.red()

        embed = discord.Embed(
            title=f"{member.display_name}'s money",
            description=f"{description}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Gacha(bot))
