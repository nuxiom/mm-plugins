import json
import os
import sys

import discord
from discord.ext import commands

from core.paginator import EmbedPaginatorSession

sys.path.append(os.path.dirname(__file__))
from data import Data
from banner import Banner


GACHA_FILE = os.path.dirname(__file__) + "/gacha.json"

COG_NAME="Gacha"


class Gacha(commands.Cog, name=COG_NAME):
    """Earn currency, gacha-it, and win roles!"""

    save: dict

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        if os.path.exists(GACHA_FILE):
            self.load_conf()
        else:
            self.save = {}

        self.footer = ""  # TODO: added just in case we do something with it someday


    def load_conf(self):
        with open(GACHA_FILE, "r") as f:
            self.save = json.load(f)


    def save_conf(self):
        with open(GACHA_FILE, "w+") as f:
            json.dump(self.save, f)


    @commands.group(invoke_without_command=True)
    async def gacha(self, ctx):
        """
        Ruan Mei Mains' gacha system!
        """

        await ctx.send_help(ctx.command)


    # Get gacha drop rates
    @gacha.command(name="details", aliases=["rates"])
    async def add_qotd(self, ctx: commands.Context, *, banner: str = None):
        """Display gacha drop rates for current banner"""

        bann: Banner = None
        if banner is None:
            if len(Data.banners) == 1:
                bann = Data.banners[0]
        else:
            if banner.isnumeric() and int(banner) > 0 and int(banner) <= len(Data.banners):
                bann = Data.banners[int(banner) - 1]
            else:
                for b in Data.banners:
                    if b.name == banner:
                        bann = b
                        break

        if bann is None:
            description = f'Banner "{banner}" not found!'
            colour = discord.Colour.red
        else:
            bann_description = bann.get_rates_text()
            description = f"# {bann.name}\n\n{bann_description}"


        embed = discord.Embed(
            title="Banner details",
            description=f"{description}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # List questions of the day
    @commands.has_role("QOTD Manager")
    @gacha.command(name="list")
    async def list_qotd(self, ctx: commands.Context):
        """Lists upcoming questions of the day"""

        embeds = []
        description = ""
        for index, question in enumerate(self.questions):
            description += str(index + 1) + ". "
            description += question["title"]
            description += "\n"

            if index % 5 == 4 or index == len(self.questions) - 1:
                embed = discord.Embed(
                    title="Upcoming questions of the day",
                    description=description.strip(),
                    colour=discord.Colour.dark_green()
                )
                embed.set_footer(text=self.footer)
                embeds.append(embed)
                description = ""
        
        if len(embeds) == 0:
            description = "*No upcoming questions* :frowning:"
            embed = discord.Embed(
                title="Upcoming questions of the day",
                description=description.strip(),
                colour=discord.Colour.dark_green()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
        else:
            paginator = EmbedPaginatorSession(ctx, *embeds)
            await paginator.run()


    # Remove a question of the day
    @commands.has_role("QOTD Manager")
    @qotd.command(name="remove", aliases=['delete', 'del', 'rm'])
    async def remove_qotd(self, ctx: commands.Context, number: int):
        """Removes a question (use `?qotd list` to find the number)"""

        if number > 0 and number <= len(self.questions):
            idx = number - 1
            question = self.questions.pop(idx)
            self.save_conf()

            description = f'Question "{question["title"]}" removed '
            emote = discord.utils.get(ctx.guild.emojis, id=1153489300051202198)
            colour = discord.Colour.dark_green()
        else:
            description = f"Question number {number} doesn't exist "
            emote = discord.utils.get(ctx.guild.emojis, id=1156319608630935584)
            colour = discord.Colour.red()

        embed = discord.Embed(
            title="Remove question",
            description=f"{description}{emote}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Edit question of the day
    @commands.has_role("QOTD Manager")
    @qotd.command(name="edit")
    async def edit_qotd(self, ctx: commands.Context, number: int, title: str = None, *options: str):
        """Edits a question. Use `?qotd edit number` to show the command used to create the question."""

        if number > 0 and number <= len(self.questions):
            idx = number - 1

            if title is not None:
                if len(options) <= len(QOTD_REACT_EMOTES):
                    question = {
                        "title": title,
                        "options": list(options)
                    }

                    self.questions[idx] = question
                    self.save_conf()

                    description = f'Question "{question["title"]}" edited '
                    emote = discord.utils.get(ctx.guild.emojis, id=1153489300051202198)
                    colour = discord.Colour.dark_green()
                else:
                    description = f"Max {len(QOTD_REACT_EMOTES)} options! "
                    emote = discord.utils.get(ctx.guild.emojis, id=1160588883516473464)
                    colour = discord.Colour.red()
            else:
                question = self.questions[idx]

                description = f"Here is the command used:\n\n```?qotd edit {number} \"{question['title']}\" {' '.join([chr(34) + option + chr(34) for option in question['options']])}```"
                emote = ""
                colour = discord.Colour.dark_green()
        else:
            description = f"Question number {number} doesn't exist "
            emote = discord.utils.get(ctx.guild.emojis, id=1156319608630935584)
            colour = discord.Colour.red()

        embed = discord.Embed(
            title="Edit question",
            description=f"{description}{emote}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Move a question of the day
    @commands.has_role("QOTD Manager")
    @qotd.command(name="move")
    async def move_qotd(self, ctx: commands.Context, number: int, position: int):
        """Moves a question to the specified position"""

        if number > 0 and number <= len(self.questions):
            if position > 0 and position <= len(self.questions):
                idx = number - 1
                new_idx = position - 1
                question = self.questions.pop(idx)
                self.questions.insert(new_idx, question)
                self.save_conf()

                description = f'Question "{question["title"]}" moved to position {position} '
                emote = discord.utils.get(ctx.guild.emojis, id=1153489300051202198)
                colour = discord.Colour.dark_green()
            else:
                description = f"{position} is not a valid position "
                emote = discord.utils.get(ctx.guild.emojis, id=1156319608630935584)
                colour = discord.Colour.red()
        else:
            description = f"Question number {number} doesn't exist "
            emote = discord.utils.get(ctx.guild.emojis, id=1156319608630935584)
            colour = discord.Colour.red()

        embed = discord.Embed(
            title="Remove question",
            description=f"{description}{emote}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the schedule for qotd
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_time", aliases=['set_schedule'])
    async def set_qotd_time(self, ctx: commands.Context, *, cron: str):
        """Sets the cron time to send the question"""

        if aiocron.croniter.is_valid(cron):
            self.time = cron
            self.save_conf()

            self.cron.stop()
            self.cron = aiocron.crontab(self.time, func=self.send_question)

            base = datetime.now()
            iter = aiocron.croniter(self.time, base)
            ts = int(iter.get_next(datetime).timestamp())
            description = f'Questions scheduled to `{cron}`! Next question will be sent on <t:{ts}:f> '
            emote = discord.utils.get(ctx.guild.emojis, id=1154897211235258390)
            colour = discord.Colour.dark_green()
        else:
            description = f"`{cron}` is an invalid cron format. You may want to check [Crontab Guru](https://crontab.guru/) "
            emote = discord.utils.get(ctx.guild.emojis, id=1157943933683384382)
            colour = discord.Colour.red()

        embed = discord.Embed(
            title="Update questions schedule",
            description=f"{description}{emote}",
            colour=colour
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the channel for qotd
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_channel")
    async def set_qotd_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter = None):
        """Sets the channel to send the questions to (here if none specified)"""

        if channel is None:
            channel = ctx.channel

        self.channel_id = channel.id
        self.save_conf()

        description = f'Questions will be sent in {channel.mention}! '
        emote = discord.utils.get(ctx.guild.emojis, id=1154671375970209852)

        embed = discord.Embed(
            title="Update channel",
            description=f"{description}{emote}",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the channel for qotd admin info
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_react_channel")
    async def set_qotd_react_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter = None):
        """Sets the channel to where people can discuss (here if none specified)"""

        if channel is None:
            channel = ctx.channel

        self.react_channel_id = channel.id
        self.save_conf()

        description = f'People will be told to discuss in {channel.mention}! '
        emote = discord.utils.get(ctx.guild.emojis, id=1155737942506078278)

        embed = discord.Embed(
            title="Update react channel",
            description=f"{description}{emote}",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the role to mention for qotd
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_ping_role")
    async def set_qotd_ping_role(self, ctx: commands.Context, role: commands.RoleConverter = None):
        """Sets the role to ping for QOTD (disable it if none specified)"""

        emote = discord.utils.get(ctx.guild.emojis, id=1147153985275437056)

        if role is not None:
            self.ping_role_id = role.id
            description = f'Will ping {role.mention} for QOTD '
        else:
            self.ping_role_id = None
            description = f'No role will be pinged for QOTD '

        self.save_conf()

        embed = discord.Embed(
            title="Update ping role",
            description=f"{description}{emote}",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the channel for qotd admin info
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_admin_channel")
    async def set_qotd_admin_channel(self, ctx: commands.Context, channel: commands.TextChannelConverter = None):
        """Sets the channel to send admin info to (here if none specified)"""

        if channel is None:
            channel = ctx.channel

        self.admin_channel_id = channel.id
        self.save_conf()

        description = f'Admin info will be sent in {channel.mention}! '
        emote = discord.utils.get(ctx.guild.emojis, id=1155737942506078278)

        embed = discord.Embed(
            title="Update admin channel",
            description=f"{description}{emote}",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the admin role to mention for info 
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_admin_role")
    async def set_qotd_admin_role(self, ctx: commands.Context, role: commands.RoleConverter = None):
        """Sets the role to ping for admin info (disable it if none specified)"""

        emote = discord.utils.get(ctx.guild.emojis, id=1147153985275437056)

        if role is not None:
            self.admin_role_id = role.id
            description = f'Will ping {role.mention} for admin news '
        else:
            self.admin_role_id = None
            description = f'No role will be pinged for admin news '

        self.save_conf()

        embed = discord.Embed(
            title="Update admin role",
            description=f"{description}{emote}",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Set the channel for qotd
    @commands.has_role("QOTD Manager")
    @qotd.command(name="set_threshold")
    async def set_qotd_warning_threshold(self, ctx: commands.Context, threshold: int):
        """Sets the number of questions at which it starts to warn admins about low questions count"""

        self.warning_threshold = threshold
        self.save_conf()

        description = f"Admins will be warned when there's less than {threshold} questions left "
        emote = discord.utils.get(ctx.guild.emojis, id=1157946531773681704)

        embed = discord.Embed(
            title="Update threshold",
            description=f"{description}{emote}",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        await ctx.send(embed=embed)


    # Show bot configuration
    @commands.has_role("QOTD Manager")
    @qotd.command(name="conf")
    async def qotd_conf(self, ctx: commands.Context):
        """Shows the QOTD configuration"""

        base = datetime.now()
        iter = aiocron.croniter(self.time, base)
        ts = int(iter.get_next(datetime).timestamp())
        time_desc = f"The question of the day cron schedule is `{self.time}`.\nWhich means the next question will be posted on <t:{ts}:f>."

        if self.channel_id is not None:
            channel = self.bot.get_channel(self.channel_id)
            qotd_channel_desc = f"Questions will be sent to {channel.mention}."
        else:
            qotd_channel_desc = f":warning: **No QOTD channel configured !** Use `?qotd set_channel <channel>`."

        if self.react_channel_id is not None:
            react_channel = self.bot.get_channel(self.react_channel_id)
            react_channel_desc = f"People will be told to discuss in {react_channel.mention}."
        else:
            react_channel_desc = f"No discussion channel configured."

        ping_role = None
        if self.ping_role_id is not None:
            ping_role = ctx.guild.get_role(self.ping_role_id).mention
        if ping_role is not None:
            ping_role_desc = f"{ping_role} will be pinged when sending QOTD."
        else:
            ping_role_desc = "No role will be pinged."

        if self.admin_channel_id is not None:
            admin_channel = self.bot.get_channel(self.admin_channel_id)
            if admin_channel is not None:
                admin_channel_desc = f"Admin warnings will be sent to {admin_channel.mention}."

                role = None
                if self.admin_role_id is not None:
                    role = admin_channel.guild.get_role(self.admin_role_id).mention

                if role is not None:
                    admin_role_desc = f"{role} will be pinged for admin warnings."
                else:
                    admin_role_desc = "No role will be pinged."

                threshold_desc = f"Admins will be pinged if there's {self.warning_threshold} questions or less queued."
            else:
                admin_channel_desc = "Invalid admin channel setup."
                admin_role_desc = "Invalid admin channel setup."
                threshold_desc = "Invalid admin channel setup."
        else:
                admin_channel_desc = "No admin channel setup."
                admin_role_desc = "No admin channel setup."
                threshold_desc = "No admin channel setup."


        embed = discord.Embed(
            title="QOTD configuration",
            colour=discord.Colour.dark_green()
        )
        embed.set_footer(text=self.footer)

        embed.add_field(name="Questions", value=f"There are currently {len(self.questions)} questions queued.")
        embed.add_field(name="Schedule", value=time_desc)
        embed.add_field(name="QOTD channel", value=qotd_channel_desc)
        embed.add_field(name="React channel", value=react_channel_desc)
        embed.add_field(name="Ping role", value=ping_role_desc)
        embed.add_field(name="Admin channel", value=admin_channel_desc)
        embed.add_field(name="Admin role", value=admin_role_desc)
        embed.add_field(name="Warning threshold", value=threshold_desc)

        await ctx.send(embed=embed)


    # Set the role to mention for qotd
    @commands.has_role("QOTD Manager")
    @qotd.command(name="preview")
    async def preview_qotd(self, ctx: commands.Context, number: int = None):
        """Previews a question of the day"""

        if number is None:
            number = len(self.questions)

        if number > 0 and number <= len(self.questions):
            idx = number - 1
            question = self.questions[idx]

            react_emotes, embed = self.make_question(question, ctx.guild)
            embed.set_footer(text="Emotes and image are random and will differ when the question is sent")

            message = await ctx.send(embed=embed)

            for emote in react_emotes:
                await message.add_reaction(emote)
        else:
            description = f"Question number {number} doesn't exist "
            emote = discord.utils.get(ctx.guild.emojis, id=1156319608630935584)
            colour = discord.Colour.red()

            embed = discord.Embed(
                title="Preview error",
                description=f"{description}{emote}",
                colour=colour
            )
            embed.set_footer(text=self.footer)

            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(QOTDs(bot))
