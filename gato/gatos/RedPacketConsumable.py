from random import randint

import discord
from discord.ext import commands

from discord.ext.commands.context import Context
from discord.ui import View

from AConsumable import AConsumable


CURRENCY_EMOJI = "🌸"


class RedPacketView(View):

    message: discord.Message
    count: int
    claimed: dict[int, str]
    left: int
    owner: str

    TOTAL: int = 1000
    MAX_CLAIMS: int = 10

    def __init__(self, gatogame):
        super().__init__(timeout=86400)

        self.gatogame = gatogame
        self.count = 0
        self.left = self.TOTAL
        self.claimed = {}

    async def start(self, ctx: Context):
        self.owner = ctx.author.display_name
        embed = discord.Embed(
            title=f"{self.owner}'s Red Packet",
            description="*Nobody claimed yet.*",
            colour=discord.Colour.gold()
        )
        self.message = await ctx.send(embed=embed, view=self)

    async def on_timeout(self) -> None:
        self.stop()
        await self.message.edit(view=None)

    @discord.ui.button(style=discord.ButtonStyle.blurple, label="Claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        player_id = interaction.user.id
        if player_id in self.claimed:
            await interaction.response.send_message(embed=discord.Embed(
                title="Error",
                description="You already claimed this red packet"
            ), ephemeral=True)
        elif self.count == self.MAX_CLAIMS:
            await interaction.response.send_message(embed=discord.Embed(
                title="Error",
                description="Sorry, this red packet was already entirely claimed"
            ), ephemeral=True)
        else:
            await interaction.response.defer()

            self.count += 1
            if self.count < self.MAX_CLAIMS:
                amt = randint(1, self.left + self.count - self.MAX_CLAIMS)
            else:
                amt = self.left

            self.left -= amt

            if player_id not in self.gatogame.players:
                self.gatogame.create_player(player_id)
            player = self.gatogame.players[player_id]
            player.transactions.currency += amt

            self.claimed[player_id] = f"- {interaction.user.display_name} received {amt} {CURRENCY_EMOJI}"
            embed = discord.Embed(
                title=f"{self.owner}'s Red Packet",
                description="\n".join(self.claimed.values()),
                colour=discord.Colour.gold()
            )

            if self.count == self.MAX_CLAIMS:
                await self.message.edit(embed=embed, view=None)
            else:
                await self.message.edit(embed=embed)


class RedPacketConsumable(AConsumable):

    IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    ANIMATIONS: str = "redpacket"
    DISPLAY_NAME: str = "Red Packet"
    RARITY: int = 3

    async def consume(self, ctx: Context, gatogame, gato = None):
        await super().consume(ctx, gatogame)

        red_packet_view = RedPacketView(gatogame)
        await red_packet_view.start(ctx)
        return True
