"""
Prefixes Lookup extension for qrm
---
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from typing import Union

import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType

import common as cmn
from resources import callsign_info


class PrefixesCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pfxs = callsign_info.options

    # region prefixes

    async def _vanity_prefixes_core(
        self, ctx: Union[ApplicationContext, commands.Context], country: str = ""
    ) -> Embed:
        country = country.lower()
        embed = cmn.embed_factory(ctx)
        if country not in self.pfxs:
            desc = "Possible arguments are:\n"
            for key, val in self.pfxs.items():
                desc += (
                    f"`{key}`: {val.title}{('  ' + val.emoji if val.emoji else '')}\n"
                )
            embed.title = f"{country} Not Found!"
            embed.description = desc
            embed.colour = cmn.colours.bad
            return embed
        else:
            data = self.pfxs[country]
            embed.title = data.title + ("  " + data.emoji if data.emoji else "")
            embed.description = data.desc
            embed.colour = cmn.colours.good

            for name, val in data.calls.items():
                embed.add_field(name=name, value=val, inline=False)
            return embed

    @commands.slash_command(
        name="prefixes",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _vanity_prefixes_slash(self, ctx: ApplicationContext, country: str = ""):
        """Lists valid callsign prefixes for different countries."""
        await ctx.send_response(embed=await self._vanity_prefixes_core(ctx, country))

    @commands.command(
        name="prefixes",
        aliases=["vanity", "pfx", "vanities", "prefix"],
        category=cmn.Cats.REF,
    )
    async def _vanity_prefixes_prefix(self, ctx: commands.Context, country: str = ""):
        """Lists valid callsign prefixes for different countries."""
        await ctx.send(embed=await self._vanity_prefixes_core(ctx, country))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(PrefixesCog(bot))
