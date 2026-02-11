"""
Propagation extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from datetime import datetime, timezone
from io import BytesIO

import cairosvg
import httpx

import discord
import discord.ext.commands as commands
from discord import commands as std_commands
from discord import IntegrationType

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

    @prop_cat.command(
        name="muf",
    )
    async def mufmap(self, ctx: std_commands.context.ApplicationContext):
        """Shows a world map of the Maximum Usable Frequency (MUF)."""
        await ctx.defer()

        resp = await self.httpx_client.get(self.muf_url)
        await resp.aclose()
        if resp.status_code != 200:
            raise cmn.BotHTTPError(resp)
        out = BytesIO(cairosvg.svg2png(bytestring=await resp.aread()))  # type: ignore # TODO: fix
        file = discord.File(out, "muf_map.png")
        embed = cmn.embed_factory_slash(ctx)
        embed.title = "Maximum Usable Frequency Map"
        embed.description = "Image from [prop.kc2g.com](https://prop.kc2g.com/)\nData sources listed on the page."
        embed.set_image(url="attachment://muf_map.png")
        await ctx.send_followup(file=file, embed=embed)

    @prop_cat.command(
        name="fof2",
    )
    async def fof2map(self, ctx: std_commands.context.ApplicationContext):
        """Shows a world map of the Critical Frequency (foF2)."""
        await ctx.defer()

        resp = await self.httpx_client.get(self.fof2_url)
        await resp.aclose()
        if resp.status_code != 200:
            raise cmn.BotHTTPError(resp)
        out = BytesIO(cairosvg.svg2png(bytestring=await resp.aread()))  # type: ignore
        file = discord.File(out, "fof2_map.png")
        embed = cmn.embed_factory_slash(ctx)
        embed.title = "Critical Frequency (foF2) Map"
        embed.description = "Image from [prop.kc2g.com](https://prop.kc2g.com/)\nData sources listed on the page."
        embed.set_image(url="attachment://fof2_map.png")
        await ctx.send_followup(file=file, embed=embed)

    @prop_cat.command(
        name="grayline",
    )
    async def grayline(self, ctx: std_commands.context.ApplicationContext):
        """Gets a map of the current greyline, where HF propagation is the best."""
        embed = cmn.embed_factory_slash(ctx)
        embed.title = "Current Greyline Conditions"
        embed.colour = cmn.colours.good
        date_params = f"&date=1&utc={datetime.now(timezone.utc):%Y-%m-%d+%H:%M:%S}"
        embed.set_image(url=self.gl_baseurl + date_params)
        await ctx.send_response(embed=embed)

    @prop_cat.command(
        name="solarweather",
    )
    async def solarweather(self, ctx: std_commands.context.ApplicationContext):
        """Gets a solar weather report."""
        resp = await self.httpx_client.get(self.n0nbh_sun_url)
        await resp.aclose()
        if resp.status_code != 200:
            raise cmn.BotHTTPError(resp)
        img = BytesIO(await resp.aread())
        file = discord.File(img, "solarweather.png")
        embed = cmn.embed_factory_slash(ctx)
        embed.title = "☀️ Current Solar Weather"
        embed.colour = cmn.colours.good
        embed.set_image(url="attachment://solarweather.png")
        await ctx.send_response(file=file, embed=embed)

    @prop_cat.command(
        name="drap",
    )
    async def drapmap(self, ctx: std_commands.context.ApplicationContext):
        """Gets the current D-RAP map for radio blackouts"""
        embed = cmn.embed_factory_slash(ctx)
        embed.title = "D Region Absorption Predictions (D-RAP) Map"
        embed.colour = cmn.colours.good
        embed.description = (
            "Image from [swpc.noaa.gov]"
            "(https://www.swpc.noaa.gov/products/d-region-absorption-predictions-d-rap)"
        )
        embed.set_image(url=self.noaa_drap_url)
        await ctx.send_response(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(PropagationCog(bot))
