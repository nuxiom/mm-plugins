import asyncio

from discord.utils import find

from discord.ext.commands.context import Context

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.result = None

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

    async def consume(self, ctx: Context, gatogame, gato = None):
        await super().consume(ctx, gatogame, gato)

        self._player = gatogame.players[ctx.author.id]
        count = self._player.inventory[self.__class__.__name__]

        view = ViewGato(
            player=self._player,
            callback=self.modal_callback
        )

        message = await ctx.send(
            content=f"You have **{count} {self.DISPLAY_NAME}** left. Which critter do you want to use **{self.DISPLAY_NAME}** on?",
            view=view,
            ephemeral=True
        )

        print(self, self.result)
        while self.result is None:
            await asyncio.sleep(0.5)

        await message.delete()

        return self.result
