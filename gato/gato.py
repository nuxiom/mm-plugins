import asyncio
import importlib
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
import gatos
importlib.reload(gatos)


class GatoGame(commands.Cog):
    """Gato gacha game plugin"""

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
        eg = gatos.ExampleGato()
        j = eg.to_json()
        sg = gatos.StrongGato.from_json(j)
        eg.affect_health(40)
        sg.affect_health(40)
        await ctx.send(f"```\n{eg.to_json()}\n{sg.to_json()}\n```")



async def setup(bot):
    await bot.add_cog(GatoGame(bot))
