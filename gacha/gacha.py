import json
import os
import sys

import discord
from discord.ext import commands

from core.paginator import EmbedPaginatorSession

sys.path.append(os.path.dirname(__file__))
from gachalib.data import Data
from gachalib.banner import Banner


GACHA_FILE = os.path.dirname(__file__) + "/gacha.json"

COG_NAME="Gacha"


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
            bann_description = bann.get_rates_text()
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
