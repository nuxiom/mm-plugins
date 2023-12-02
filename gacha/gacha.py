import datetime
import hashlib
import io
import json
import os
import random
import uuid
from typing import Optional

import asyncio
import discord
import requests
from discord.ext import commands
from discord.utils import get
from PIL import Image

from core import checks
from core.models import PermissionLevel, getLogger
from core.paginator import EmbedPaginatorSession

logger = getLogger(__name__)


COG_NAME = "Gacha"
DIR = os.path.dirname(__file__)
GACHA_FILE = os.path.join(os.path.expanduser("~"), "gacha.json")
CURRENCY_NAME = "Cosmic Fragment"
CURRENCY_EMOJI = "cosmic.png"
PULL_ANIM = [
    "https://media.discordapp.net/attachments/1179003913354104832/1179017794994569236/pull-5star.gif",
    "https://media.discordapp.net/attachments/1179003913354104832/1179029377976119306/pull-3star.gif"
]


def hash2(s: str):
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

    def get_image(self):
        return Image.open(os.path.join(DIR, "img", "items", self.image))


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
    _pulling: bool

    def __init__(self, player_id: int, pull_currency: int = 0, currencies: dict = {}, inventory: dict = {}):
        self.player_id = player_id
        self.pull_currency = pull_currency
        self.currencies = currencies
        self.inventory = inventory

        self._last_talked = datetime.datetime.now()
        self._talked_this_minute = 0
        self._pulling = False

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

    _cumulative_weights = []

    def __init__(self, name: str, pull_cost: int, drop_weights: dict = {}):
        self.name = name
        self.pull_cost = pull_cost
        self.drop_weights = drop_weights

        self._cumulative_weights = [0]
        for w in sorted(self.drop_weights.keys()):
            self._cumulative_weights.append(self._cumulative_weights[0] + w)
        self._cumulative_weights.pop(0)

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

    items: dict[str, Item] = {}

    shops: list[Shop] = []

    banners: list[Banner] = []

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
        self.cog_id = uuid.uuid4()

        self.save = {}
        if os.path.exists(GACHA_FILE):
            self.load_conf()

        logger.info(os.getcwd())

        self.bot.loop.create_task(self.schedule_save())

        shops_save = os.path.join(DIR, "shops_url.json")
        self.shop_images = {}
        if os.path.exists(shops_save):
            with open(shops_save) as f:
                self.shop_images = json.load(f)
        for shop in Data.shops:
            n = len(shop.to_sell) // 8 + 1
            for i in range(n):
                filename = f"to_sell_{hash2(json.dumps(shop.to_dict()))}_{i}.png"
                if filename not in self.shop_images.keys():
                    logger.warn(f"No image for shop {shop.name}-{i}")

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


    async def schedule_save(self):
        while True:
            cog: Gacha = self.bot.get_cog(COG_NAME)
            if cog is None or cog.cog_id != self.cog_id:
                # We are in an old cog after update and don't have to send QOTD anymore
                break
            await asyncio.sleep(60)
            self.save_conf()


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author.id in self.save:
            player = self.save[message.author.id]
        else:
            player = Player(message.author.id)
            self.save[message.author.id] = player

        t = datetime.datetime.now()
        if player._last_talked.minute != t.minute or player._last_talked.hour != t.hour or player._last_talked.date() != t.date():
            player._last_talked = t
            player._talked_this_minute = 0

        msg: str = message.content
        if not msg.startswith("?") and player._talked_this_minute < 10:
            filtered = list(filter(lambda w: len(w) > 1, msg.split()))
            score = min(len(filtered), 20)
            player.pull_currency += score

            if len(message.stickers) > 0:
                player.pull_currency += 3

            player._talked_this_minute += 1


    def get_banner(self, banner: str):
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
        return bann


    def get_shop(self, shop: str):
        shp: Shop = None
        if shop is None:
            if len(Data.shops) == 1:
                shp = Data.shops[0]
        else:
            if shop.isnumeric() and int(shop) > 0 and int(shop) <= len(Data.shops):
                shp = Data.shops[int(shop) - 1]
            else:
                for s in Data.shops:
                    if s.name == shop:
                        shp = s
                        break
        return shp


    def get_item(self, item: str):
        for item_id, itm in Data.items.items():
            if itm.name == item or item_id == item:
                return item_id, itm
        return None, None


    def get_item_price(self, item: str, prices: dict[str, int]):
        itm: Item = None
        price: int = None
        if item.isnumeric() and int(item) > 0 and int(item) <= len(prices):
            item_id, price = list(prices.items())[int(item) - 1]
            itm = Data.items[item_id]
        else:
            item_id, itm = self.get_item(item)
            if item_id in prices.keys():
                price = prices[item_id]
            else:
                itm = None
        return itm, price


    async def give_role(self, ctx: commands.Context, item: Item):
        if item.role is not None:
            try:
                role = get(ctx.guild.roles, name=item.role)
                logger.info(f"{ctx.author} won role {item.role}")
                await ctx.author.add_roles(role)
                self.save_conf()
            except:
                logger.error(f"Error while giving role {item.role} to {ctx.author}")


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

        bann = self.get_banner(banner)

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


    # List items to buy in shops
    @gacha.command(name="buy")
    async def buy(self, ctx: commands.Context, item: str = None, count: int = 1, shop: str = None):
        """Buy items / Shows what's to buy in the shops"""

        if item is None:
            embeds = []
            for shop in Data.shops:
                n = len(shop.to_buy) // 8 + 1
                for i in range(n):
                    embed = discord.Embed(
                        title="Items to buy",
                        description=f"## Items to buy - {shop.name} ({i+1}/{n})",
                        colour=discord.Colour.green()
                    )

                    filename = f"to_buy_{hash2(json.dumps(shop.to_dict()))}_{i}.png"
                    if filename in self.shop_images.keys():
                        embed.set_image(url=self.shop_images[filename])
                    else:
                        embed.set_footer("ERROR: No image for this shop. Please ping @cyxo")
                    embeds.append(embed)

            paginator = EmbedPaginatorSession(ctx, *embeds)
            await paginator.run()
        else:
            title = "Buy item"
            colour = discord.Colour.red()
            if ctx.author.id not in self.save:
                embed = discord.Embed(
                    title=title,
                    description=f"You don't have any currency. Try talking a little before trying to buy, okay?",
                    colour=colour
                )
                embed.set_footer(text=self.footer)
                await ctx.send(embed=embed)
                return
            player = self.save[ctx.author.id]

            if item.isnumeric():
                if shop is None and len(Data.shops) > 1:
                    txt_shop_list = "\n".join([f'{i+1}. "{shop.name}"' for i, shop in enumerate(Data.shops)])
                    embed = discord.Embed(
                        title=title,
                        description=f"**Multiple shops found. Please specify a shop to use:**\n{txt_shop_list}\nUsage: `?gacha buy {item} {count} [shop name or number]`",
                        colour=colour
                    )
                    embed.set_footer(text=self.footer)
                    await ctx.send(embed=embed)
                    return
                
                shp = self.get_shop(shop)
                if shp is None:
                    description = f'Shop "{shop}" not found'
                else:
                    itm, price = self.get_item_price(item, shp.to_buy)
                    if itm is None:
                        description = f'Item "{item}" not found in shop "{shp.name}"'
                    else:
                        item_id, _ = self.get_item(itm.name)
                        total_price = price * count
                        if shp.currency_emoji not in player.currencies.keys() or player.currencies[shp.currency_emoji] < total_price:
                            description = f"You don't have enough {shp.currency}s to buy {count} {itm.name}"
                        else:
                            player.currencies[shp.currency_emoji] -= total_price
                            if item_id not in player.inventory.keys():
                                player.inventory[item_id] = 0
                            player.inventory[item_id] += count
                            description = f"You bought **{count} {itm.name}** for **{total_price}** {shp.currency_emoji}"
                            colour = discord.Colour.green()
            else:
                shp = None
                if shop == None:
                    avail_shops = []
                    item_id, itm = self.get_item(item)
                    for s in Data.shops:
                        if item_id in s.to_buy.keys():
                            avail_shops.append(s)

                    if len(avail_shops) > 1:
                        txt_shop_list = "\n".join([f'{i+1}. "{shop.name}"' for i, shop in enumerate(avail_shops)])
                        description = f'**Multiple shops found to buy "{item}". Please specify a shop to use:**\n{txt_shop_list}\nUsage: `?gacha buy "{item}" {count} [shop name or number]`'
                    elif len(avail_shops) == 0:
                        description = f'No shop to buy "{item}" at the moment'
                    else:
                        shp = avail_shops[0]
                else:
                    shp = self.get_shop(shop)
                    if shp is None:
                        description = f'Shop "{shop}" not found'

                if shp is not None:
                    itm, price = self.get_item_price(item, shp.to_buy)
                    if itm is None:
                        description = f'Item "{item}" not found in shop "{shp.name}"'
                    else:
                        item_id, _ = self.get_item(itm.name)
                        total_price = price * count
                        if shp.currency_emoji not in player.currencies.keys() or player.currencies[shp.currency_emoji] < total_price:
                            description = f"You don't have enough {shp.currency}s to buy {count} {itm.name}"
                        else:
                            player.currencies[shp.currency_emoji] -= total_price
                            if item_id not in player.inventory.keys():
                                player.inventory[item_id] = 0
                            player.inventory[item_id] += count
                            description = f"You bought **{count} {itm.name}** for **{total_price}** {shp.currency_emoji}"
                            colour = discord.Colour.green()

            embed = discord.Embed(
                title=title,
                description=description,
                colour=colour
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)


    @gacha.command(name="sell")
    async def sell(self, ctx: commands.Context, item: str = None, count: int = 1, shop: str = None):
        """Sell items / Shows what's to sell in the shops"""

        if item is None:
            embeds = []
            for shop in Data.shops:
                n = len(shop.to_sell) // 8 + 1
                for i in range(n):
                    embed = discord.Embed(
                        title="Items to sell",
                        description=f"## Items to sell - {shop.name} ({i+1}/{n})",
                        colour=discord.Colour.green()
                    )

                    filename = f"to_sell_{hash2(json.dumps(shop.to_dict()))}_{i}.png"
                    if filename in self.shop_images.keys():
                        embed.set_image(url=self.shop_images[filename])
                    else:
                        embed.set_footer(text="ERROR: No image for this shop. Please ping @cyxo")
                    embeds.append(embed)

            paginator = EmbedPaginatorSession(ctx, *embeds)
            await paginator.run()
        else:
            title = "Sell item"
            colour = discord.Colour.red()
            if ctx.author.id not in self.save:
                embed = discord.Embed(
                    title=title,
                    description=f"You don't have any item. Try talking a little before trying to sell, okay?",
                    colour=colour
                )
                embed.set_footer(text=self.footer)
                await ctx.send(embed=embed)
                return
            player = self.save[ctx.author.id]

            if item.isnumeric():
                if shop is None and len(Data.shops) > 1:
                    txt_shop_list = "\n".join([f'{i+1}. "{shop.name}"' for i, shop in enumerate(Data.shops)])
                    embed = discord.Embed(
                        title=title,
                        description=f"**Multiple shops found. Please specify a shop to use:**\n{txt_shop_list}\nUsage: `?gacha sell {item} {count} [shop name or number]`",
                        colour=colour
                    )
                    embed.set_footer(text=self.footer)
                    await ctx.send(embed=embed)
                    return
                
                shp = self.get_shop(shop)
                if shp is None:
                    description = f'Shop "{shop}" not found'
                else:
                    itm, price = self.get_item_price(item, shp.to_sell)
                    if itm is None:
                        description = f'Item "{item}" not found in shop "{shp.name}"'
                    else:
                        item_id, _ = self.get_item(itm.name)
                        if item_id not in player.inventory.keys() or player.inventory[item_id] < count:
                            description = f"You don't have enough {itm.name} in your inventory to sell {count} of them..."
                        else:
                            total_price = price * count
                            player.inventory[item_id] -= count
                            if shp.currency_emoji not in player.currencies.keys():
                                player.currencies[shp.currency_emoji] = 0
                            player.currencies[shp.currency_emoji] += total_price
                            description = f"You sold **{count} {itm.name}** and earned **{total_price}** {shp.currency_emoji}"
                            colour = discord.Colour.green()
            else:
                shp = None
                if shop == None:
                    avail_shops = []
                    item_id, itm = self.get_item(item)
                    for s in Data.shops:
                        if item_id in s.to_sell.keys():
                            avail_shops.append(s)

                    if len(avail_shops) > 1:
                        txt_shop_list = "\n".join([f'{i+1}. "{shop.name}"' for i, shop in enumerate(avail_shops)])
                        description = f'**Multiple shops found to sell "{item}". Please specify a shop to use:**\n{txt_shop_list}\nUsage: `?gacha sell "{item}" {count} [shop name or number]`'
                    elif len(avail_shops) == 0:
                        description = f'No shop to sell "{item}" at the moment'
                    else:
                        shp = avail_shops[0]
                else:
                    shp = self.get_shop(shop)
                    if shp is None:
                        description = f'Shop "{shop}" not found'

                if shp is not None:
                    itm, price = self.get_item_price(item, shp.to_sell)
                    if itm is None:
                        description = f'Item "{item}" not found in shop "{shp.name}"'
                    else:
                        item_id, _ = self.get_item(itm.name)
                        if item_id not in player.inventory.keys() or player.inventory[item_id] < count:
                            description = f"You don't have enough {itm.name} in your inventory to sell {count} of them..."
                        else:
                            total_price = price * count
                            player.inventory[item_id] -= count
                            if shp.currency_emoji not in player.currencies.keys():
                                player.currencies[shp.currency_emoji] = 0
                            player.currencies[shp.currency_emoji] += total_price
                            description = f"You sold **{count} {itm.name}** and earned **{total_price}** {shp.currency_emoji}"
                            colour = discord.Colour.green()

            embed = discord.Embed(
                title=title,
                description=description,
                colour=colour
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)


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
            
            description += "\n## Shop currencies:\n"
            i = 0
            for curr, amount in player.currencies.items():
                i += 1
                description += f"- {amount} {curr}\n"
            if i == 0:
                description += "This user has no shop currencies.\n"

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


    # Give item or currency to user
    @gacha.command(name="give")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def give(self, ctx: commands.Context, member: commands.MemberConverter, amount: int, *, item: str = None):
        """Gives an item or currency to a member"""

        if member.id in self.save:
            player = self.save[member.id]
        else:
            player = Player(member.id)
            self.save[member.id] = player

        if item is None:
            player.pull_currency += amount
        elif item in Data.items.keys():
            if item not in player.inventory.keys():
                player.inventory[item] = 0
            player.inventory[item] += amount
            await self.give_role(ctx, Data.items[item])
        else:
            for shp in Data.shops:
                if item.lower() == shp.currency.lower() or item == shp.currency_emoji:
                    if shp.currency_emoji not in player.currencies.keys():
                        player.currencies[shp.currency_emoji] = 0
                    player.currencies[shp.currency_emoji] += amount

        self.save_conf()

        if item is None: item = CURRENCY_NAME

        embed = discord.Embed(
            title=f"Give to {member.display_name}",
            description=f"Gave **{amount} {item}** to {member.mention}",
            colour=discord.Colour.green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Scoreboard for currency owners (debug)
    @gacha.command(name="topkek")
    async def topkek(self, ctx: commands.Context):
        """Scoreboard for currency owners (for debug purposes)"""

        topmembers = sorted(self.save.items(), key=lambda p: p[1].pull_currency, reverse=True)
        topmembers = list(filter(
            lambda i: (m := get(ctx.guild.members, id=i[0])) is not None and not m.bot,
            topmembers))
        topmembers = topmembers[:min(len(topmembers), 10)]

        description = ""
        i = 0
        for id, player in topmembers:
            i += 1
            user: discord.Member = get(ctx.guild.members, id=id)
            description += f"{i}. {user.display_name}: {player.pull_currency} {CURRENCY_NAME}s\n"

        embed = discord.Embed(
            title=f"Currency scoreboard",
            description=description.strip(),
            colour=discord.Colour.green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Items and currencies inventory
    @gacha.command(name="inventory", aliases=["items", "bag"])
    async def inventory(self, ctx: commands.Context, *, member: commands.MemberConverter = None):
        """Shows a user's inventory"""

        if member is None:
            member = ctx.author

        if member.id in self.save:
            player = self.save[member.id]

            description = "## Items:\n"
            i = 0
            for item, amount in player.inventory.items():
                i += 1
                itm = Data.items[item]
                description += f"- **{itm.name}** x{amount}\n"
            if i == 0:
                description += "This user has no items in their inventory."

            colour = discord.Colour.green()
        else:
            description = f"{member.display_name} isn't in our database. Have they ever talked??"
            colour = discord.Colour.red()

        embed = discord.Embed(
            title=f"{member.display_name}'s inventory",
            description=description,
            colour=colour
        )
        embed.set_footer(text=self.footer)
        await ctx.send(embed=embed)


    # Pull on a banner
    @gacha.command(name="pull", aliases=["single", "multi", "10pull"])
    async def pull(self, ctx: commands.Context, *, banner: str = "1"):
        """Pull on a banner (defaults to banner number 1)"""

        command = ctx.message.content.split()[1]
        bann = self.get_banner(banner)

        error_title = f"Can't do a {command}"
        MULTIS = ["10pull", "multi"]

        if bann is None:
            description = f'No banners at the time!'
            embed = discord.Embed(
                title=error_title,
                description=description.strip(),
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
            return

        if command in MULTIS:
            pull_count = 10
        else:
            pull_count = 1
        pull_cost = bann.pull_cost * pull_count

        player_id = ctx.author.id
        if player_id not in self.save.keys() or self.save[player_id].pull_currency < pull_cost:
            description = f"You don't have enough {CURRENCY_NAME}s. The cost for a {command} on this banner is **{pull_cost} {CURRENCY_NAME}{'s' if pull_cost > 1 else ''}**.\n\nTalk some more and use `?gacha balance` to check your balance!"
            embed = discord.Embed(
                title=error_title,
                description=description.strip(),
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
            return

        player = self.save[player_id]
        if player._pulling:
            description = f"You already have an ongoing pull, please be patient!"
            embed = discord.Embed(
                title=error_title,
                description=description.strip(),
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
            return

        player._pulling = True

        title = f"{ctx.author.display_name}'s {command} on {bann.name}"

        pull_results = []
        pull_results_ids = []
        mini = len(PULL_ANIM)
        for _ in range(pull_count):
            rnd = random.randint(0, bann._cumulative_weights[-1] - 1)
            for i in range(len(bann._cumulative_weights)):
                if rnd < bann._cumulative_weights[i]:
                    if i < mini:
                        mini = i
                    weight = sorted(bann.drop_weights.keys())[i]
                    item_id = random.choice(bann.drop_weights[weight])
                    pull_results_ids.append(item_id)
                    item = Data.items[item_id]
                    pull_results.append(item)
                    break

        if mini < len(PULL_ANIM):
            anim = PULL_ANIM[mini]
        else:
            anim = PULL_ANIM[-1]

        img = Image.open(os.path.join(DIR, "img", "gachabg.png"))
        if command in MULTIS:
            for i in range(pull_count):
                item = pull_results[i]
                itm = item.get_image().resize((92, 92))
                img.paste(itm, (30 * (1+(i % 5)) + 92 * (i % 5), 60 * (1+(i // 5)) + 92 * (i // 5)), itm)
        else:
            item = pull_results[0]
            itm = item.get_image().resize((160, 160))
            img.paste(itm, (240, 100), itm)

        with io.BytesIO() as f:
            img.save(f, 'PNG')
            f.seek(0)
            r = requests.post("https://api.imgbb.com/1/upload?key=97d73c9821eedce1864ef870883defdb", files={"image": f})
            j = r.json()
            pull_url = j["data"]["url"]

        colour = discord.Colour.random()
        embed = discord.Embed(
            title=title,
            colour=colour
        )
        embed.set_image(url=anim)
        embed.set_footer(text=self.footer)

        message: discord.Message = await ctx.send(embed=embed)

        await asyncio.sleep(11.5)

        embed = discord.Embed(
            title=title,
            colour=colour
        )
        embed.set_image(url=pull_url)
        embed.set_footer(text=self.footer)

        results_dict = dict([(item.name, pull_results.count(item)) for item in pull_results])
        results_str = [f"**{k} x{v}**" for k, v in results_dict.items()]

        await message.edit(embed=embed)
        await message.reply(f"{ctx.author.mention} just pulled {', '.join(results_str)}!")

        for item in pull_results:
            await self.give_role(ctx, item)

        player.pull_currency -= pull_cost

        for item_id in pull_results_ids:
            if item_id not in player.inventory:
                player.inventory[item_id] = 0

            player.inventory[item_id] += 1

        player._pulling = False


async def setup(bot):
    await bot.add_cog(Gacha(bot))
