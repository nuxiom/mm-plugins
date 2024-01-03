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
CURRENCY_NAME = "Plum Blossom"
CURRENCY_EMOJI = "🌸"

sys.path.append(DIR)
import gatos
importlib.reload(gatos)


class GatoGame(commands.Cog):
    """Gato gacha game plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.footer = ""  # TODO: REPLACE ME

        self.nurseries: dict[int, list[gatos.Gato]] = {
            200282032771694593: [gatos.ExampleGato(name="Cyxo's critter")]
        }


    @commands.group(invoke_without_command=True)
    async def gato(self, ctx):
        """
        Ruan Mei Mains' gato gacha game!
        """

        await ctx.send_help(ctx.command)


    @gato.command(name="pull")
    async def pull(self, ctx, *, gato_name: str = None):
        if ctx.author.id not in self.nurseries:
            self.nurseries[ctx.author.id] = []
        
        nursery = self.nurseries[ctx.author.id]

        pulled = "ExampleGato"

        gato: gatos.Gato = None
        for cat in nursery:
            if cat.__class__.__name__ == pulled:
                gato = cat
                break
        
        if gato is None:
            if gato_name is None:
                gato_name = f"{ctx.author.name}'s critter"

            gato = eval(f"gatos.{pulled}")(name=gato_name)
            nursery.append(gato)
            embed = discord.Embed(
                title="Pull",
                colour=discord.Colour.teal(),
                description=f"{ctx.author.mention} you just obtained a **{pulled}** named **{gato_name}** !!"
            )
            await ctx.send(embed=embed)
        elif gato.eidolon < 6:
            gato.eidolon += 1
            embed = discord.Embed(
                title="Pull",
                colour=discord.Colour.gold(),
                description=f"{ctx.author.mention} you just obtained a **{pulled}** !! **{gato.name}**'s Eidolon level increased to **{gato.eidolon}**!"
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Pull",
                colour=discord.Colour.teal(),
                description=f"{ctx.author.mention} your **{gato.name}** is already at Eidolon level 6! You got **666** {CURRENCY_EMOJI} as a compensation!"
            )
            await ctx.send(embed=embed)


    @gato.command(name="nursery")
    async def nursery(self, ctx):
        description = ""
        colour = discord.Colour.green()
        if ctx.author.id in self.nurseries or len(self.nurseries[ctx.author.id]) == 0:
            for i, gato in enumerate(self.nurseries[ctx.author.id]):
                description += f"{i+1}. {gato.name}: {gato.__class__.__name__} (E{gato.eidolon})"
        else:
            description = "You have no gatos silly goose ! Use `?gato pull (name of the gato)`"
            colour = discord.Colour.red()
        
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s nursery",
            description=description,
            colour=colour
        )
        await ctx.send(embed=embed)


    @gato.command(name="info")
    async def info(self, ctx, number: int):
        if ctx.author.id in self.nurseries or len(self.nurseries[ctx.author.id]) == 0:
            nursery = self.nurseries[ctx.author.id]
            number -= 1

            if number < 0 or number >= len(nursery):
                embed = discord.Embed(
                    title=f"Error",
                    description=f"Gato number {number + 1} not found. Use `?gato nursery`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
            else:
                gato = nursery[number]
                desc = gato.__doc__.format(eidolon=gato.eidolon)

                description = f"{desc}\n" + \
                f"Health: {round(gato.health)}\n" + \
                f"Hunger: {round(gato.hunger)}\n" + \
                f"Mood: {round(gato.mood)}\n" + \
                f"Hunger: {round(gato.hunger)}\n" + \
                f"\n✨ **Eidolon {gato.eidolon}**"

                embed = discord.Embed(
                    title=gato.name,
                    description=description,
                    colour=discord.Colour.teal()
                )
                embed.set_thumbnail(url=gato.image)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s nursery",
                description="You have no gatos silly goose ! Use `?pull (name of the gato)`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(GatoGame(bot))
