from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable


class MedkitConsumable(AConsumable):

    IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    ANIMATIONS: str = "medkit"
    DISPLAY_NAME: str = "Medkit"
    RARITY: int = 3

    async def consume(self, ctx: Context, gatogame):
        await super().consume(ctx, gatogame)

        # Later make a modal or something, to select the gato to use it on

        player = gatogame.players[ctx.author.id]

        for gato in player.nursery:
            gato.health = gato.max_health
            gato.mood = gato.max_mood
            gato.hunger = gato.max_hunger
            gato.energy = gato.max_energy

        await ctx.send("Your critters were fully restored! ✅")
