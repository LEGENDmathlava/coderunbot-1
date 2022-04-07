import io
import json
import os
import pathlib
import re

import aiohttp
import discord
from discord.ext import commands


URL = 'https://wandbox.org/api/compile.json'
BADE_DIR = pathlib.Path(__file__).parent.parent


class DeleteButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == interaction.message.reference.cached_message.author.id:
            await interaction.message.delete()


class Code(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def run(self, ctx: commands.Context, language: str, *, code: str):
        """Run code"""

        view = discord.ui.View(DeleteButton(label='Delete'))

        with open(BADE_DIR / 'config' / 'languages.json', 'r') as f:
            language_dict = json.load(f)
        code = re.sub(r'```[A-z\-\+]*\n', '', code).replace('```', '')
        stdin = ''
        language = language.lower() \
            .replace('pp', '++').replace('sharp', '#') \
            .replace('clisp', 'lisp').replace('lisp', 'clisp')
        if language not in language_dict.keys():
            embed = discord.Embed(
                title='The following languages are supported',
                description=', '.join(language_dict.keys()),
                color=0xff0000
            )
            embed.set_author(
                name=ctx.author.name,
                icon_url=ctx.author.display_avatar.url
            )
            return await ctx.reply(embed=embed, view=view)
        if language == 'nim':
            compiler_option = '--hint[Processing]:off\n' \
                '--hint[Conf]:off\n' \
                '--hint[Link]:off\n' \
                '--hint[SuccessX]:off'
        else:
            compiler_option = ''
        params = {
            'compiler': language_dict[language],
            'code': code,
            'stdin': stdin,
            'compiler-option-raw': compiler_option,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(URL, json=params) as r:
                if r.status == 200:
                    result = await r.json()
                else:
                    embed = discord.Embed(
                        title='Connection Error',
                        description=f'{r.status}',
                        color=0xff0000
                    )
                    return await ctx.reply(embed=embed, view=view)

        embed = discord.Embed(title='Result')
        embed_color = 0xff0000
        files = []
        for k, v in result.items():
            if k in ('program_message', 'compiler_message'):
                continue
            if v == '':
                continue
            if k == 'status' and v == '0':
                embed_color = 0x007000
            if language == 'nim' and k == 'compiler_error':
                v = re.sub(r'CC: \S+\n', '', v)
                if v == '':
                    continue
            if len(v) > 1000 or len(v.split('\n')) > 100:
                files.append(
                    discord.File(
                        io.StringIO(v),
                        k + '.txt'
                    )
                )
            else:
                embed.add_field(
                    name=k,
                    value='```\n' + v + '\n```',
                )
        embed.color = embed_color
        embed.set_author(
            name=ctx.author.name,
            icon_url=ctx.author.display_avatar.url
        )
        return await ctx.reply(embed=embed, files=files, view=view)


def setup(bot):
    return bot.add_cog(Code(bot))