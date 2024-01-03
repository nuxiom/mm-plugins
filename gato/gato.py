import asyncio
import importlib
import json
import os
import random
import sys
from datetime import datetime, timedelta
from functools import reduce

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

sys.path.append(os.path.dirname(__file__))
import gatos
importlib.reload(gatos)
import team
importlib.reload(team)


DIR = os.path.dirname(__file__)
SAVE_FILE = os.path.join(os.getcwd(), "currency.json")
CURRENCY_NAME = "Plum Blossom"
CURRENCY_EMOJI = "🌸"


class GatoGame(commands.Cog):
    """Gato gacha game plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.footer = ""  # TODO: REPLACE ME

        self.nurseries: dict[int, list[gatos.Gato]] = {
            200282032771694593: [gatos.ExampleGato(name="Cyxo's critter")]
        }

        self.teams: dict[int, team.Team] = {}


    @commands.group(invoke_without_command=True)
    async def gato(self, ctx: commands.Context):
        """
        Ruan Mei Mains' gato gacha game!
        """

        await ctx.send_help(ctx.command)


    def handle_events(self, user_id: int, team: list[gatos.Gato]):
        description = ""

        for gato in team:
            for event in gato._events:
                description += f"- **{gato.name}** "

                args = {}
                if "bitten" in event:
                    rnd = random.randint(100, 500)
                    args["amount"] = rnd
                    args["currency"] = CURRENCY_EMOJI
                elif "find" in event:
                    args["object_name"] = event['find']

                description += gato.EVENT_DESCRIPTIONS[list(event.keys())[0]].format(**args)
                description += "\n"

        return description


    @gato.command(name="pull")
    async def pull(self, ctx: commands.Context, *, gato_name: str = None):
        if ctx.author.id not in self.nurseries:
            self.nurseries[ctx.author.id] = []

        nursery = self.nurseries[ctx.author.id]

        pulled = random.choice(["ExampleGato", "NormalGato"])

        gato: gatos.Gato = None
        for cat in nursery:
            if cat.__class__.__name__ == pulled:
                gato = cat
                break

        if gato is None:
            if gato_name is None:
                gato_name = f"{ctx.author.name}'s {pulled}"

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
    async def nursery(self, ctx: commands.Context):
        description = ""
        colour = discord.Colour.teal()
        if ctx.author.id in self.nurseries or len(self.nurseries[ctx.author.id]) == 0:
            for i, gato in enumerate(self.nurseries[ctx.author.id]):
                description += f"{i+1}. **{gato.name}**: {gato.__class__.__name__} *(✨ E{gato.eidolon})*\n"
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
    async def info(self, ctx: commands.Context, number: int):
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
                f"**Health:** {round(gato.health)} / {round(gato.max_health)}\n" + \
                f"**Hunger:** {round(gato.hunger)} / {round(gato.max_hunger)}\n" + \
                f"**Mood:** {round(gato.mood)} / {round(gato.max_mood)}\n" + \
                f"**Energy:** {round(gato.energy)} / {round(gato.max_energy)}\n" + \
                f"\n✨ **Eidolon {gato.eidolon}**"

                embed = discord.Embed(
                    title=gato.name,
                    description=description,
                    colour=discord.Colour.teal()
                )
                embed.set_thumbnail(url=gato.IMAGE)
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s nursery",
                description="You have no gatos silly goose ! Use `?gato pull (name of the gato)`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)


    @gato.command(name="deploy")
    async def deploy(self, ctx: commands.Context, *gato_numbers):
        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no gatos silly goose ! Use `?gato pull (name of the gato)`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        nursery = self.nurseries[ctx.author.id]

        if len(gato_numbers) == 0:
            if ctx.author.id in self.teams:
                tm = self.teams[ctx.author.id]
                if tm.deployed_at is not None:
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description="A team is already deployed! Use `?gato claim` to see what they fetched for you!",
                        colour=discord.Colour.red()
                    )
                    await ctx.send(embed=embed)
                else:
                    tm.deployed_at = datetime.now()
                    for gato in tm.gatos:
                        gato.deploy()
                    gato_names = "**, **".join([gato.name for gato in tm.gatos])
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description=f"A team with **{gato_names}** has been deployed! Check back in a while with `?gato claim` to see what they fetched for you!",
                        colour=discord.Colour.teal()
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Deploy team",
                    description="No team was previously deployed! Example use `?gato deploy 1 2 3 4` (check gato numbers with `?gato nursery`)",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
        else:
            if ctx.author.id in self.teams and self.teams[ctx.author.id].deployed_at is not None:
                embed = discord.Embed(
                    title=f"Deploy team",
                    description="A team is already deployed! Use `?gato claim` to see what they fetched for you!",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
                return

            # Get unique numbers
            gato_numbers = reduce(lambda re, x: re+[x] if x not in re else re, gato_numbers, [])
            legatos: list[gatos.Gato] = []
            for i in gato_numbers[:4]:
                if not i.isnumeric():
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description=f"{i} is not a valid number! Example usage: `?gato deploy 1 2 3 4`!",
                        colour=discord.Colour.red()
                    )
                    await ctx.send(embed=embed)
                    return
                number = int(i)-1
                if number >= 0 and number < len(nursery):
                    legatos.append(nursery[number])
                else:
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description=f"Gato number {i} not found in your nursery! Check gato numbers with `?gato nursery`!",
                        colour=discord.Colour.red()
                    )
                    await ctx.send(embed=embed)
                    return

            tm = team.Team(legatos)
            self.teams[ctx.author.id] = tm
            for gato in tm.gatos:
                gato.deploy()

            gato_names = "**, **".join([gato.name for gato in legatos])
            embed = discord.Embed(
                title=f"Deploy team",
                description=f"A team with **{gato_names}** has been deployed! Check back in a while with `?gato claim` to see what they fetched for you!",
                colour=discord.Colour.teal()
            )
            await ctx.send(embed=embed)
            return


    @gato.command(name="claim")
    async def claim(self, ctx: commands.Context):
        if not ctx.author.id in self.teams or self.teams[ctx.author.id].deployed_at is None:
            embed = discord.Embed(
                title=f"Claim rewards",
                description="No team has been deployed! Check `?gato deploy` to deploy one first!",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        tm = self.teams[ctx.author.id]
        now = datetime.now()
        delta = int((now - tm.deployed_at).total_seconds())
        tm.deployed_at = None

        TIME_STEP = 1
        currency = 0
        objects = []
        for _ in range(0, delta, TIME_STEP):
            for gato in tm.gatos:
                c, o = gato.simulate(tm.gatos, TIME_STEP)
                currency += c
                objects += o

        events = self.handle_events(ctx.author.id, tm.gatos)
        if len(events) == 0:
            events = "*Nothing specific happened*"
        obj = '**, **'.join(set([f"{objects.count(o)}x {o}" for o in objects]))

        embed = discord.Embed(
            title=f"Claim rewards",
            description=f"### Expedition results\nYour gatos brought back {int(currency)} {CURRENCY_EMOJI} and {obj}\n### Event log\n{events}",
            colour=discord.Colour.teal()
        )
        await ctx.send(embed=embed)


    @gato.command(name="nanook")
    async def nanook(self, ctx: commands.Context):
        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no gatos silly goose ! Use `?gato pull (name of the gato)`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        for gato in self.nurseries[ctx.author.id]:
            gato.health = 1
            gato.mood = 1
            gato.hunger = 1
            gato.energy = 1

        await ctx.send("Done! ✅")


    @gato.command(name="yaoshi")
    async def yaoshi(self, ctx: commands.Context):
        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no gatos silly goose ! Use `?gato pull (name of the gato)`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        for gato in self.nurseries[ctx.author.id]:
            gato.health = gato.max_health
            gato.mood = gato.max_mood
            gato.hunger = gato.max_hunger
            gato.energy = gato.max_energy

        await ctx.send("Done! ✅")


    @gato.command(name="fastforward", aliases=["ff"])
    async def ff(self, ctx: commands.Context, seconds: int):
        if not ctx.author.id in self.teams or self.teams[ctx.author.id].deployed_at is None:
            embed = discord.Embed(
                title=f"Claim rewards",
                description="No team has been deployed! Check `?gato deploy` to deploy one first!",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        tm = self.teams[ctx.author.id]
        tm.deployed_at -= timedelta(seconds=seconds)

        await ctx.send("Done! ✅")



async def setup(bot):
    await bot.add_cog(GatoGame(bot))
