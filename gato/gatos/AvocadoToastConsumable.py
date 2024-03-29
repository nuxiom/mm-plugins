from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable
from ViewGato import ViewGato


class AvocadoToastConsumable(AConsumable):
    """> Restores 30 hunger and 30 HP"""

    # IMAGE: str = "UPLOAD IT TO IMGBB.COM"
    # ANIMATIONS: str = "medkit"
    DISPLAY_NAME: str = "Avocado toast"
    RARITY: int = 3

    _gato = None
    _player = None
    result = None

    async def modal_callback(self, value):
        if value:
            self.gato = find(
                lambda g: g.DISPLAY_NAME == value,
                self._player.nursery
            )
            self.gato.add_health(30)
            self.gato.add_hunger(30)
            self.result = True
        else:
            self.result = False

    async def consume(self, interaction: Interaction, gatogame, gato = None):
        await super().consume(interaction, gatogame, gato)

        self._player = gatogame.players[interaction.user.id]
        count = self._player.inventory[self.__class__.__name__]

        view = ViewGato(
            player=self._player,
            callback=self.modal_callback
        )

        await interaction.response.send_message(
            content=f"You have **{count} {self.DISPLAY_NAME}** left. Which critter do you want to use **{self.DISPLAY_NAME}** on?",
            view=view,
            ephemeral=True
        )

        while self.result is None:
            await asyncio.sleep(0.5)

        await interaction.delete_original_response()

        return self.result
