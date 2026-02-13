"""
Contest Calendar extension for qrm
---
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from typing import Union

import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType

import common as cmn


class ContestCalendarCog(commands.Cog):

    # region contests

    async def _contests_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        embed = Embed()
        embed = cmn.embed_factory(ctx)
        embed.title = "Contest Calendar"
        embed.description = (
            "*We are currently rewriting the old, Chrome-based `contests` command. In the meantime, "
            "use [the website](https://www.contestcalendar.com/weeklycont.php).*"
        )
        embed.colour = cmn.colours.good
        return embed

    @commands.slash_command(
        name="contests",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _contests_slash(self, ctx: ApplicationContext, private: bool = False):
        await ctx.send_response(embed=await self._contests_core(ctx), ephemeral=private)

    @commands.command(
        name="contests", aliases=["cc", "tests"], category=cmn.Cats.LOOKUP
    )
    async def _contests_prefix(self, ctx: commands.Context):
        await ctx.send(embed=await self._contests_core(ctx))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(ContestCalendarCog(bot))
