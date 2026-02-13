"""
Fun extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import json
import random
from typing import Union

import discord.ext.commands as commands
from discord import ApplicationContext, IntegrationType, Embed, SlashCommandGroup

import common as cmn

import data.options as opt


class FunCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(cmn.paths.resources / "imgs.1.json") as file:
            self.imgs: dict = json.load(file)
        with open(cmn.paths.resources / "words.1.txt") as words_file:
            self.words = words_file.read().lower().splitlines()

    fun_cat = SlashCommandGroup(
        "fun",
        "Novelty fun commands.",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )

    # region xkcd

    @commands.slash_command(
        name="xkcd",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _xkcd_slash(self, ctx: ApplicationContext, number: int):
        """Looks up an xkcd comic by number."""
        await ctx.send_response("http://xkcd.com/" + str(number))

    @commands.command(name="xkcd", aliases=["x"], category=cmn.Cats.FUN)
    async def _xkcd_prefix(self, ctx: commands.Context, number: int):
        """Looks up an xkcd comic by number."""
        await ctx.send("http://xkcd.com/" + str(number))

    # endregion

    # region tar

    @fun_cat.command(
        name="tar",
    )
    async def _tar_slash(self, ctx: ApplicationContext):
        """Returns xkcd: tar."""
        await ctx.send_response("http://xkcd.com/1168")

    @commands.command(name="tar", category=cmn.Cats.FUN)
    async def _tar_prefix(self, ctx: commands.Context):
        """Returns xkcd: tar."""
        await ctx.send("http://xkcd.com/1168")

    # endregion

    # region standards

    @fun_cat.command(
        name="standards",
    )
    async def _standards_slash(self, ctx: ApplicationContext):
        """Returns xkcd: Standards."""
        await ctx.send_response("http://xkcd.com/927")

    @commands.command(name="standards", category=cmn.Cats.FUN)
    async def _standards_prefix(self, ctx: commands.Context):
        """Returns xkcd: Standards."""
        await ctx.send("http://xkcd.com/927")

    # endregion

    # region worksplit

    async def _worksplit_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        embed = cmn.embed_factory(ctx)
        embed.title = "Work Split, You Lids!"
        embed.set_image(url=opt.resources_url + self.imgs["worksplit"])
        return embed

    @fun_cat.command(
        name="worksplit",
    )
    async def _worksplit_slash(self, ctx: ApplicationContext):
        """Posts "Work split you lids"."""
        await ctx.send_response(embed=await self._worksplit_core(ctx))

    @commands.command(name="worksplit", aliases=["split", "ft8"], category=cmn.Cats.FUN)
    async def _worksplit_prefix(self, ctx: commands.Context):
        """Posts "Work split you lids"."""
        await ctx.send(embed=await self._worksplit_core(ctx))

    # endregion

    # region funetics

    async def _funetics_lookup_core(
        self, ctx: Union[ApplicationContext, commands.Context], msg
    ) -> Embed:
        result = ""
        for char in msg.lower():
            if char.isalpha():
                result += random.choice(
                    [word for word in self.words if word[0] == char]
                )
            else:
                result += char
            result += " "
        embed = cmn.embed_factory(ctx)
        embed.title = f"Funetics for {msg}"
        embed.description = result.title()
        embed.colour = cmn.colours.good
        return embed

    @fun_cat.command(
        name="funetics",
    )
    async def _funetics_lookup_slash(self, ctx: ApplicationContext, msg: str):
        """Generates fun/wacky phonetics for a word or phrase."""
        await ctx.send_response(embed=await self._funetics_lookup_core(ctx, msg))

    @commands.command(name="funetics", aliases=["fun"], category=cmn.Cats.FUN)
    async def _funetics_lookup_prefix(self, ctx: commands.Context, *, msg: str):
        """Generates fun/wacky phonetics for a word or phrase."""
        await ctx.send(embed=await self._funetics_lookup_core(ctx, msg))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(FunCog(bot))
