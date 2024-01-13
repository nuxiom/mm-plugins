import asyncio

from beaupy import confirm, prompt, select, select_multiple
from gato import GatoGame
from discord import Message, User
from discord.ext.commands import Context
from rich.console import Console


console = Console()


class LocalContext(Context):

    author = User(state=None, data={
                  'id': 1234, 'username': 'root', 'discriminator': '', 'avatar': ''})

    def __init__(self):
        pass

    def send_help(self, *args):
        console.print('Not implemented')

    async def send(self, content=None, *, embed=None):
        if content is not None:
            console.print(content)

        if embed is not None:
            console.print(embed.title)
            console.print(embed.description)

        return None


gato = GatoGame(None)
ctx = LocalContext()


cmds = ['pull', 'nursery', 'info', 'deploy',
        'claim', 'nanook', 'yaoshi', 'ff', 'quit']


while True:
    console.print('Select a command:')
    cmd = select(options=cmds, cursor='>', cursor_style='red')

    if cmd == 'pull':
        asyncio.run(gato.pull(gato, ctx))
    elif cmd == 'nursery':
        asyncio.run(gato.nursery(gato, ctx))
    elif cmd == 'info':
        if ctx.author.id not in gato.nurseries:
            gato.nurseries[ctx.author.id] = []
        gatos = [f'{i+1}. {gato.name}' for i,
                 gato in enumerate(gato.nurseries[ctx.author.id])]
        if len(gatos) < 1:
            console.print('No gato yet!')
            continue
        console.print('Select a gato:')
        selection = select(options=range(1, len(
            gatos)+1), preprocessor=lambda num: gatos[num-1], cursor='>', cursor_style='red')
        asyncio.run(gato.info(gato, ctx, selection))
    elif cmd == 'deploy':

        if ctx.author.id not in gato.nurseries:
            gato.nurseries[ctx.author.id] = []
        gatos = [f'{i+1}. {gato.name}' for i,
                 gato in enumerate(gato.nurseries[ctx.author.id])]
        if len(gatos) < 1:
            console.print('No gato yet!')
            continue

        team = []
        opts = list(range(1, len(gatos)+2))
        for _ in range(4):
            selection = select(options=opts, preprocessor=lambda num: "That's it!" if num == len(
                gatos)+1 else gatos[num-1], cursor='>', cursor_style='red')
            if selection == opts[-1]:
                break
            team.append(selection)
            opts.remove(selection)
            console.print(f'Selected {selection}! Current team: {team}')
        console.print(f'Team assembled! {team}')
        asyncio.run(gato.deploy(gato, ctx, *[str(i) for i in team]))
    elif cmd == 'claim':
        asyncio.run(gato.claim(gato, ctx))
    elif cmd == 'nanook':
        asyncio.run(gato.nanook(gato, ctx))
    elif cmd == 'yaoshi':
        asyncio.run(gato.yaoshi(gato, ctx))
    elif cmd == 'ff':
        t = prompt('# of seconds?', target_type=int)
        asyncio.run(gato.ff(gato, ctx, t))
    elif cmd == 'quit':
        break
