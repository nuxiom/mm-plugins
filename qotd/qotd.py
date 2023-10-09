import json
import os

import aiocron
import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel


QUOTES_FILE = os.path.dirname(__file__) + "/qotd.json"


class QOTD(commands.Cog):
    """Manages quote of the day and sends them periodically."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if os.path.exists(QUOTES_FILE):
            with open(QUOTES_FILE, "r") as f:
                self.conf = json.load(f)
        else:
            self.conf = {
                "quotes": [],
                "time": "0 8 * * *",
                "channel": None
            }

        self.quotes: list = self.conf["quotes"]
        self.time: str = self.conf["time"]
        self.channel_id: int = self.conf["channel"]

        # TODO: init crontab here
        self.cron = aiocron.crontab(self.time, func=self.send_quote)

        self.footer = ""  # TODO: added just in case we do something with it someday


    def save_conf(self):
        self.conf = {
            "quotes": self.quotes,
            "time": self.time,
            "channel": self.channel_id
        }

        with open(QUOTES_FILE, "w+") as f:
            json.dump(self.conf, f)


    async def send_quote(self):
        if self.channel_id is not None:
            channel: discord.TextChannel = self.bot.get_channel(self.channel_id)

            if channel is None:
                # TODO: send message to admins channel
                return

            quote = self.quotes.pop(0)
            self.save_conf()

            await channel.send(content=quote) # TODO: make embed


    # TODO: merge all qotd commands in one?


    # Add quote of the day
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command(aliases=['qotdadd'])
    async def add_qotd(self, ctx: commands.Context, quote: str):
        """Adds a quote of the day and saves it"""

        if quote is not None and len(quote) > 0:
            self.quotes.append(quote)
            self.save_conf()

            description = f'Quote "{quote}" added '
            emote = discord.utils.get(ctx.guild.emojis, id=1160566321306673233)
            colour = discord.Colour.dark_green
        else:
            description = f"Quote can't be empty "
            emote = discord.utils.get(ctx.guild.emojis, id=1160588883516473464)
            colour = discord.Colour.red

        embed = discord.Embed(
            title="New quote",
            description=description + emote,
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # List quotes of the day
    @checks.has_permissions(PermissionLevel.MODERATOR)
    @commands.command(aliases=['qotdlist'])
    async def list_qotd(self, ctx: commands.Context):
        """Lists upcoming quotes of the day"""

        description = ""
        for index, quote in enumerate(self.quotes):
            description += str(index + 1) + ". "
            description += quote
            description += "\n"

        embed = discord.Embed(
            title="Upcoming quotes of the day",
            description=description.strip(),
            colour=discord.Colour.dark_green
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Remove a quote of the day
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command(aliases=['qotdrm'])
    async def remove_qotd(self, ctx: commands.Context, number: int):
        """Removes a quote (use `?qotdlist` to find the number)"""

        if number > 0 and number <= len(self.quotes):
            idx = number - 1
            quote = self.quotes.pop(number)
            self.save_conf()

            description = f'Quote "{quote}" removed '
            emote = discord.utils.get(ctx.guild.emojis, id=1153489300051202198)
            colour = discord.Colour.dark_green
        else:
            description = f"Quote number {number} doesn't exist "
            emote = discord.utils.get(ctx.guild.emojis, id=1156319608630935584)
            colour = discord.Colour.red

        embed = discord.Embed(
            title="Remove quote",
            description=description + emote,
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the schedule for qotd
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command(aliases=['qotdtime'])
    async def set_qotd_time(self, ctx: commands.Context, cron: str):
        """Sets the cron time to send the quote (UTC)"""

        if aiocron.croniter.is_valid(cron):
            self.time = cron
            self.save_conf()

            # TODO: reschedule
            self.cron.stop()
            self.cron = aiocron.crontab(self.time, func=self.send_quote)

            description = f'Quotes scheduled to `{cron}`! '
            emote = discord.utils.get(ctx.guild.emojis, id=1154897211235258390)
            colour = discord.Colour.dark_green
        else:
            description = f"`{cron}` is an invalid cron format. You may want to check [Crontab Guru](https://crontab.guru/) "
            emote = discord.utils.get(ctx.guild.emojis, id=1157943933683384382)
            colour = discord.Colour.red

        embed = discord.Embed(
            title="Update quote schedule",
            description=description + emote,
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the channel for qotd
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.command(aliases=['qotdchannel'])
    async def set_qotd_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter = None):
        """Sets the channel to send the quotes to"""

        if channel is None:
            channel = ctx.channel

        self.channel_id = channel.id
        self.save_conf()

        description = f'Quotes will be sent in {channel.mention}! '
        emote = discord.utils.get(ctx.guild.emojis, id=1154671375970209852)

        embed = discord.Embed(
            title="Update channel",
            description=description + emote,
            colour=discord.Colour.dark_green
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)