import discord
from discord.ext import commands


class MessageCounter:

    def __init__(self):
        self.message = ""
        self.count = 0
        self.users = []
        self.stickers = []


class Parrot(commands.Cog):
    """Funpost Plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.messages: dict[int, MessageCounter] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id not in self.messages:
            self.messages[message.channel.id] = MessageCounter()

        ct = self.messages[message.channel.id]
        if message.content == ct.message or (message.stickers and message.stickers[0].id == ct.stickers[0]):
            if message.author.id not in ct.users:
                ct.count += 1
                # ct.users.append(message.author.id)
        else:
            ct.message = message.content
            ct.users = [message.author.id]
            ct.count = 1
            if message.stickers is not None:
                ct.stickers = message.stickers
            else:
                ct.stickers = []

        if ct.count == 4:
            await message.channel.send(ct.message, stickers=ct.stickers)


async def setup(bot):
    await bot.add_cog(Parrot(bot))

