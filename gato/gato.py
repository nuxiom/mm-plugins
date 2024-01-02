import asyncio
import json
import os
import random
import shutil
import sys

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


DIR = os.path.dirname(__file__)
SAVE_FILE = os.path.join(os.getcwd(), "currency.json")

sys.path.append(DIR)
cachepath = os.path.join(DIR, "__pycache__")
if os.path.exists(cachepath):
    shutil.rmtree(cachepath)

from gatos import GATO_CONST


class GatoGame(commands.Cog):
    """Funpost Plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.footer = ""  # TODO: REPLACE ME


    @commands.group(invoke_without_command=True)
    async def gato(self, ctx):
        """
        Ruan Mei Mains' gato gacha game!
        """

        await ctx.send_help(ctx.command)


    @gato.command(name="testmodule")
    async def testmodule(self, ctx):
        await ctx.send(f"`{GATO_CONST}`")


async def setup(bot):
    await bot.add_cog(GatoGame(bot))
