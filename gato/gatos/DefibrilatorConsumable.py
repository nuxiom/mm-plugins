from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable


class DefibrilatorConsumable(AConsumable):
    """> Revives an undeployed critter with 20 HP"""

    # IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    # ANIMATIONS: str = "medkit"
    DISPLAY_NAME: str = "Defibrilator"
    RARITY: int = 3

    async def consume(self, ctx: Context, gatogame, gato = None):
        await super().consume(ctx, gatogame, gato)

        player = gatogame.players[ctx.author.id]
        if gato is None:
            embed = discord.Embed(
                title = "Defibrilator",
                description = "You need to specify a critter to use this on",
                colour = discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return False

        tm = player.deployed_team
        if tm is not None and tm.deployed_at is not None and gato in tm.gatos:
            embed = discord.Embed(
                title = "Defibrilator",
                description = "This critter is currently deployed. Please recall it using `/critter recall` first",
                colour = discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return False

        if not gato._fainted:
            embed = discord.Embed(
                title = "Defibrilator",
                description = "This critter has not fainted, so it can't be revived",
                colour = discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return False

        gato._fainted = False
        gato.add_health(20)

        embed = discord.Embed(
            title = "Defibrilator",
            description = f"**{gato.name}** was revived with **20 HP**",
            colour = discord.Colour.teal()
        )
        await ctx.send(embed=embed)
        return True
