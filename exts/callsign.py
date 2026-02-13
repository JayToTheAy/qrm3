"""
Callsign Lookup extension for qrm
---
Copyright (C) 2019-2020 classabbyamp, 0x5c  (as qrz.py)
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from typing import Dict, Union

import aiohttp
from callsignlookuptools import QrzAsyncClient, CallsignLookupError, CallsignData

from discord import IntegrationType, ApplicationContext, Embed
from discord.ext import commands

import common as cmn

import data.options as opt
import data.keys as keys


class QRZCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.qrz = None
        try:
            if keys.qrz_user and keys.qrz_pass:
                # seed the qrz object with the previous session key, in case it already works
                session_key = ""
                try:
                    with open("data/qrz_session") as qrz_file:
                        session_key = qrz_file.readline().strip()
                except FileNotFoundError:
                    pass
                self.qrz = QrzAsyncClient(
                    username=keys.qrz_user,
                    password=keys.qrz_pass,
                    useragent="discord-qrm3",
                    session_key=session_key,
                    session=aiohttp.ClientSession(connector=bot.qrm.connector),
                )
        except AttributeError:
            pass

    # region QRZ Lookup

    async def _qrz_lookup_core(
        self, ctx: Union[ApplicationContext, commands.Context], callsign: str
    ) -> Embed:
        """Builds an embed for a QRZ Lookup."""

        embed = cmn.embed_factory(ctx)
        embed.title = f"QRZ Data for {callsign.upper()}"

        if self.qrz is None:
            embed.colour = cmn.colours.neutral
            embed.add_field(
                name="Link", value=f"http://qrz.com/db/{callsign}", inline=False
            )
            return embed
        else:
            try:
                data = await self.qrz.search(callsign)
            except CallsignLookupError as e:
                embed.colour = cmn.colours.bad
                embed.description = str(e)
                return embed
            else:
                embed.title = f"QRZ Data for {data.callsign}"
                embed.colour = cmn.colours.good
                embed.url = data.url
                if data.image is not None:
                    embed.set_thumbnail(url=data.image.url)

                for title, val in qrz_process_info(data).items():
                    if val is not None and (val := str(val)):
                        embed.add_field(name=title, value=val, inline=True)

                return embed

    @commands.slash_command(
        name="call",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _qrz_lookup_slash(
        self,
        ctx: ApplicationContext,
        callsign: str,
        private: bool = False,
    ):
        """Looks up a callsign on [QRZ.com](https://www.qrz.com/)."""
        await ctx.defer(ephemeral=private)

        await ctx.send_followup(
            embed=await self._qrz_lookup_core(ctx, callsign), ephemeral=private
        )

    @commands.command(name="call", aliases=["qrz"], category=cmn.Cats.LOOKUP)
    async def _qrz_lookup_prefix(self, ctx: commands.Context, callsign: str):
        """Looks up a callsign on [QRZ.com](https://www.qrz.com/)."""
        async with ctx.typing():
            await ctx.send(embed=await self._qrz_lookup_core(ctx, callsign))


def qrz_process_info(data: CallsignData) -> Dict:
    if data.name is not None:
        if opt.qrz_only_nickname:
            nm = data.name.name if data.name.name is not None else ""
            if data.name.nickname is not None:
                name = data.name.nickname + " " + nm
            elif data.name.first:
                name = data.name.first + " " + nm
            else:
                name = nm
        else:
            name = data.name
    else:
        name = None

    qsl = dict()
    if data.qsl is not None:
        qsl = {
            "eQSL?": data.qsl.eqsl,
            "Paper QSL?": data.qsl.mail,
            "LotW?": data.qsl.lotw,
            "QSL Info": data.qsl.info,
        }

    return {
        "Name": name,
        "Country": data.dxcc.name if data.dxcc is not None else None,
        "Address": data.address,
        "Grid Square": data.grid,
        "County": data.county,
        "CQ Zone": data.cq_zone,
        "ITU Zone": data.itu_zone,
        "IOTA Designator": data.iota,
        "Expires": f"{data.expire_date:%Y-%m-%d}"
        if data.expire_date is not None
        else None,
        "Aliases": ", ".join(data.aliases) if data.aliases else None,
        "Previous Callsign": data.prev_call,
        "License Class": data.lic_class,
        "Trustee": data.trustee,
        "Born": data.born,
    } | qsl

    # endregion


def setup(bot):
    bot.add_cog(QRZCog(bot))
