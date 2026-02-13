"""
TeX extension for qrm
---
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import aiohttp
from io import BytesIO
from typing import Tuple, Union
from urllib.parse import urljoin

import discord
import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType

import common as cmn
import data.options as opt


class TexCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(connector=bot.qrm.connector)
        with open(cmn.paths.resources / "template.1.tex") as latex_template:
            self.template = latex_template.read()

    # region tex

    async def _tex_core(
        self, ctx: Union[ApplicationContext, commands.Context], expr: str
    ) -> Tuple[Union[discord.File, None], Embed]:
        payload = {
            "format": "png",
            "code": self.template.replace("#CONTENT#", expr),
            "quality": 50,
        }

        # ask rTeX to render our expression
        async with self.session.post(
            urljoin(opt.rtex_instance, "api/v2"), json=payload
        ) as r:
            if r.status != 200:
                raise cmn.BotHTTPError(r)

            render_result = await r.json()
            if render_result["status"] != "success":
                embed = cmn.embed_factory(ctx)
                embed.title = "LaTeX Rendering Failed!"
                embed.description = (
                    "Here are some common reasons:\n"
                    "• Did you forget to use math mode? Surround math expressions with `$`,"
                    " like `$x^3$`.\n"
                    "• Are you using a command from a package? It might not be available.\n"
                    "• Are you including the document headers? We already did that for you."
                )
                return (None, embed)

        # if rendering went well, download the file given in the response
        async with self.session.get(
            urljoin(opt.rtex_instance, "api/v2/" + render_result["filename"])
        ) as r:
            png_buffer = BytesIO(await r.read())

        embed = cmn.embed_factory(ctx)
        embed.title = "LaTeX Expression"
        embed.description = f"Rendered by [rTeX]({opt.rtex_attribution})."
        embed.set_image(url="attachment://tex.png")
        return (discord.File(png_buffer, "tex.png"), embed)

    @commands.slash_command(
        name="tex",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _tex_slash(self, ctx: ApplicationContext, expr: str):
        """Renders a LaTeX expression.

        In paragraph mode by default. To render math, add `$` around math expressions.
        """
        await ctx.defer()

        file, embed = await self._tex_core(ctx, expr)
        if file:
            await ctx.send_followup(file=file, embed=embed)
        else:
            await ctx.send_followup(embed=embed)

    @commands.command(name="tex", aliases=["latex"], category=cmn.Cats.UTILS)
    async def _tex_prefix(self, ctx: commands.Context, *, expr: str):
        """Renders a LaTeX expression.

        In paragraph mode by default. To render math, add `$` around math expressions.
        """
        with ctx.typing():
            file, embed = await self._tex_core(ctx, expr)
            if file:
                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(embed=embed)

        # endregion tex


def setup(bot: commands.Bot):
    bot.add_cog(TexCog(bot))
