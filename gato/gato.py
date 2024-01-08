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
    result_ids: list[str]

    message: discord.Message
    context: commands.Context
    ongoing: bool = True
    skipped_yet: bool = False

    def __init__(self, ctx: commands.Context, anims: list[dict], result_ids: list[str]):
        super().__init__()
        self.frames = anims
        self.ctx = ctx
        self.title = f"{self.ctx.author.display_name}'s pull"
        self.result_ids = result_ids

    async def handle_frame(self, frame: int, skipping=False):
        if skipping:
            self.skipped_yet = True

        if frame == len(self.frames):
            self.ongoing = False
            self.stop()
            if len(self.frames) == 1:
                embed = discord.Embed(title=self.title, colour=discord.Colour.teal())
                if skipping:
                    embed.set_image(url=self.frames[0]["solo"])
                    await self.message.edit(embed=embed, view=None)
                    await asyncio.sleep(self.frames[0]["solo_duration"] + 2)
                    embed.set_image(url=self.frames[0]["static"])
                    await self.message.edit(embed=embed)
                else:
                    embed.set_image(url=self.frames[0]["static"])
                    await self.message.edit(embed=embed, view=None)
            else:
                ls = "- " + "\n- ".join([eval(itm).DISPLAY_NAME for itm in self.result_ids])
                embed = discord.Embed(title=self.title, colour=discord.Colour.teal(), description=ls)
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
        self.message = await self.ctx.send(self.ctx.author.mention)
        await self.handle_frame(0, skipping=False)

    async def on_timeout(self):
        await self.handle_frame(len(self.frames))

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji="▶️")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Next item."""
        if interaction.user.id != self.ctx.author.id:
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
        if interaction.user.id != self.ctx.author.id:
            embed = discord.Embed(colour=discord.Colour.red(), description="Only the person pulling can interact.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()
        self.current_frame = len(self.frames)
        await self.handle_frame(self.current_frame, skipping=True)



class GatoGame(commands.Cog):
    """Critter gacha game plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.footer = ""  # TODO: REPLACE ME

        self.nurseries: dict[int, list[gatos.Gato]] = {
            200282032771694593: [gatos.ExampleGato(name="Cyxo's critter")]
        }

        self.teams: dict[int, team.Team] = {}

        self.ongoing_pulls: dict[int, PullView] = {}


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
                        rnd = random.randint(10, 50)
                        args["amount"] += rnd
                    args["currency"] = CURRENCY_EMOJI
                    args["count"] = len(value)

                description += gato.EVENT_DESCRIPTIONS[et].format(**args)
                description += "\n"

        return description


    # @gato.command(name="pull")
    # async def pull(self, ctx: commands.Context, *, gato_name: str = None):
    #     """ Pull for a random Gato. You can specify a name to give it if it's a gato type you don't own yet. """

    #     if ctx.author.id not in self.nurseries:
    #         self.nurseries[ctx.author.id] = []

    #     nursery = self.nurseries[ctx.author.id]

    #     pulled = random.choice(["ExampleGato", "NormalGato"])

    #     gato: gatos.Gato = None
    #     for cat in nursery:
    #         if cat.__class__.__name__ == pulled:
    #             gato = cat
    #             break

    #     if gato is None:
    #         if gato_name is None:
    #             gato_name = f"{ctx.author.name}'s {pulled}"

    #         gato = eval(f"gatos.{pulled}")(name=gato_name)
    #         nursery.append(gato)
    #         embed = discord.Embed(
    #             title="Pull",
    #             colour=discord.Colour.teal(),
    #             description=f"{ctx.author.mention} you just obtained a **{pulled}** named **{gato_name}** !!"
    #         )
    #         await ctx.send(embed=embed)
    #     elif gato.eidolon < 6:
    #         gato.eidolon += 1
    #         embed = discord.Embed(
    #             title="Pull",
    #             colour=discord.Colour.gold(),
    #             description=f"{ctx.author.mention} you just obtained a **{pulled}** !! **{gato.name}**'s Eidolon level increased to **{gato.eidolon}**!"
    #         )
    #         await ctx.send(embed=embed)
    #     else:
    #         embed = discord.Embed(
    #             title="Pull",
    #             colour=discord.Colour.teal(),
    #             description=f"{ctx.author.mention} your **{gato.name}** is already at Eidolon level 6! You got **666** {CURRENCY_EMOJI} as a compensation!"
    #         )
    #         await ctx.send(embed=embed)


    @critter.command(name="pull", aliases=["single", "multi", "10pull"])
    async def pull(self, ctx: commands.Context, *, banner: str = "1"):
        """Pull on a banner (defaults to banner number 1)"""

        command = ctx.message.content.split()[1]
        
        bann = data.Data.banners[0]

        error_title = f"Can't do a {command}"
        MULTIS = ["10pull", "multi"]

        if bann is None:
            description = f'No banners at the time!'
            embed = discord.Embed(
                title=error_title,
                description=description.strip(),
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
            return

        if command in MULTIS:
            pull_count = 10
        else:
            pull_count = 1
        pull_cost = bann.pull_cost * pull_count

        player_id = ctx.author.id
        # if player_id not in self.save.keys() or self.save[player_id].pull_currency < pull_cost:
        #     description = f"You don't have enough {CURRENCY_NAME}s. The cost for a {command} on this banner is **{pull_cost} {CURRENCY_NAME}{'s' if pull_cost > 1 else ''}**.\n\nTalk some more and use `?gacha balance` to check your balance!"
        #     embed = discord.Embed(
        #         title=error_title,
        #         description=description.strip(),
        #         colour=discord.Colour.red()
        #     )
        #     embed.set_footer(text=self.footer)
        #     await ctx.send(embed=embed)
        #     return

        # player = self.save[player_id]
        # if player._pulling:
        if player_id in self.ongoing_pulls and self.ongoing_pulls[player_id].ongoing:
            description = f"You already have an ongoing pull, please be patient!"
            embed = discord.Embed(
                title=error_title,
                description=description.strip(),
                colour=discord.Colour.red()
            )
            embed.set_footer(text=self.footer)
            await ctx.send(embed=embed)
            return

        pull_results = []
        pull_results_ids = []
        anims_lists = []
        max_rarity = 3
        for _ in range(pull_count):
            rnd = random.randint(0, bann._cumulative_weights[-1] - 1)
            for i in range(len(bann._cumulative_weights)):
                if rnd < bann._cumulative_weights[i]:
                    weight = sorted(bann.drop_weights.keys())[i]
                    item_id = random.choice(bann.drop_weights[weight])
                    pull_results_ids.append(item_id)
                    item = eval(item_id)
                    if item.RARITY > max_rarity:
                        max_rarity = item.RARITY
                    pull_results.append(item)
                    break

        gato: gatos.Gato
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

        pv = PullView(ctx, anims_lists, pull_results_ids)
        self.ongoing_pulls[player_id] = pv
        await pv.first_frame()

        # img = Image.open(os.path.join(DIR, "img", "gachabg.png"))
        # if command in MULTIS:
        #     for i in range(pull_count):
        #         item = pull_results[i]
        #         itm = item.get_image().resize((92, 92))
        #         img.paste(itm, (30 * (1+(i % 5)) + 92 * (i % 5), 60 * (1+(i // 5)) + 92 * (i // 5)), itm)
        # else:
        #     item = pull_results[0]
        #     itm = item.get_image().resize((160, 160))
        #     img.paste(itm, (240, 100), itm)

        # with io.BytesIO() as f:
        #     img.save(f, 'PNG')
        #     f.seek(0)
        #     r = requests.post("https://api.imgbb.com/1/upload?key=97d73c9821eedce1864ef870883defdb", files={"image": f})
        #     j = r.json()
        #     pull_url = j["data"]["url"]


    @critter.command(name="nursery")
    async def nursery(self, ctx: commands.Context):
        """ Show your critter nursery. """

        description = ""
        colour = discord.Colour.teal()
        if ctx.author.id in self.nurseries and len(self.nurseries[ctx.author.id]) > 0:
            for i, gato in enumerate(self.nurseries[ctx.author.id]):
                description += f"{i+1}. **{gato.name}**: {gato.__class__.__name__} *(✨ E{gato.eidolon})*\n"
        else:
            description = "You have no critter silly goose ! Use `?critter pull/multi`"
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
                description="You have no critter silly goose ! Use `?critter pull/multi`",
                colour=discord.Colour.red()
            )
            await ctx.send(embed=embed)


    @critter.command(name="deploy")
    async def deploy(self, ctx: commands.Context, *gato_numbers):
        """ Deploy a team of critters. Specify numbers from your nursery (example: `?critter deploy 3 2 1 4`) or use `?critter deploy` alone to redeploy previous team. ⚠️ Order matters! Critter skills will take effect in deployment order (for example, put Critters that boost the whole team in first place). """

        if ctx.author.id not in self.nurseries:
            embed = discord.Embed(
                title=f"Deploy team",
                description="You have no critter silly goose ! Use `?critter pull/multi`",
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
                        gato.deploy()
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
                gato.deploy()

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
                description="You have no critter silly goose ! Use `?critter pull/multi`",
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
                description="You have no critter silly goose ! Use `?critter pull/multi`",
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
