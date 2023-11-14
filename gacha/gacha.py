import json
import os
from typing import Optional

import discord
from discord.ext import commands

from core.paginator import EmbedPaginatorSession


GACHA_FILE = os.path.dirname(__file__) + "/gacha.json"

COG_NAME="Gacha"


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


class Shop():
    """ Currency name """
    currency: str

    """ Shop name """
    name: str

    """ Items you can buy (dict  item_id -> price) """
    to_buy: dict[str, int]

    """ Items you can sell (dict  item_id -> price) """
    to_sell: dict[str, int]


    def __init__(self, currency: str, name: str = None, to_buy: dict = {}, to_sell: dict = {}):
        if name is None:
            name = f"{currency.title()} shop"

        self.currency = currency
        self.name = name
        self.to_buy = to_buy
        self.to_sell = to_sell


class Banner():
    """ Banner/event name """
    name: str

    """ Items (dict  drop_weight -> list[item_id]) """
    drop_weights: dict[int, list[str]] # eg: if weight is 1 and sum of weights is 3000, 1 among 3000 chances to get one in the list


    def __init__(self, name: str, drop_weights: dict = {}):
        self.name = name
        self.drop_weights = drop_weights


    def get_rates_text(self, items: dict[str, Item]):
        text = ""

        sorted_rates: sorted(self.drop_weights.keys())
        total_weight = sum(sorted_rates)

        for weight in sorted_rates:
            rate = weight / total_weight * 100
            text += f"{rate:.2f}% chance to get one of the following:\n"

            for item_id in self.drop_weights[weight]:
                text += f"- {items[item_id].name}\n"

            text += "\n"

        return text.strip()


class Data:

    items = {
        "5starRole": Item(
            "5⭐ Role",
            "This is a super rare role!",
            "https://media.discordapp.net/attachments/1106786214608109669/1173895704821907517/ruan_mei_mooncake.png?ex=65659e91&is=65532991&hm=5a9e5f513c124acfbdf05a2c1f02b14df757395aaa0725ca2d1fb25184073f94&=&width={size}&height={size}",
            "Super Lucky Player"
        ),
        "4starCollectible": Item(
            "4⭐ Collectible",
            "This is just a collectible, doesn't give a role but it's nice to have!",
            "https://media.discordapp.net/attachments/1106786214608109669/1173895705329405952/ruan_mei_dumpling.png?ex=65659e92&is=65532992&hm=4a134dee3c3568714b8654fd3109840937589664a2a8bfd1a1a5c3ff892b55ec&=&width={size}&height={size}"
        )
    }


    shops = [
        Shop(
            currency="Plum Blossom",
            to_buy={
                "5starRole": 1e6
            },
            to_sell={
                "4starCollectible": 300
            }
        )
    ]


    banners = [
        Banner(
            "Standard banner",
            {
                1: ["5starRole"],
                2999: ["4starCollectible"]
            }
        )
    ]




class Gacha(commands.Cog, name=COG_NAME):
    """Earn currency, gacha-it, and win roles!"""

    save: dict

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if os.path.exists(GACHA_FILE):
            self.load_conf()
        else:
            self.save = {}

        self.footer = ""  # TODO: added just in case we do something with it someday


    def load_conf(self):
        with open(GACHA_FILE, "r") as f:
            self.save = json.load(f)


    def save_conf(self):
        with open(GACHA_FILE, "w+") as f:
            json.dump(self.save, f)


    @commands.group(invoke_without_command=True)
    async def gacha(self, ctx):
        """
        Ruan Mei Mains' gacha system!
        """

        await ctx.send_help(ctx.command)


    # Get gacha drop rates
    @gacha.command(name="details", aliases=["rates"])
    async def add_qotd(self, ctx: commands.Context, *, banner: str = None):
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
            colour = discord.Colour.red
        else:
            bann_description = bann.get_rates_text(Data.items)
            description = f"# {bann.name}\n\n{bann_description}"


        embed = discord.Embed(
            title="Banner details",
            description=f"{description}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # List questions of the day
    @commands.has_role("QOTD Manager")
    @gacha.command(name="list")
    async def list_qotd(self, ctx: commands.Context):
        """Lists upcoming questions of the day"""

        embeds = []
        description = ""
        for index, question in enumerate(self.questions):
            description += str(index + 1) + ". "
            description += question["title"]
            description += "\n"

            if index % 5 == 4 or index == len(self.questions) - 1:
                embed = discord.Embed(
                    title="Upcoming questions of the day",
                    description=description.strip(),
                    colour=discord.Colour.dark_green()
                )
                embed.set_footer(text=self.footer)
                embeds.append(embed)
                description = ""
        
        if len(embeds) == 0:
            description = "*No upcoming questions* :frowning:"
            embed = discord.Embed(
                title="Upcoming questions of the day",
                description=description.strip(),
                colour=discord.Colour.dark_green()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
        else:
            paginator = EmbedPaginatorSession(ctx, *embeds)
            await paginator.run()


async def setup(bot):
    await bot.add_cog(Gacha(bot))
