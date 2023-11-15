import json
import os
from io import BytesIO
from typing import Optional

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from core.paginator import EmbedPaginatorSession


COG_NAME = "Gacha"
DIR = os.path.dirname(__file__)
GACHA_FILE = DIR + "/gacha.json"
CURRENCY_NAME = "Cosmic Fragment"


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

    def get_image(self):
        return Image.open(os.path.join(DIR, self.image))


class Player():
    """ Player id """
    player_id: int

    """ Pull currency """
    pull_currency: int

    """ Shop currencies (dict  name -> amount) """
    currencies: dict[str, int]

    """ Inventory (dict  item_id -> amount) """
    inventory: dict[str, int]


    def __init__(self, player_id: int, pull_currency: int = 0, currencies: dict = {}, inventory: dict = {}):
        self.player_id = player_id
        self.pull_currency = pull_currency
        self.currencies = currencies
        self.inventory = inventory

    def to_dict(self):
        res = {
            "player_id": self.player_id,
            "pull_currency": self.pull_currency,
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

    def get_shop_image(self, items: dict[str, Item]):
        font = ImageFont.truetype(os.path.join(DIR, "gg.ttf"), 16)
        img = Image.new("RGB", (1280, 720), (49, 51, 56))
        draw = ImageDraw.Draw(img)

        for i, itemprice in enumerate(self.to_sell):
            itm, price = itemprice
            item = items[itm]

            x = (i % 4) * 300 + 110
            y = (i // 4) * 300 + 110
            img.paste(item.get_image().resize((160, 160)), (x, y))

            _, _, w, _ = draw.textbbox((0, 0), item.name, font=font)
            tx = x + 80 - w / 2
            ty = y + 170
            draw.text((tx, ty), item.name, font=font, fill='white')

            pricetxt = f"{price}{self.currency_emoji}"
            _, _, w, _ = draw.textbbox((0, 0), pricetxt, font=font)
            tx = x + 80 - w / 2
            ty = y + 200
            draw.text((tx, ty), pricetxt, font=font, fill='white')

        return img



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

    items = {
        "5starRole": Item(
            "5⭐ Role",
            "This is a super rare role!",
            "000.png",
            "Super Lucky Player"
        ),
        "4starCollectible": Item(
            "4⭐ Collectible",
            "This is just a collectible, doesn't give a role but it's nice to have!",
            "001.png"
        )
    }


    shops = [
        Shop(
            currency="Plum Blossom",
            currency_emoji="🌸",
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
            100,
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

        # embeds = []
        # description = ""
        # for index, question in enumerate(self.questions):
        #     description += str(index + 1) + ". "
        #     description += question["title"]
        #     description += "\n"

        #     if index % 5 == 4 or index == len(self.questions) - 1:
        #         embed = discord.Embed(
        #             title="Upcoming questions of the day",
        #             description=description.strip(),
        #             colour=discord.Colour.dark_green()
        #         )
        #         embed.set_footer(text=self.footer)
        #         embeds.append(embed)
        #         description = ""
        
        # if len(embeds) == 0:
        #     description = "*No upcoming questions* :frowning:"
        #     embed = discord.Embed(
        #         title="Upcoming questions of the day",
        #         description=description.strip(),
        #         colour=discord.Colour.dark_green()
        #     )
        #     embed.set_footer(text=self.footer)
        #     await ctx.send(embed=embed)
        # else:
        #     paginator = EmbedPaginatorSession(ctx, *embeds)
        #     await paginator.run()

        with BytesIO() as image_binary:
            Data.shops[0].get_shop_image(Data.items).save(image_binary)
            image_binary.seek(0)
            await ctx.send("# Items to buy", file=discord.File(fp=image_binary, filename='shop.png'))


async def setup(bot):
    await bot.add_cog(Gacha(bot))
