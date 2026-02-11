"""
Land Weather extension for qrm
---
Copyright (C) 2019-2020 classabbyamp, 0x5c  (as weather.py)
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import re

import aiohttp

import discord
import discord.ext.commands as commands
from discord import commands as std_commands
from discord import IntegrationType
from discord import Option

import common as cmn


class WeatherCog(commands.Cog):
    wttr_units_regex = re.compile(r"\B-([cCfF])\b")

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(connector=bot.qrm.connector)

    weather_cat = discord.SlashCommandGroup(
        "weather",
        "Gets weather conditions from wttr.in.",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )

    @weather_cat.command(name="forecast")
    async def _weather_conditions_forecast(
        self,
        ctx: std_commands.context.ApplicationContext,
        location: Option(
            str,
            "City name, landmark, airport code, domain, IP, \
area code, or GPS coords. See https://wttr.in/:help",
        ),  # type: ignore
        scale: str = "",
    ):
        """Gets local weather forecast for the next three days from wttr.in."""

        if scale == "f":  # TODO: change this out for OptionChoices
            units = "u"
        elif scale == "c":
            units = "m"
        else:
            units = ""

        loc = self.wttr_units_regex.sub("", location).strip()

        embed = cmn.embed_factory_slash(ctx)
        embed.title = f"Weather Forecast for {loc}"
        embed.description = "Data from [wttr.in](http://wttr.in/)."
        embed.colour = cmn.colours.good

        loc = loc.replace(" ", "+")
        embed.set_image(url=f"http://wttr.in/{loc}_{units}pnFQ.png")
        await ctx.send_response(embed=embed)

    @weather_cat.command(
        name="now",
    )
    async def _weather_conditions_now(
        self,
        ctx: std_commands.context.ApplicationContext,
        location: Option(
            str,
            "City name, landmark, airport code, domain, IP, \
area code, or GPS coords. See https://wttr.in/:help",
        ),  # type: ignore
        scale: str = "",
    ):
        """Gets current local weather conditions from wttr.in."""

        if scale == "f":
            units = "u"
        elif scale == "c":
            units = "m"
        else:
            units = ""

        loc = self.wttr_units_regex.sub("", location).strip()

        embed = cmn.embed_factory_slash(ctx)
        embed.title = f"Current Weather for {loc}"
        embed.description = "Data from [wttr.in](https://wttr.in/:help)."
        embed.colour = cmn.colours.good

        loc = loc.replace(" ", "+")
        embed.set_image(url=f"http://wttr.in/{loc}_0{units}pnFQ.png")

        await ctx.send_response(embed=embed)

    @commands.slash_command(
        name="metar",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def metar(
        self,
        ctx: std_commands.context.ApplicationContext,
        airport: Option(
            str,
            "Four character ICAO code identifying an airport.",
            required=True,
            min_length=4,
            max_length=4,
        ),  # type: ignore
        hours: Option(int, "Hours of historical data to pull", default=0, max_value=500),  # type: ignore
    ):
        """Gets current raw METAR (Meteorological Terminal Aviation Routine Weather Report) for an airport."""

        embed = cmn.embed_factory_slash(ctx)
        airport = airport.upper()

        if not re.fullmatch(r"\w(\w|\d){2,3}", airport):
            embed.title = "Invalid airport given!"
            embed.colour = cmn.colours.bad
            await ctx.send_response(embed=embed)
            return

        url = f"https://aviationweather.gov/api/data/metar?ids={airport}&format=raw&taf=false&hours={hours}"
        async with self.session.get(url) as r:
            if r.status != 200:
                raise cmn.BotHTTPError(r)
            metar = await r.text()

        if hours > 0:
            embed.title = f"METAR for {airport} for the last {hours} hour{'s' if hours > 1 else ''}"
        else:
            embed.title = f"Current METAR for {airport}"

        embed.description = (
            "Data from [aviationweather.gov](https://www.aviationweather.gov/)."
        )
        embed.colour = cmn.colours.good
        embed.description += f"\n\n```\n{metar}\n```"

        await ctx.send_response(embed=embed)

    @commands.slash_command(
        name="taf",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def taf(
        self,
        ctx: std_commands.context.ApplicationContext,
        airport: Option(
            str,
            "Four character ICAO code identifying an airport.",
            required=True,
            min_length=4,
            max_length=4,
        ),  # type: ignore
    ):
        """Gets forecasted Terminal Aerodrome Forecast data for an airport. Includes the latest METAR data."""

        embed = cmn.embed_factory_slash(ctx)
        airport = airport.upper()

        if not re.fullmatch(r"\w(\w|\d){2,3}", airport):
            embed.title = "Invalid airport given!"
            embed.colour = cmn.colours.bad
            await ctx.send_response(embed=embed)
            return

        url = f"https://aviationweather.gov/api/data/taf?ids={airport}&format=raw&metar=true"
        async with self.session.get(url) as r:
            if r.status != 200:
                raise cmn.BotHTTPError(r)
            taf = await r.text()

        embed.title = f"Current TAF for {airport}"
        embed.description = (
            "Data from [aviationweather.gov](https://www.aviationweather.gov/)."
        )
        embed.colour = cmn.colours.good
        embed.description += f"\n\n```\n{taf}\n```"

        await ctx.send_response(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(WeatherCog(bot))
