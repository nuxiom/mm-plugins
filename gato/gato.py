import asyncio
import importlib
import json
import os
import random
import sys
from datetime import datetime, timedelta
from functools import reduce

import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

sys.path.append(os.path.dirname(__file__))
import gatos
importlib.reload(gatos)
import team
importlib.reload(team)
import data
importlib.reload(data)


DIR = os.path.dirname(__file__)
SAVE_FILE = os.path.join(os.getcwd(), "currency.json")
CURRENCY_NAME = "Plum Blossom"
CURRENCY_EMOJI = "🌸"


class PullView(discord.ui.View):

    frames: list[dict] = []
    current_frame: int = 0
    title: str
    results: list[gatos.Gato]
    result_lines: list[str]

    channel: discord.TextChannel
    author: discord.User
    message: discord.Message
    ongoing: bool = True
    skipped_yet: bool = False

    def __init__(self, channel: discord.TextChannel, author: discord.User, anims: list[dict], results: list[gatos.Gato], result_lines: list[str]):
        super().__init__()
        self.frames = anims
        self.channel = channel
        self.author = author
        self.title = f"{self.author.display_name}'s pull"
        self.results = results
        self.result_lines = result_lines

    async def handle_frame(self, frame: int, skipping=False):
        if skipping:
            self.skipped_yet = True

        if frame == len(self.frames):
            self.ongoing = False
            self.stop()
            description="\n".join(self.result_lines)
            if len(self.frames) == 1:
                embed = discord.Embed(title=self.title, colour=discord.Colour.teal())
                if skipping:
                    embed.set_image(url=self.frames[0]["solo"])
                    await self.message.edit(embed=embed, view=None)
                    await asyncio.sleep(self.frames[0]["solo_duration"] + 2)
                    embed.description = description
                    embed.set_image(url=self.frames[0]["static"])
                    await self.message.edit(embed=embed)
                else:
                    embed.description = description
                    embed.set_image(url=self.frames[0]["static"])
                    await self.message.edit(embed=embed, view=None)
            else:
                ls = "- " + "\n- ".join([itm.DISPLAY_NAME for itm in self.results])
                embed = discord.Embed(title=self.title, colour=discord.Colour.teal(), description=description)
                await self.message.edit(embed=embed, view=None)
        else:
            embed = discord.Embed(title=self.title, colour=discord.Colour.teal())
            if skipping:
                embed.set_image(url=self.frames[frame]["static"])
                await self.message.edit(embed=embed, view=self)
            else:
                embed.set_image(url=self.frames[frame]["anim"])
                await self.message.edit(embed=embed, view=self)
                await asyncio.sleep(self.frames[frame]["duration"] + 3)
                self.skipped_yet = True
                if self.current_frame == frame:
                    if len(self.frames) == 1:
                        await self.handle_frame(1)
                    else:
                        embed.set_image(url=self.frames[frame]["static"])
                        await self.message.edit(embed=embed, view=self)

    async def first_frame(self):
        self.message = await self.channel.send(self.author.mention)
        await self.handle_frame(0, skipping=False)

    async def on_timeout(self):
        await self.handle_frame(len(self.frames))

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="▶️")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Next item."""
        if interaction.user.id != self.author.id:
            embed = discord.Embed(colour=discord.Colour.red(), description="Only the person pulling can interact.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()
        if not self.skipped_yet:
            if len(self.frames) == 1:
                self.current_frame += 1
            await self.handle_frame(self.current_frame, skipping=True)
        else:
            self.current_frame += 1
            await self.handle_frame(self.current_frame)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="⏩")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip pulls to result."""
        if interaction.user.id != self.author.id:
            embed = discord.Embed(colour=discord.Colour.red(), description="Only the person pulling can interact.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()
        self.current_frame = len(self.frames)
        await self.handle_frame(self.current_frame, skipping=True)


class BannersView(discord.ui.View):

    banners: list[data.Banner]
    current_banner: int
    ongoing_pulls: dict[int, PullView]
    gato_game: "GatoGame"
    
    author_id: int
    ctx: commands.Context
    message: discord.Message

    def __init__(self, ctx: commands.Context, banners: list[data.Banner], message: discord.Message, gato_game: "GatoGame"):
        super().__init__()
        self.banners = banners
        self.current_banner = 0
        self.ongoing_pulls: dict[int, PullView] = {}
        self.message = message
        self.ctx = ctx
        self.author_id = ctx.author.id
        self.gato_game = gato_game

    async def refresh_embed(self):
        desc = " | ".join([
            bann.name if i != self.current_banner else f"**{bann.name}**" for i, bann in enumerate(self.banners)
        ])
        embed = discord.Embed(
            title="Gacha banners",
            description=desc,
            colour=self.banners[self.current_banner].colour
        )
        embed.set_image(url=self.banners[self.current_banner].img)
        await self.message.edit(content="", embed=embed)

    async def on_timeout(self) -> None:
        self.stop()
        embed = discord.Embed(
            title="Gacha banners",
            description="This view has expired. Use `?critter banners` to show one again!"
        )
        await self.message.edit(embed=embed, view=None)

    async def refresh_buttons(self):
        pull_cost = self.banners[self.current_banner].pull_cost
        btn: discord.ui.Button
        for btn in self.children:
            if btn.custom_id == "1pull":
                btn.label = f"{pull_cost} - Pull 1"
            elif btn.custom_id == "10pull":
                btn.label = f"{pull_cost*10} - Pull 10"
            elif btn.custom_id == "left":
                btn.disabled = True if self.current_banner == 0 else False
            elif btn.custom_id == "right":
                btn.disabled = True if self.current_banner+1 == len(self.banners) else False
        await self.message.edit(view=self)

    async def start_pulls(self, interaction: discord.Interaction, pull_count: int):
        player_id = interaction.user.id
        if player_id in self.gato_game.ongoing_pulls and self.gato_game.ongoing_pulls[player_id].ongoing:
            description = f"You already have an ongoing pull, please be patient!"
            embed = discord.Embed(
                title="Error",
                description=description.strip(),
                colour=discord.Colour.red()
            )
            await self.ctx.send(embed=embed)
            return

        anims_lists = []
        anims_lists = []
        bann = self.banners[self.current_banner]
        pull_results = bann.get_pulls_results(pull_count)
        max_rarity = max(itm.RARITY for itm in pull_results)

        if player_id not in self.gato_game.nurseries:
            self.gato_game.nurseries[player_id] = []
        nursery = self.gato_game.nurseries[player_id]

        result_lines = []
        gato: gatos.Gato
        for gato in pull_results:
            thegato: gatos.Gato = None
            for g in nursery:
                if isinstance(g, gato):
                    thegato = g
            if thegato is None:
                thegato = gato(name=f"{interaction.user.name}'s {gato.DISPLAY_NAME}")
                nursery.append(thegato)
                result_lines.append(f"- **{gato.DISPLAY_NAME}** obtained!")
            elif thegato.eidolon < 6:
                thegato.eidolon += 1
                result_lines.append(f"- **{thegato.name}**'s eidolon level increased to **E{thegato.eidolon}**!")
            else:
                cpr = {
                    6: 10*bann.pull_cost,
                    5: 5*bann.pull_cost,
                    4: 1*bann.pull_cost,
                    3: bann.pull_cost//2
                }
                money = cpr[thegato.RARITY]
                # refund player
                result_lines.append(f"- **{thegato.name}** is already **E6**. You received **{money}** {CURRENCY_EMOJI} in compensation.")

        for i, gato in enumerate(pull_results):
            anim_name: str
            if i == 0:
                anim_name = f"train{max_rarity}"
            else:
                anim_name = "solo"
            
            anims_lists.append({
                "anim": data.Data.animations[gato.ANIMATIONS][anim_name]["url"],
                "solo": data.Data.animations[gato.ANIMATIONS]["solo"]["url"],
                "static": data.Data.animations[gato.ANIMATIONS]["static"]["url"],
                "duration": data.Data.animations[gato.ANIMATIONS][anim_name]["duration"],
                "solo_duration": data.Data.animations[gato.ANIMATIONS]["solo"]["duration"],
            })

        pv = PullView(self.ctx.channel, interaction.user, anims_lists, pull_results, result_lines)
        self.gato_game.ongoing_pulls[player_id] = pv
        await pv.first_frame()


    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="left", emoji="⬅️")
    async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            embed = discord.Embed(colour=discord.Colour.red(), description="Only the person who did the command can interact with this.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()
        self.current_banner -= 1
        if self.current_banner < 0:
            self.current_banner = 0
        await self.refresh_buttons()
        await self.refresh_embed()

    @discord.ui.button(style=discord.ButtonStyle.gray, label="Details", emoji="📄")
    async def details(self, interaction: discord.Interaction, button: discord.ui.Button):
        bann = self.banners[self.current_banner]
        embed = discord.Embed(
            title=f"{bann.name} - Details",
            description=bann.get_rates_text(),
            colour=bann.colour
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="1pull", label="... - Pull 1", emoji="🌸")
    async def single(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.start_pulls(interaction, 1)

    @discord.ui.button(style=discord.ButtonStyle.green, custom_id="10pull", label="... - Pull 10", emoji="🌸")
    async def multi(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.start_pulls(interaction, 10)

    @discord.ui.button(style=discord.ButtonStyle.blurple, custom_id="right", emoji="➡️")
    async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            embed = discord.Embed(colour=discord.Colour.red(), description="Only the person who did the command can interact with this.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()
        self.current_banner += 1
        if self.current_banner >= len(self.banners):
            self.current_banner = len(self.banners) - 1
        await self.refresh_buttons()
        await self.refresh_embed()



class GatoGame(commands.Cog):
    """Critter gacha game plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.footer = ""  # TODO: REPLACE ME

        self.nurseries: dict[int, list[gatos.Gato]] = {
            200282032771694593: [gatos.ExampleGato(name="Cyxo's critter")]
        }

        self.teams: dict[int, team.Team] = {}

        self.ongoing_pulls = {}


    @commands.group(name="critter", invoke_without_command=True, aliases=["gato", "catto", "cake"])
    async def critter(self, ctx: commands.Context):
        """
        Ruan Mei Mains' critter gacha game!
        """

        await ctx.send_help(ctx.command)


    def handle_events(self, user_id: int, team: list[gatos.Gato]):
        description = ""

        for gato in team:
            events_by_type = {}
            for event in gato._events:
                et = list(event.keys())[0]
                if et not in events_by_type:
                    events_by_type[et] = []
                events_by_type[et].append(event[et])

            for et, value in events_by_type.items():
                description += f"- **{gato.name}** "

                args = {}
                if et == "bitten":
                    args["amount"] = 0
                    for _ in value:
                        rnd = random.randint(2, 10)
                        args["amount"] += rnd
                    args["currency"] = CURRENCY_EMOJI
                    args["count"] = len(value)

                description += gato.EVENT_DESCRIPTIONS[et].format(**args)
                description += "\n"

        return description


    @critter.command(name="banners", aliases=["banner", "bann", "pull", "gacha"])
    async def banners(self, ctx: commands.Context):
        """List banners and allow to pull on them"""
        message = await ctx.send("Loading...")

        bv = BannersView(ctx, data.Data.banners, message, self)
        await bv.refresh_buttons()
        await bv.refresh_embed()


    @critter.command(name="nursery")
    async def nursery(self, ctx: commands.Context):
        """ Show your critter nursery. """

        description = ""
        colour = discord.Colour.teal()
        if ctx.author.id in self.nurseries and len(self.nurseries[ctx.author.id]) > 0:
            for i, gato in enumerate(self.nurseries[ctx.author.id]):
                description += f"{i+1}. **{gato.name}**: {gato.DISPLAY_NAME} *(✨ E{gato.eidolon})*\n"
        else:
            description = "You have no critter silly goose ! Use `?critter pull`"
            colour = discord.Colour.red()

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s nursery",
            description=description,
            colour=colour
        )
        await ctx.send(embed=embed)


    @critter.command(name="info")
    async def info(self, ctx: commands.Context, number: int):
        """ Show info about a critter from your nursery. """

        if ctx.author.id in self.nurseries or len(self.nurseries[ctx.author.id]) == 0:
            nursery = self.nurseries[ctx.author.id]
            number -= 1

            if number < 0 or number >= len(nursery):
                embed = discord.Embed(
                    title=f"Error",
                    description=f"Critter number {number + 1} not found. Use `?critter nursery`",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
            else:
                gato = nursery[number]
                desc = gato.__doc__.format(eidolon=gato.eidolon)

                description = f"{desc}\n" + \
                f"**Health:** {round(gato.health)} / {round(gato.max_health)}\n" + \
                f"**Hunger:** {round(gato.hunger)} / {round(gato.max_hunger)}\n" + \
                f"**Mood:** {round(gato.mood)} / {round(gato.max_mood)}\n" + \
                f"**Energy:** {round(gato.energy)} / {round(gato.max_energy)}\n" + \
                f"**Friendship:** {int(gato.friendship)}/10\n" + \
                f"\n✨ **Eidolon {gato.eidolon}**"

                embed = discord.Embed(
                    title=gato.name,
                    description=description,
                    colour=discord.Colour.teal()
                )
                embed.set_thumbnail(url=gato.IMAGE)
                embed.set_footer(text="For now, stats don't update in real time. Only when you claim rewards.")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s nursery",
                description="You have no critter silly goose ! Use `?critter pull`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)


    @critter.command(name="deploy", aliases=["dispatch"])
    async def deploy(self, ctx: commands.Context, *gato_numbers):
        """ Deploy a team of critters. Specify numbers from your nursery (example: `?critter deploy 3 2 1 4`) or use `?critter deploy` alone to redeploy previous team. ⚠️ Order matters! Critter skills will take effect in deployment order (for example, put Critters that boost the whole team in first place). """

        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no critter silly goose ! Use `?critter pull`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        nursery = self.nurseries[ctx.author.id]

        if len(gato_numbers) == 0:
            if ctx.author.id in self.teams:
                tm = self.teams[ctx.author.id]
                if tm.deployed_at is not None:
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description="A team is already deployed! Use `?critter claim` to see what they fetched for you!",
                        colour=discord.Colour.red()
                    )
                    await ctx.send(embed=embed)
                else:
                    tm.deployed_at = datetime.now()
                    for gato in tm.gatos:
                        gato.deploy(tm.gatos)
                    gato_names = "**, **".join([gato.name for gato in tm.gatos])
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description=f"A team with **{gato_names}** has been deployed! Check back in a while with `?critter claim` to see what they fetched for you!",
                        colour=discord.Colour.teal()
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Deploy team",
                    description="No team was previously deployed! Example use `?critter deploy 1 2 3 4` (check critter numbers with `?critter nursery`)",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
        else:
            if ctx.author.id in self.teams and self.teams[ctx.author.id].deployed_at is not None:
                embed = discord.Embed(
                    title=f"Deploy team",
                    description="A team is already deployed! Use `?critter claim` to see what they fetched for you!",
                    colour=discord.Colour.red()
                )
                await ctx.send(embed=embed)
                return

            # Get unique numbers
            gato_numbers = reduce(lambda re, x: re+[x] if x not in re else re, gato_numbers, [])
            legatos: list[gatos.Gato] = []
            for i in gato_numbers[:4]:
                if not i.isnumeric():
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description=f"{i} is not a valid number! Example usage: `?critter deploy 1 2 3 4`!",
                        colour=discord.Colour.red()
                    )
                    await ctx.send(embed=embed)
                    return
                number = int(i)-1
                if number >= 0 and number < len(nursery):
                    legatos.append(nursery[number])
                else:
                    embed = discord.Embed(
                        title=f"Deploy team",
                        description=f"Critter number {i} not found in your nursery! Check critter numbers with `?critter nursery`!",
                        colour=discord.Colour.red()
                    )
                    await ctx.send(embed=embed)
                    return

            tm = team.Team(legatos)
            self.teams[ctx.author.id] = tm
            for gato in tm.gatos:
                gato.deploy(tm.gatos)

            gato_names = "**, **".join([gato.name for gato in legatos])
            embed = discord.Embed(
                title=f"Deploy team",
                description=f"A team with **{gato_names}** has been deployed! Check back in a while with `?critter claim` to see what they fetched for you!",
                colour=discord.Colour.teal()
            )
            await ctx.send(embed=embed)
            return


    @critter.command(name="claim")
    async def claim(self, ctx: commands.Context):
        """ Claim what the deployed team has gathered. """

        if not ctx.author.id in self.teams or self.teams[ctx.author.id].deployed_at is None:
            embed = discord.Embed(
                title=f"Claim rewards",
                description="No team has been deployed! Check `?critter deploy` to deploy one first!",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        tm = self.teams[ctx.author.id]
        now = datetime.now()
        delta = int((now - tm.deployed_at).total_seconds())
        tm.deployed_at = None

        TIME_STEP = 1
        currency = 0
        objects = []
        for _ in range(0, delta, TIME_STEP):
            if all(gato._fainted for gato in tm.gatos):
                break

            for gato in tm.gatos:
                c, o = gato.simulate(tm.gatos, TIME_STEP)
                currency += c
                objects += o

        events = self.handle_events(ctx.author.id, tm.gatos)
        if len(events) == 0:
            events = "*Nothing specific happened.*"
        if len(objects) > 0:
            obj = "**" + '**, **'.join(set([f"{objects.count(o)}x {o}" for o in objects])) + "**"
        else:
            obj = "*no objects*"

        embed = discord.Embed(
            title=f"Claim rewards",
            description=f"### Expedition results\nYour critters brought back **{int(currency)}** {CURRENCY_EMOJI} and {obj}.\n### Event log\n{events}",
            colour=discord.Colour.teal()
        )
        await ctx.send(embed=embed)


    @critter.command(name="nanook")
    async def nanook(self, ctx: commands.Context):
        """ Set all the stats of all your critters to 1 """

        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no critter silly goose ! Use `?critter pull`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        for gato in self.nurseries[ctx.author.id]:
            gato.health = 1
            gato.mood = 1
            gato.hunger = 1
            gato.energy = 1

        await ctx.send("Done! ✅")


    @critter.command(name="yaoshi")
    async def yaoshi(self, ctx: commands.Context):
        """ Set all the stats of all your Critters to maximum """

        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no critter silly goose ! Use `?critter pull`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        for gato in self.nurseries[ctx.author.id]:
            gato.health = gato.max_health
            gato.mood = gato.max_mood
            gato.hunger = gato.max_hunger
            gato.energy = gato.max_energy

        await ctx.send("Done! ✅")


    @critter.command(name="fastforward", aliases=["ff"])
    async def ff(self, ctx: commands.Context, seconds: int):
        """ Fastforward the ongoing Gato expedition by a specified amount of time (in seconds) """

        if not ctx.author.id in self.teams or self.teams[ctx.author.id].deployed_at is None:
            embed = discord.Embed(
                title=f"Claim rewards",
                description="No team has been deployed! Check `?critter deploy` to deploy one first!",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)
            return

        tm = self.teams[ctx.author.id]
        tm.deployed_at -= timedelta(seconds=seconds)

        await ctx.send("Done! ✅")



async def setup(bot):
    await bot.add_cog(GatoGame(bot))
