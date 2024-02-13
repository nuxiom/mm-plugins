from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable


class AvocadoToastConsumable(AConsumable):
    """> Restores 30 hunger and 30 HP"""

    # IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    # ANIMATIONS: str = "medkit"
    DISPLAY_NAME: str = "Avocado toast"
    RARITY: int = 3

    async def consume(self, ctx: Context, gatogame, gato = None):
        await super().consume(ctx, gatogame, gato)

        if gato is None:
            embed = discord.Embed(
                title = self.DISPLAY_NAME,
                description = "You need to specify a critter to use this on",
                colour = discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return False

        if gato._fainted:
            embed = discord.Embed(
                title = self.DISPLAY_NAME,
                description = "This critter has fainted, please revive it first",
                colour = discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return False

        gato.add_hunger(30)
        gato.add_health(30)

        embed = discord.Embed(
            title = self.DISPLAY_NAME,
            description = f"**30 hunger** and **30 HP** were restored to **{gato.name}**",
            colour = discord.Colour.teal()
        )
        await ctx.send(embed=embed)
        return True
