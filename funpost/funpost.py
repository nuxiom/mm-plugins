import asyncio
import json
import random
from os.path import dirname, exists

import discord
from discord.ext import commands
from urlextract import URLExtract

from core import checks
from core.models import PermissionLevel

# List of commands here:
# ?magic8ball

DIR = dirname(__file__)
GAY_STICKERS = [
    "https://media.discordapp.net/attachments/1106785083379171372/1157133462331985961/20230928_174023.png?ex=65178003&is=65162e83&hm=dc1d01d630f54b13f7bea3dc29be717a279dd46929041dd34745880963379621&",
    "https://media.discordapp.net/attachments/1106785083379171372/1156858924838965268/Untitled570_20230928144333.png?ex=65168055&is=65152ed5&hm=257aeb2eb1d4596009f0ef092adf2e8573242cfae51116e0685545bfa322b87d&=&width=703&height=655",
    "https://media.discordapp.net/attachments/1106793246748848199/1156482829098692649/20230926_233455.png?ex=65152210&is=6513d090&hm=0a5126e8622729f3baa2b31b69dcfef12c9e4d0808e9c09ab9febb46692489bb&=&width=655&height=655",
    "https://media.discordapp.net/attachments/1106793246748848199/1156482828868014100/20230926_230548.png?ex=65152210&is=6513d090&hm=3d90ac3e06e7c44fbb399bf9d06a7634d88940a51d533e086c44cb21c6775077&=&width=334&height=333",
    "https://media.discordapp.net/attachments/1106785083379171372/1156341810042515486/20230926_013519.png?ex=65149ebb&is=65134d3b&hm=330623a1c4b273c609e548740ca66145e5d0365735b3bfbf76348454492b6e4a&=&width=655&height=655",
    "https://media.discordapp.net/attachments/1106785083379171372/1156341810315149395/20230926_013109.png?ex=65149ebb&is=65134d3b&hm=b30994a003ffd066581127220f869c6d90ad41810e86034e0117df45a4748500&=&width=655&height=655",
    "https://media.discordapp.net/attachments/1106785083379171372/1156341810868793505/20230926_002553.png?ex=65149ebb&is=65134d3b&hm=71997888a7a9399fc9443d2b454c55aaa409d95b8bfeb9c83f90017265284d64&=&width=655&height=655",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876241093464264/ruan_mei_nerd.png?ex=651dd71a&is=651c859a&hm=06c83048f9ec6c405cd1c5ebf169214cf4db9b9e655d6711854ee1003febd15d&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876240736956526/ruanmeifingerheart.png?ex=651dd71a&is=651c859a&hm=0a506f0784a73f21d142dfa4dcf747854a1b00fdaa378d2db70a6359fb074b15&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876415614255194/ruanmei_bugcat_nod.gif?ex=651dd744&is=651c85c4&hm=c7e78157961d9421ec7d9445b6c23d3c16832b732673e5b51fded27929691949&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876605804986389/ruanmeijoy1.png?ex=651dd771&is=651c85f1&hm=d2b89fc3e7b7b5a426a67b6c54e30d357db69e1e0ee98fe47359e79e3935c33a&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876917269803088/20230926_230006.png?ex=651dd7bb&is=651c863b&hm=8768cd09a5fd98b9105293645c12a6f1e121e0ae9e9e0223108537ee8bda8806&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876917609537556/ruan_mei_eyebrow_raise.png?ex=651dd7bc&is=651c863c&hm=29ad9b9f9bd18ca6cba98f5b79ed564ef489f9beefe8764d94b2b3206188e23b&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158876917836042290/20230926_012018.gif?ex=651dd7bc&is=651c863c&hm=9bbace8884217e3c582c89d5e5f61496baced80d0c462790f82bbb64c65d2d95&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158877082860912661/ruanmeidead.png?ex=651dd7e3&is=651c8663&hm=3690617f2abd9143677c348a9c947d1cc6f0d4b1393296fac131c4df86e5e14d&",
    "https://cdn.discordapp.com/attachments/1117346551644295239/1158877083657846824/ruanpackwatch.png?ex=651dd7e3&is=651c8663&hm=876634884d7a439207bafbc26916a03f6b1c1b68d029a94b57168463ddda3208&",
    "https://cdn.discordapp.com/emojis/1153489300051202198.png",
    "https://cdn.discordapp.com/emojis/1155737942506078278.png",
    "https://cdn.discordapp.com/emojis/1155740644040519690.png"
]
EIGHT_BALL_TITLES = [
    'Ruan Mei has calculated..',
    'Ruan_Mei.exe outputs..',
    'Ruan Mei has thought about this..'
]

class Misc(commands.Cog):
    """Funpost Plugin"""

    def __init__(self, bot):
        self.bot = bot
        self.footer = ""  # TODO: REPLACE ME

    # Gaydar
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.command(aliases=['gay', 'gae', 'gayrate'])
    async def gaydar(self, ctx: commands.Context, member: commands.MemberConverter = None):
        """🌈?"""
        if member is None:
            member = ctx.author

        num = random.randrange(10001) / 100

        embed = discord.Embed(
            title=f"The Genius Society has decided...",
            description=f"{member.display_name} is **{num}%** gae.",
            colour=discord.Colour.random()
        )
        embed.set_thumbnail(url=random.choice(GAY_STICKERS))

        # funi footer if anyone gets either
        if num == 0:
            embed.set_footer(text=f'[{member.display_name} is now a Certified Hetero]')
        elif num == 100:
            embed.set_footer(text=f'[{member.display_name} is now a Certified Gay]')
            
        await ctx.send(embed=embed)

    # Magic 8 Ball
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.command(aliases=['8ball', 'ball'])
    async def magic8ball(self, ctx: commands.Context, *, text: str):
        """Ask the magic Seele~"""

        num = random.randint(0, 9)

        with open(f'{DIR}/8ball.json') as f:
            ans = json.load(f)

        if num < 3:
            thumbnail = "https://media.discordapp.net/attachments/1106793246748848199/1156482828620537866/20230926_231635.png?ex=65152210&is=6513d090&hm=4d60abc6fc8a9fd4359bc6f4b1e5d0e40978ec2575ecee3e429d8084e8dd183a&=&width=315&height=315"
            emote = discord.utils.get(ctx.guild.emojis, id=1156150407228309564)
            answer = random.choice(ans[2]["negative"])
        elif num < 6:
            thumbnail = "https://cdn.discordapp.com/attachments/1117346551644295239/1158876241093464264/ruan_mei_nerd.png?ex=651dd71a&is=651c859a&hm=06c83048f9ec6c405cd1c5ebf169214cf4db9b9e655d6711854ee1003febd15d&"
            emote = discord.utils.get(ctx.guild.emojis, id=1156716062461661314)
            answer = random.choice(ans[1]["neutral"])
        elif num < 10:
            thumbnail = "https://media.discordapp.net/attachments/1106785083379171372/1156341810315149395/20230926_013109.png?ex=65149ebb&is=65134d3b&hm=b30994a003ffd066581127220f869c6d90ad41810e86034e0117df45a4748500&=&width=655&height=655"
            emote = discord.utils.get(ctx.guild.emojis, id=1152230094312591360)
            answer = random.choice(ans[0]["positive"])
        else:  # Easter egg
            thumbnail = "https://s3.blankdvth.com/74b72448-f31f-4d85-a765-fa04bca84edd.jpg"
            emote = "🐛"
            answer = f"You've won, you've done the impossible. Contact the bot devs to see them become confused. (`{num}`)"

        embed = discord.Embed(
            title=random.choice(EIGHT_BALL_TITLES),
            colour=discord.Colour.random()
        )

        embed.add_field(name='Question', value=text)
        embed.set_footer(text=self.footer)
        embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="Answer", value=f"{emote} {answer}", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Misc(bot))
