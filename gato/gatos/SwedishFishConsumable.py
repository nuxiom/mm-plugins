from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable
from EfficiencyFoodEq import EfficiencyFoodEq
from SwedeGato import SwedeGato


class SwedishFishConsumable(AConsumable):
    """> Restores 30 hunger and increases efficiency by 10% for 1 hour. ⚠️ Efficiency food buffs don't stack!"""

    IMAGE: str = "https://media.discordapp.net/attachments/1106794389759598662/1181130462874312714/image0.png"
    # ANIMATIONS: str = "medkit"
    DISPLAY_NAME: str = "Swedish Fish"
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

        for eq in gato.equipments:
            if eq.DISPLAY_NAME == EfficiencyFoodEq.DISPLAY_NAME:
                embed = discord.Embed(
                    title = self.DISPLAY_NAME,
                    description = "This critter already has an efficiency food buff!",
                    colour = discord.Colour.red()
                )
                await ctx.send(embed=embed)
                return False


        gato.add_hunger(30)
        gato.equipments.append(EfficiencyFoodEq())


        # Handle favorite food
        fav_food = ""
        if gato.DISPLAY_NAME == SwedeGato.DISPLAY_NAME:
            gato.add_mood(20)
            gato.add_hunger(20)
            fav_food = f". It's its favorite food! **{gato.name}** additionally restored **20 mood** and **20 hunger**"

        embed = discord.Embed(
            title = self.DISPLAY_NAME,
            description = f"**30 hunger** were restored to **{gato.name}** and its efficiency will be increased by 10% for 1 hour" + fav_food,
            colour = discord.Colour.teal()
        )
        await ctx.send(embed=embed)
        return True
