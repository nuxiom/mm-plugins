import datetime
import hashlib
import io
import json
import os
import random
import shutil
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


COG_NAME = "Currency"
DIR = os.path.dirname(__file__)
OLD_GACHA_FILE = os.path.join(os.path.expanduser("~"), "gacha.json")
SAVE_FILE = os.path.join(os.getcwd(), "currency.json")
CURRENCY_NAME = "Plum Blossom"
CURRENCY_EMOJI = "🌸"

NERFED_CHANNELS = [1106794426711408700]


def hash2(s: str):
    return hashlib.md5(s.encode()).hexdigest()


class Item():

    """ Name of the item """
    name: str

    """ Description in shop """
    description: str

    """ Icon in shop / collection """
    image: str

    """ Effects """
    effects: dict[str, list]


    def __init__(self, name: str, description: str, image: str, effects: dict[str, list] = {}) -> None:
        self.name = name
        self.description = description
        self.image = image
        self.effects = effects

    def to_dict(self):
        res = {
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "effects": self.effects
        }

        return res

    @staticmethod
    def from_dict(d: dict):
        return Item(**d)

    def get_image(self):
        return Image.open(os.path.join(DIR, "img", "items", self.image))


class Player():
    """ Player id """
    player_id: int

    """ Currency """
    currency: float

    """ Inventory (dict  item_id -> amount) """
    inventory: dict[str, int]

    """ Currency boost """
    currency_boost: float

    # Internal variables
    _last_talked: datetime.datetime
    _talked_this_minute: int
    _vc_earn_rate: float
    _time_in_vc: int # in seconds, resets daily
    _last_day_in_vc: datetime.datetime

    def __init__(self, player_id: int, currency: float = 0.0, inventory: dict = {}, currency_boost: float = 0.0, **kwargs):
        self.player_id = player_id
        self.currency = float(currency)
        self.inventory = inventory
        self.currency_boost = currency_boost

        self._last_talked = datetime.datetime.now()
        self._talked_this_minute = 0
        self._vc_earn_rate = 0
        self._time_in_vc = 3 * 60 * 60
        self._last_day_in_vc = datetime.datetime(2000, 1, 1)

    def to_dict(self):
        return {
            "player_id": self.player_id,
            "currency": self.currency,
            "inventory": self.inventory,
            "currency_boost": self.currency_boost
        }

    @staticmethod
    def from_dict(d: dict):
        return Player(**d)


class Shop():
    """ Shop name """
    name: str

    """ Items you can buy (dict  item_id -> price) """
    to_buy: dict[str, int]

    """ Items you can sell (dict  item_id -> price) """
    to_sell: dict[str, int]


    def __init__(self, name: str, to_buy: dict = {}, to_sell: dict = {}):
        self.name = name
        self.to_buy = to_buy
        self.to_sell = to_sell

    def to_dict(self):
        return {
            "name": self.name,
            "to_buy": self.to_buy,
            "to_sell": self.to_sell
        }

    @staticmethod
    def from_dict(d: dict):
        return Shop(**d)


class Data:

    items: dict[str, Item] = {}

    shops: list[Shop] = []

    with open(os.path.join(DIR, "data.json"), encoding='utf8') as f:
        o = json.load(f)

        for k, v in o["items"].items():
            items[k] = Item.from_dict(v)

        for s in o["shops"]:
            shops.append(Shop.from_dict(s))



class Currency(commands.Cog, name=COG_NAME):
    """Earn currency, spend in shops, and win roles!"""

    save: dict[int, Player]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cog_id = uuid.uuid4()

        self.save = {}
        if os.path.exists(OLD_GACHA_FILE):
            shutil.copy(OLD_GACHA_FILE, SAVE_FILE)
            os.remove(OLD_GACHA_FILE)
        if os.path.exists(SAVE_FILE):
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
                    # TODO: "upload" to Discord and retrieve URL
                    logger.warn(f"No image for shop {shop.name}-{i}")

        self.footer = ""  # TODO: added just in case we do something with it someday


    def compute_vc_currency(self, duration: int):
        # duration in seconds since last compute

        for g in self.bot.guilds:
            for vc in g.voice_channels:
                for member in vc.members:
                    if member.id not in self.save.keys():
                        self.save[member.id] = Player(member.id)
                    player = self.save[member.id]

                    mute = (member.voice.mute or member.voice.self_mute) and not member.voice.suppress
                    deaf = member.voice.deaf or member.voice.self_deaf

                    if deaf:
                        player._vc_earn_rate = 0
                    elif mute:
                        player._vc_earn_rate = 0.5
                    else:
                        player._vc_earn_rate = 0.7

                    boost = 1 + player.currency_boost
                    if any([role.id == 1145893255062495303 for role in member.roles]):
                        boost += 0.1

                    decay = max(1 - player._time_in_vc / (3*60*60), 0.3)

                    if vc.id in NERFED_CHANNELS:
                        player._vc_earn_rate = 0.005
                        decay = 1
                        boost = 1

                    earnings = 100 / 60 * duration * boost * player._vc_earn_rate * decay
                    player.currency += earnings

                    player._time_in_vc += duration


    def load_conf(self):
        with open(SAVE_FILE, "r") as f:
            save = json.load(f)

        for k, v in save.items():
            self.save[int(k)] = Player.from_dict(v)


    def save_conf(self):
        save = {}
        for k, v in self.save.items():
            save[str(k)] = v.to_dict()

        with open(SAVE_FILE, "w+") as f:
            json.dump(save, f)


    async def schedule_save(self):
        while True:
            cog: Currency = self.bot.get_cog(COG_NAME)
            if cog is None or cog.cog_id != self.cog_id:
                # We are in an old cog after update and don't have to send QOTD anymore
                break
            sleep = 2
            await asyncio.sleep(sleep)
            self.compute_vc_currency(sleep)
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
            boost = 1 + player.currency_boost
            if any([role.id == 1145893255062495303 for role in message.author.roles]):
                boost += 0.1
            
            player.currency += score * boost

            if len(message.stickers) > 0:
                player.currency += 3

            player._talked_this_minute += 1


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id not in self.save.keys():
            self.save[member.id] = Player(member.id)
        player = self.save[member.id]

        if before.channel is None and after.channel is not None:
            now = datetime.datetime.now()
            if now.date() != player._last_day_in_vc.date():
                player._time_in_vc = 0
            player._last_day_in_vc = now


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
            if item.lower() in itm.name.lower() or item.lower() in item_id.lower():
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


    # Help command
    @commands.command(name="currency", aliases=["currency_help"])
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def currency_help(self, ctx: commands.Context):
        """
        Earn currency by chatting in text or voice chat, and buy cool things with it!

        ### General commands

        `?buy|?shop(s) [item] [quantity] [shop_name]`: Buys an item in a shop.
        > Use `?shop` alone to show current shops.

        `?bal(ance)|?money [user]`: Checks how much currency you or another user have.

        `?inv(entory)|?bag|?items [user]`: Checks your or another player's inventory.

        `?item <item>`: Check infos about an item

        ### Gambling

        `?flip <heads/h/tails/t> <amount bet>`: Gamble currency by flipping a coin

        `?rps <rock/r/paper/p/scissors/s> <amount bet>`: Gamble currency at Rock Paper Scissors
        """
        await ctx.send_help(ctx.command)


    # List items to buy in shops
    @commands.command(name="buy", aliases=["shop", "shops"])
    @checks.has_permissions(PermissionLevel.REGULAR)
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
                        embed.set_footer(text="ERROR: No image for this shop. Please ping @cyxo")
                    embeds.append(embed)

            paginator = EmbedPaginatorSession(ctx, *embeds)
            await paginator.run()
        else:
            title = "Buy item"
            colour = discord.Colour.red()
            if ctx.author.id not in self.save:
                embed = discord.Embed(
                    title=title,
                    description=f"You don't have any money. Try talking a little before trying to buy, okay?",
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
                        if player.currency < total_price:
                            description = f"You don't have enough {CURRENCY_NAME}s to buy {count} {itm.name}"
                        else:
                            player.currency -= total_price
                            if item_id not in player.inventory.keys():
                                player.inventory[item_id] = 0
                            for _ in range(count):
                                player.inventory[item_id] += 1
                                for effect, args in itm.effects.items():
                                    await eval(f"Effects.{effect}")(self, ctx, *args)
                            description = f"You bought **{count} {itm.name}** for **{total_price}** {CURRENCY_EMOJI}"
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
                        if player.currency < total_price:
                            description = f"You don't have enough {CURRENCY_NAME}s to buy {count} {itm.name}"
                        else:
                            player.currency -= total_price
                            if item_id not in player.inventory.keys():
                                player.inventory[item_id] = 0
                            for _ in range(count):
                                player.inventory[item_id] += 1
                                for effect, args in itm.effects.items():
                                    await eval(f"Effects.{effect}")(self, ctx, *args)
                            description = f"You bought **{count} {itm.name}** for **{total_price}** {CURRENCY_EMOJI}"
                            colour = discord.Colour.green()

            embed = discord.Embed(
                title=title,
                description=description,
                colour=colour
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)


    @commands.command(name="sell")
    @checks.has_permissions(PermissionLevel.OWNER)
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
                            player.currency += total_price
                            description = f"You sold **{count} {itm.name}** and earned **{total_price}** {CURRENCY_EMOJI}"
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
                            player.currency += total_price
                            description = f"You sold **{count} {itm.name}** and earned **{total_price}** {CURRENCY_EMOJI}"
                            colour = discord.Colour.green()

            embed = discord.Embed(
                title=title,
                description=description,
                colour=colour
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)


    # Get player balance
    @commands.command(name="balance", aliases=["money", "bal"])
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def balance(self, ctx: commands.Context, *, member: commands.MemberConverter = None):
        """Shows a user's currency balance"""

        if member is None:
            member = ctx.author

        if member.id in self.save:
            player = self.save[member.id]
            description = f"{member.display_name} currently has {int(player.currency)} {CURRENCY_EMOJI}"
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


    # Items and currencies inventory
    @commands.command(name="inventory", aliases=["items", "bag", "inv"])
    @checks.has_permissions(PermissionLevel.REGULAR)
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


    # Give item or currency to user
    @commands.command(name="give")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def give(self, ctx: commands.Context, member: commands.MemberConverter, amount: int, *, item: str = None):
        """Gives an item or currency to a member"""

        if member.id in self.save:
            player = self.save[member.id]
        else:
            player = Player(member.id)
            self.save[member.id] = player

        if item is None:
            player.currency += amount
        elif item in Data.items.keys():
            _, itm = self.get_item(item)
            if item not in player.inventory.keys():
                player.inventory[item] = 0
            for _ in range(amount):
                player.inventory[item] += 1
                for effect, args in itm.effects.items():
                    await eval(f"Effects.{effect}")(self, ctx, *args)
        else:
            embed = discord.Embed(
                title=f"Give to {member.display_name}",
                description=f"Item {item} does not exist.",
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
            return

        self.save_conf()

        if item is None: item = CURRENCY_EMOJI

        embed = discord.Embed(
            title=f"Give to {member.display_name}",
            description=f"Gave **{amount} {item}** to {member.mention}",
            colour=discord.Colour.green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Scoreboard for currency owners (debug)
    @commands.command(name="topkek")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def topkek(self, ctx: commands.Context):
        """Scoreboard for currency owners (for debug purposes)"""

        topmembers = sorted(self.save.items(), key=lambda p: p[1].currency, reverse=True)
        topmembers = list(filter(
            lambda i: (m := get(ctx.guild.members, id=i[0])) is not None and not m.bot,
            topmembers))
        topmembers = topmembers[:min(len(topmembers), 10)]

        description = ""
        i = 0
        for id, player in topmembers:
            i += 1
            user: discord.Member = get(ctx.guild.members, id=id)
            description += f"{i}. {user.display_name}: {int(player.currency)} {CURRENCY_EMOJI}\n"

        embed = discord.Embed(
            title=f"Currency scoreboard",
            description=description.strip(),
            colour=discord.Colour.green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Display info about an item
    @commands.command(name="item")
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def item(self, ctx: commands.Context, *, item: str):
        """ Shows info about an item """

        item_id, itm = self.get_item(item)
        if itm is not None:
            description = f"## {itm.name}\n`{item_id}`\n\n"
            description += f"{itm.description}\n\n"
            description += "**Effects:**\n"
            if len(itm.effects.keys()) > 0:
                for effect in itm.effects.keys():
                    description += f"- {eval(f'Effects.{effect}').__doc__.format(*itm.effects[effect])}\n"
            else:
                description += "*No effect, this item is purely a collectible!*\n"
            if any([item_id in shop.to_buy.keys() for shop in Data.shops]):
                description += "\n**Buyable in the following shop(s):**\n"
                for shop in Data.shops:
                    if item_id in shop.to_buy.keys():
                        description += f"- {shop.name}: {shop.to_buy[item_id]} {CURRENCY_EMOJI}\n"
            embed = discord.Embed(
                title=f'Item info',
                description=description,
                colour=discord.Colour.green()
            )
            embed.set_thumbnail(url="attachment://item.png")
            embed.set_footer(text=self.footer)
            with open(os.path.join(DIR, "img", "items", itm.image), "rb") as f:
                await ctx.send(embed=embed, file=discord.File(fp=f, filename="item.png"))
        else:
            embed = discord.Embed(
                title=f'Item info',
                description=f"Item {item} not found!",
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)


    # Gamble currency in heads/tails
    @commands.command(name="flip")
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def flip(self, ctx: commands.Context, guess: str, amount: int):
        """ Gamble currency by flippîng a coin """

        heads = ["heads", "h"]
        tails = ["tails", "t"]

        player: Player = None
        if ctx.author.id in self.save.keys():
            player = self.save[ctx.author.id]

        img = None

        if guess.lower() not in heads and guess.lower() not in tails:
            description = f"Stop kidding with your `{guess}`! Guess one of these: `heads/h/tails/t`"
            colour = discord.Colour.red()
        elif player is None:
            description = "You don't have any money. Try talking a little before trying to gamble, okay?"
            colour = discord.Colour.red()
        elif amount < 0 or amount > player.currency:
            description = f"Can't bet **{amount}** {CURRENCY_EMOJI}. Try checking your balance with `?bal`"
            colour = discord.Colour.red()
        else:
            colour = discord.Colour.green()
            description = "Ruan Mei flips a coin, and it falls on... "
            rnd = random.randint(0, 10000)
            if rnd < 5000:
                description += "Heads!\n"
                if guess.lower() in heads:
                    player.currency += amount
                    description += "You won! You get double what you bet!"
                    img = "https://cdn.discordapp.com/emojis/1164689665740259369.gif"
                else:
                    player.currency -= amount
                    description += "You lost :frowning: You lost everything you bet, try again next time!"
                    img = "https://cdn.discordapp.com/emojis/1188293763718709258.webp"
            elif rnd < 10000:
                description += "Tails!\n"
                if guess.lower() in tails:
                    player.currency += amount
                    description += "You won! You get double what you bet!"
                    img = "https://cdn.discordapp.com/emojis/1164689665740259369.gif"
                else:
                    player.currency -= amount
                    description += "You lost :frowning: You lost everything you bet, try again next time!"
                    img = "https://cdn.discordapp.com/emojis/1188293763718709258.webp"
            else:
                colour = discord.Colour.gold()
                description += "its edge!\nWow, who could've guessed that?? Anyway, you get your coins back!"
                img = "https://cdn.discordapp.com/emojis/1171830972786933850.webp"
        
        embed = discord.Embed(
            title=f'Coin flip',
            description=description,
            colour=colour
        )
        if img is not None: embed.set_thumbnail(url=img)
        embed.set_footer(text=self.footer)
        await ctx.send(embed=embed)


    # Gamble currency in rock paper scissors
    @commands.command(name="rps")
    @checks.has_permissions(PermissionLevel.REGULAR)
    async def rps(self, ctx: commands.Context, move: str, amount: int):
        """ Gamble currency by playing Rock Paper Scissors """

        rock = ["rock", "r"]
        paper = ["paper", "p"]
        scissors = ["scissors", "s"]

        adjectives = ["an epic", "a grand", "a heroic", "a monumental", "an extravagant", "a bombastic", "an ambitious", "an arduous", "a huge", "an extraordinary"]
        battles = ["battle", "duel", "clash", "fight", "confrontation", "encounter", "skirmish", "contest"]

        player: Player = None
        if ctx.author.id in self.save.keys():
            player = self.save[ctx.author.id]

        img = None

        if move.lower() not in (rock+paper+scissors):
            description = f"Hey! `{move}` is not a valid move in Rock Paper Scissors! Pick one of these: `rock/r/paper/p/scissors/s`"
            colour = discord.Colour.red()
        elif player is None:
            description = "You don't have any money. Try talking a little before trying to gamble, okay?"
            colour = discord.Colour.red()
        elif amount < 0 or amount > player.currency:
            description = f"Can't bet **{amount}** {CURRENCY_EMOJI}. Try checking your balance with `?bal`"
            colour = discord.Colour.red()
        else:
            topick = [rock, paper, scissors]
            mmove = [m[0] for m in topick if move.lower() in m][0]
            rmove = random.choice(topick)[0]

            colour = discord.Colour.green()
            description = f"You pick {random.choice(adjectives)} {random.choice(battles)} of Rock Paper Scissors against Ruan Mei!\n"
            description += f"The tension is at its highest as **{amount}** {CURRENCY_EMOJI} are at stake on each side...\n\n"
            description += f"You play *{mmove}*.\n"
            description += f"She plays *{rmove}*.\n\n"
            if mmove in rock and rmove in paper \
            or mmove in paper and rmove in scissors \
            or mmove in scissors and rmove in rock:
                description += f"You crumble in tears as you lose your **{amount}** {CURRENCY_EMOJI}..."
                player.currency -= amount
                img = "https://cdn.discordapp.com/emojis/1188293763718709258.webp"
            elif mmove == rmove:
                description += f"It's a tie! Everyone gets their money back."
                img = "https://cdn.discordapp.com/emojis/1171830972786933850.webp"
            else:
                description += f"You did it! You won! You receive **{amount*2}** {CURRENCY_EMOJI} for your victory!"
                player.currency += amount
                img = "https://cdn.discordapp.com/emojis/1164689665740259369.gif"
        
        embed = discord.Embed(
            title=f'Rock Paper Scissors',
            description=description,
            colour=colour
        )
        if img is not None: embed.set_thumbnail(url=img)
        embed.set_footer(text=self.footer)
        await ctx.send(embed=embed)



class Effects:
    @staticmethod
    async def give_role(plugin: Currency, ctx: commands.Context, role_id: int):
        """ Gives you the <@&{}> Discord role """

        try:
            role = get(ctx.guild.roles, id=role_id)
            logger.info(f"{ctx.author} won role {role.name}")
            await ctx.author.add_roles(role)
            return role.name
        except:
            logger.error(f"Error while giving role {role_id} to {ctx.author}")

    @staticmethod
    async def dna_role(plugin: Currency, ctx: commands.Context, dna_role_id: int):
        """ Collect them all to get a special prize! """

        dna_list = ["adenine", "cytosine", "guanine", "thymine"]

        player = plugin.save[ctx.author.id]
        if all(dna in player.inventory.keys() for dna in dna_list):
            role_name = await Effects.give_role(plugin, ctx, dna_role_id)
            await ctx.author.send(f'Congrats! You collected all the parts to assemble Ruan Mei\'s hairpin! You received the role "{role_name}"! Please keep it a secret <a:RuanMeiAiPeace:1164689665740259369>')

    @staticmethod
    async def currency_boost(plugin: Currency, ctx: commands.Context):
        """ Boosts your currency earnings. The more you have the better!
            - 1 Currency Boost: +5%
            - 5 Currency Boost: +10%
            - 20 Currency Boost: +15%
            - 50 Currency Boost: +20%
        """
        player = plugin.save[ctx.author.id]
        if player.inventory["currencyboost"] < 5:
            player.currency_boost = 0.05
        elif player.inventory["currencyboost"] < 20:
            player.currency_boost = 0.1
        elif player.inventory["currencyboost"] < 50:
            player.currency_boost = 0.15
        else:
            player.currency_boost = 0.2



async def setup(bot):
    await bot.add_cog(Currency(bot))
