"""
DXCC Prefix Lookup extension for qrm
---
Copyright (C) 2019-2020 classabbyamp, 0x5c  (as lookup.py)
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import threading
from typing import Union
from pathlib import Path

from ctyparser import BigCty

from discord import ApplicationContext, Embed, IntegrationType
from discord.ext import commands, tasks

import common as cmn


cty_path = Path("./data/cty.json")


class DXCCCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        try:
            self.cty = BigCty(cty_path)
        except OSError:
            self.cty = BigCty()

    # region dxcc

    async def _dxcc_lookup_core(
        self,
        ctx: Union[ApplicationContext, commands.Context],
        query: str,
        private: bool = False,
    ) -> Embed:
        query = query.upper()
        full_query = query
        embed = cmn.embed_factory(ctx)
        embed.title = "DXCC Info for "
        embed.description = f"*Last Updated: {self.cty.formatted_version}*"
        embed.colour = cmn.colours.bad
        while query:
            if query in self.cty.keys():
                data = self.cty[query]
                embed.add_field(name="Entity", value=data["entity"])
                embed.add_field(name="CQ Zone", value=data["cq"])
                embed.add_field(name="ITU Zone", value=data["itu"])
                embed.add_field(name="Continent", value=data["continent"])
                embed.add_field(
                    name="Time Zone",
                    value=f"+{data['tz']}" if data["tz"] > 0 else str(data["tz"]),
                )
                embed.title += query
                embed.colour = cmn.colours.good
                break
            else:
                query = query[:-1]
        else:
            embed.title += full_query + " not found"
            embed.colour = cmn.colours.bad
        return embed

    @commands.slash_command(
        name="dxcc",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _dxcc_lookup_slash(
        self,
        ctx: ApplicationContext,
        query: str,
        private: bool = False,
    ):
        """Gets DXCC info about a callsign prefix."""
        await ctx.send_response(
            embed=await self._dxcc_lookup_core(ctx, query), ephemeral=private
        )

    @commands.command(name="dxcc", aliases=["dx"], category=cmn.Cats.LOOKUP)
    async def _dxcc_lookup_prefix(
        self,
        ctx: commands.Context,
        query: str,
    ):
        """Gets DXCC info about a callsign prefix."""
        await ctx.send(embed=await self._dxcc_lookup_core(ctx, query))

    # endregion

    @tasks.loop(hours=24)
    async def _update_cty(self):
        update = threading.Thread(target=run_update, args=(self.cty, cty_path))
        update.start()


def run_update(cty_obj, dump_loc):
    update = cty_obj.update()
    if update:
        cty_obj.dump(dump_loc)


def setup(bot: commands.Bot):
    dxcccog = DXCCCog(bot)
    bot.add_cog(dxcccog)
    dxcccog._update_cty.start()
