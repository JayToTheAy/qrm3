"""
Propagation extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from datetime import datetime, timezone
from io import BytesIO
from typing import Tuple, Union

import cairosvg
import httpx

import discord
import discord.ext.commands as commands
from discord import ApplicationContext, Embed, File, IntegrationType

import common as cmn


class PropagationCog(commands.Cog):
    muf_url = "https://prop.kc2g.com/renders/current/mufd-normal-now.svg"
    fof2_url = "https://prop.kc2g.com/renders/current/fof2-normal-now.svg"
    gl_baseurl = "https://www.fourmilab.ch/cgi-bin/uncgi/Earth?img=ETOPO1_day-m.evif&dynimg=y&opt=-p"
    n0nbh_sun_url = "https://www.hamqsl.com/solarsun.php"
    noaa_drap_url = (
        "https://services.swpc.noaa.gov/images/animations/d-rap/global/latest.png"
    )

    prop_cat = discord.SlashCommandGroup(
        "prop",
        "Propagation",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )

    def __init__(self, bot):
        self.bot = bot
        self.httpx_client: httpx.AsyncClient = bot.qrm.httpx_client

    # region muf

    async def _mufmap_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Tuple[File, Embed]:
        resp = await self.httpx_client.get(
            self.muf_url
        )  # TODO: put this in a context manager?
        await resp.aclose()
        if resp.status_code != 200:
            raise cmn.BotHTTPError(resp)
        out = BytesIO(cairosvg.svg2png(bytestring=await resp.aread()))  # type: ignore
        file = discord.File(out, "muf_map.png")
        embed = cmn.embed_factory(ctx)
        embed.title = "Maximum Usable Frequency Map"
        embed.description = "Image from [prop.kc2g.com](https://prop.kc2g.com/)\nData sources listed on the page."
        embed.set_image(
            url="attachment://muf_map.png"
        )  # TODO: try to bypass caching of files by discord by appending the date to the image name?

        return (file, embed)

    @prop_cat.command(
        name="muf",
    )
    async def _mufmap_slash(self, ctx: ApplicationContext):
        """Shows a world map of the Maximum Usable Frequency (MUF)."""
        await ctx.defer()
        file, embed = await self._mufmap_core(ctx)
        await ctx.send_followup(file=file, embed=embed)

    @commands.command(name="mufmap", aliases=["muf"], category=cmn.Cats.WEATHER)
    async def _mufmap_prefix(self, ctx: commands.Context):
        """Shows a world map of the Maximum Usable Frequency (MUF)."""
        with ctx.typing():
            file, embed = await self._mufmap_core(ctx)
            await ctx.send(file=file, embed=embed)

    # endregion

    # region fof2

    async def _fof2map_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Tuple[File, Embed]:
        resp = await self.httpx_client.get(self.fof2_url)
        await resp.aclose()
        if resp.status_code != 200:
            raise cmn.BotHTTPError(resp)
        out = BytesIO(cairosvg.svg2png(bytestring=await resp.aread()))  # type: ignore
        file = discord.File(out, "fof2_map.png")
        embed = cmn.embed_factory(ctx)
        embed.title = "Critical Frequency (foF2) Map"
        embed.description = "Image from [prop.kc2g.com](https://prop.kc2g.com/)\nData sources listed on the page."
        embed.set_image(
            url="attachment://fof2_map.png"
        )  # TODO: try to bypass caching of files by discord by appending the date to the image name?

        return (file, embed)

    @prop_cat.command(
        name="fof2",
    )
    async def _fof2map_slash(self, ctx: ApplicationContext):
        """Shows a world map of the Critical Frequency (foF2)."""
        await ctx.defer()
        file, embed = await self._fof2map_core(ctx)
        await ctx.send_followup(file=file, embed=embed)

    @commands.command(
        name="fof2map", aliases=["fof2", "critfreq"], category=cmn.Cats.WEATHER
    )
    async def _fof2map_prefix(self, ctx: commands.Context):
        """Shows a world map of the Critical Frequency (foF2)."""
        with ctx.typing():
            file, embed = await self._fof2map_core(ctx)
            await ctx.send(file=file, embed=embed)

    # endregion

    # region grayline

    async def _grayline_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        embed = cmn.embed_factory(ctx)
        embed.title = "Current Greyline Conditions"
        embed.colour = cmn.colours.good
        date_params = f"&date=1&utc={datetime.now(timezone.utc):%Y-%m-%d+%H:%M:%S}"
        embed.set_image(url=self.gl_baseurl + date_params)
        return embed

    @prop_cat.command(
        name="grayline",
    )
    async def _grayline_slash(self, ctx: ApplicationContext):
        """Gets a map of the current greyline, where HF propagation is the best."""
        await ctx.send_response(embed=await self._grayline_core(ctx))

    @commands.command(
        name="grayline",
        aliases=["greyline", "grey", "gray", "gl"],
        category=cmn.Cats.WEATHER,
    )
    async def _grayline_prefix(self, ctx: commands.Context):
        """Gets a map of the current greyline, where HF propagation is the best."""
        await ctx.send(embed=await self._grayline_core(ctx))

    # endregion

    # region solarweather

    async def _solarweather_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Tuple[File, Embed]:
        resp = await self.httpx_client.get(self.n0nbh_sun_url)
        await resp.aclose()
        if resp.status_code != 200:
            raise cmn.BotHTTPError(resp)
        img = BytesIO(await resp.aread())
        file = discord.File(img, "solarweather.png")
        embed = cmn.embed_factory(ctx)
        embed.title = "☀️ Current Solar Weather"
        embed.colour = cmn.colours.good
        embed.set_image(
            url="attachment://solarweather.png"
        )  # TODO: try to bypass caching of files by discord by appending the date to the image name?
        return (file, embed)

    @prop_cat.command(
        name="solarweather",
    )
    async def _solarweather_slash(self, ctx: ApplicationContext):
        """Gets a solar weather report."""
        await ctx.defer()
        file, embed = await self._solarweather_core(ctx)
        await ctx.send_followup(file=file, embed=embed)

    @commands.command(name="solarweather", aliases=["solar"], category=cmn.Cats.WEATHER)
    async def _solarweather_prefix(self, ctx: commands.Context):
        """Gets a solar weather report."""
        with ctx.typing():
            file, embed = await self._solarweather_core(ctx)
            await ctx.send(file=file, embed=embed)

    # endregion

    # region drap

    async def _drapmap_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        embed = cmn.embed_factory(ctx)
        embed.title = "D Region Absorption Predictions (D-RAP) Map"
        embed.colour = cmn.colours.good
        embed.description = (
            "Image from [swpc.noaa.gov]"
            "(https://www.swpc.noaa.gov/products/d-region-absorption-predictions-d-rap)"
        )
        embed.set_image(url=self.noaa_drap_url)
        return embed

    @prop_cat.command(
        name="drap",
    )
    async def _drapmap_slash(self, ctx: ApplicationContext):
        """Gets the current D-RAP map for radio blackouts"""
        await ctx.send_response(embed=await self._drapmap_core(ctx))

    @commands.command(name="drapmap", aliases=["drap"], category=cmn.Cats.WEATHER)
    async def _drapmap_prefix(self, ctx: commands.Context):
        """Gets the current D-RAP map for radio blackouts"""
        await ctx.send(embed=await self._drapmap_core(ctx))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(PropagationCog(bot))
