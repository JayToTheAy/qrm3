"""
Morse Code extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import json
from typing import Union

import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType, SlashCommandGroup

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

    # region morsify

    async def _morse_core(
        self, ctx: Union[ApplicationContext, commands.Context], msg: str
    ) -> Embed:
        result = ""
        for char in msg.upper():
            try:
                result += self.morse[char]
            except KeyError:
                result += "<?>"
            result += " "
        embed = cmn.embed_factory(ctx)
        embed.title = f"Morse Code for {msg}"
        embed.description = "**`" + result + "`**"
        embed.colour = cmn.colours.good
        return embed

    @morse_cat.command(
        name="morsify",
    )
    async def _morse_slash(self, ctx: ApplicationContext, msg: str):
        """Converts ASCII to international morse code."""
        await ctx.send_response(embed=await self._morse_core(ctx, msg))

    @commands.command(name="morse", aliases=["cw"], category=cmn.Cats.CODES)
    async def _morse_prefix(self, ctx: commands.Context, *, msg: str):
        """Converts ASCII to international morse code."""
        await ctx.send(embed=await self._morse_core(ctx, msg))

    # endregion

    # region unmorsify

    async def _unmorse_core(
        self, ctx: Union[ApplicationContext, commands.Context], msg: str
    ) -> Embed:
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
        embed = cmn.embed_factory(ctx)
        embed.title = f"ASCII for {msg0}"
        embed.description = "`" + result + "`"
        embed.colour = cmn.colours.good
        return embed

    @morse_cat.command(
        name="unmorsify",
    )
    async def _unmorse_slash(self, ctx: ApplicationContext, msg: str):
        """Converts international morse code to ASCII."""
        await ctx.send_response(embed=await self._unmorse_core(ctx, msg))

    @commands.command(
        name="unmorse", aliases=["demorse", "uncw", "decw"], category=cmn.Cats.CODES
    )
    async def _unmorse_prefix(self, ctx: commands.Context, *, msg: str):
        """Converts international morse code to ASCII."""
        await ctx.send(embed=await self._unmorse_core(ctx, msg))

    # endregion

    # region weight

    async def _weight_core(
        self, ctx: Union[ApplicationContext, commands.Context], msg: str
    ) -> Embed:
        embed = cmn.embed_factory(ctx)
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
                return embed
        embed.title = f"CW Weight of {msg}"
        embed.description = f"The CW weight is **{weight}**"
        embed.colour = cmn.colours.good
        return embed

    @morse_cat.command(
        name="weight",
    )
    async def _weight_slash(self, ctx: ApplicationContext, msg: str):
        """Calculates the CW weight of a callsign or message."""
        await ctx.send_response(embed=await self._weight_core(ctx, msg))

    @commands.command(
        name="cwweight", aliases=["weight", "cww"], category=cmn.Cats.CODES
    )
    async def _weight_prefix(self, ctx: commands.Context, *, msg: str):
        """Calculates the CW weight of a callsign or message."""
        await ctx.send(embed=await self._weight_core(ctx, msg))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(MorseCog(bot))
