from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable


class TrashConsumable(AConsumable):

    IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    ANIMATIONS: str = "trash"
    DISPLAY_NAME: str = "Trash"
    RARITY: int = 3

    async def consume(self, ctx: Context, gatogame, gato = None):
        await super().consume(ctx, gatogame)

        # Later make a modal or something, to select the gato to use it on

        player = gatogame.players[ctx.author.id]

        for gato in player.nursery:
            gato.health = 1
            gato.mood = 1
            gato.hunger = 1
            gato.energy = 1

        await ctx.send("Your critters lost all their stats! ✅")
