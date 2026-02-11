"""
Fun extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import json
import random

import discord.ext.commands as commands
from discord import commands as std_commands
from discord import IntegrationType, SlashCommandGroup

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

    @std_commands.slash_command(
        name="xkcd",
        category=cmn.Cats.FUN,
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _xkcd(self, ctx: std_commands.context.ApplicationContext, number: int):
        """Looks up an xkcd comic by number."""
        await ctx.send_response("http://xkcd.com/" + str(number))

    @fun_cat.command(
        name="tar",
        category=cmn.Cats.FUN,
    )
    async def _tar(self, ctx: std_commands.context.ApplicationContext):
        """Returns xkcd: tar."""
        await ctx.send_response("http://xkcd.com/1168")

    @fun_cat.command(
        name="standards",
        category=cmn.Cats.FUN,
    )
    async def _standards(self, ctx: std_commands.context.ApplicationContext):
        """Returns xkcd: Standards."""
        await ctx.send_response("http://xkcd.com/927")

    @fun_cat.command(
        name="worksplit",
        category=cmn.Cats.FUN,
    )
    async def _worksplit(self, ctx: std_commands.context.ApplicationContext):
        """Posts "Work split you lids"."""
        embed = cmn.embed_factory_slash(ctx)
        embed.title = "Work Split, You Lids!"
        embed.set_image(url=opt.resources_url + self.imgs["worksplit"])
        await ctx.send_response(embed=embed)

    @fun_cat.command(
        name="funetics",
        category=cmn.Cats.FUN,
    )
    async def _funetics_lookup(
        self, ctx: std_commands.context.ApplicationContext, *, msg: str
    ):
        """Generates fun/wacky phonetics for a word or phrase."""
        result = ""
        for char in msg.lower():
            if char.isalpha():
                result += random.choice(
                    [word for word in self.words if word[0] == char]
                )
            else:
                result += char
            result += " "
        embed = cmn.embed_factory_slash(ctx)
        embed.title = f"Funetics for {msg}"
        embed.description = result.title()
        embed.colour = cmn.colours.good
        await ctx.send_response(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(FunCog(bot))
