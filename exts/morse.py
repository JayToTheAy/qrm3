"""
Morse Code extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import json

import discord.ext.commands as commands
from discord import commands as std_commands
from discord import IntegrationType, SlashCommandGroup

import common as cmn


class MorseCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(cmn.paths.resources / "morse.1.json") as file:
            d = json.load(file)
            self.morse: dict[str, str] = d["morse"]
            self.ascii: dict[str, str] = d["ascii"]

    morse_cat = SlashCommandGroup(
        "cw",
        "Morse code commands",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )

    @morse_cat.command(
        name="morsify",
        category=cmn.Cats.CODES,
    )
    async def _morse(self, ctx: std_commands.context.ApplicationContext, msg: str):
        """Converts ASCII to international morse code."""
        result = ""
        for char in msg.upper():
            try:
                result += self.morse[char]
            except KeyError:
                result += "<?>"
            result += " "
        embed = cmn.embed_factory_slash(ctx)
        embed.title = f"Morse Code for {msg}"
        embed.description = "**`" + result + "`**"
        embed.colour = cmn.colours.good
        await ctx.send_response(embed=embed)

    @morse_cat.command(
        name="unmorsify",
        category=cmn.Cats.CODES,
    )
    async def _unmorse(self, ctx: std_commands.context.ApplicationContext, msg: str):
        """Converts international morse code to ASCII."""
        result = ""
        msg0 = msg
        list_msg: list[str] = msg.split("/")
        brokenup_msg: list[list[str]] = [m.split() for m in list_msg]
        for word in brokenup_msg:
            for char in word:
                try:
                    result += self.ascii[char]
                except KeyError:
                    result += "<?>"
            result += " "
        embed = cmn.embed_factory_slash(ctx)
        embed.title = f"ASCII for {msg0}"
        embed.description = "`" + result + "`"
        embed.colour = cmn.colours.good
        await ctx.send_response(embed=embed)

    @morse_cat.command(
        name="weight",
        category=cmn.Cats.CODES,
    )
    async def _weight(self, ctx: std_commands.context.ApplicationContext, msg: str):
        """Calculates the CW weight of a callsign or message."""
        embed = cmn.embed_factory_slash(ctx)
        msg = msg.upper()
        weight = 0
        for char in msg:
            try:
                cw_char = self.morse[char].replace("-", "==")
                weight += len(cw_char) * 2 + 2
            except KeyError:
                embed.title = "Error in calculation of CW weight"
                embed.description = f"Unknown character `{char}` in message"
                embed.colour = cmn.colours.bad
                await ctx.send_response(embed=embed)
                return
        embed.title = f"CW Weight of {msg}"
        embed.description = f"The CW weight is **{weight}**"
        embed.colour = cmn.colours.good
        await ctx.send_response(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(MorseCog(bot))
