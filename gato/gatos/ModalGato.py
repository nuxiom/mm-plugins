import traceback

import discord
from discord.ext import commands

from discord import Interaction, SelectOption
from discord.ui import Modal, Select
from discord.utils import MISSING


class ModalGato(Modal):

    gato = Select(
        placeholder = "Select a critter to use this on",
        options = []
    )

    def __init__(self, player, description, callback, title: str = "Select a critter", timeout: float | None = None, custom_id: str = ...) -> None:
        self.gato = Select(
            placeholder = description,
            options = [
                SelectOption(
                    label=g.name,
                    description=f"{g.health} ❤️ | {g.hunger} 🍗 | {g.energy} ⚡ | {g.mood} 🌞",
                    value=g.DISPLAY_NAME
                )
                for g in player.nursery
            ]
        )
        self.callback = callback
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.callback(self.gato.values[0])

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.defer()
        await self.callback(None)
        traceback.print_exception(type(error), error, error.__traceback__)

    async def on_timeout(self) -> None:
        await self.callback(None)

