"""
Land Weather extension for qrm
---
Copyright (C) 2019-2020 classabbyamp, 0x5c  (as weather.py)
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import re

import aiohttp

from typing import Union

import discord
import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType, Option

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

    # region weather prefix parent

    @commands.group(
        name="weather",
        aliases=["wttr"],
        case_insensitive=True,
        category=cmn.Cats.WEATHER,
    )
    async def _weather_conditions(self, ctx: commands.Context):
        """Gets local weather conditions from [wttr.in](http://wttr.in/).

        *Supported location types:*
        city name: `paris`
        any location: `~Eiffel Tower`
        Unicode name of any location in any language: `Москва`
        airport code (3 letters): `muc`
        domain name `@stackoverflow.com`
        area codes: `12345`
        GPS coordinates: `-78.46,106.79`

        Add a `-c` or `-f` to use Celcius or Fahrenheit: `-c YSC`"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # endregion

    # region forecast

    async def _weather_conditions_forecast_core(
        self,
        ctx: Union[ApplicationContext, commands.Context],
        location: str = "",
        units: str = "",
    ) -> Embed:
        loc = self.wttr_units_regex.sub("", location).strip()

        embed = cmn.embed_factory(ctx)
        embed.title = f"Weather Forecast for {loc}"
        embed.description = "Data from [wttr.in](http://wttr.in/)."
        embed.colour = cmn.colours.good

        loc = loc.replace(" ", "+")
        embed.set_image(url=f"http://wttr.in/{loc}_{units}pnFQ.png")
        return embed

    @weather_cat.command(name="forecast")
    async def _weather_conditions_forecast_slash(
        self,
        ctx: ApplicationContext,
        location: Option(
            str,
            description="City name, landmark, airport code, domain, IP, \
area code, or GPS coords. See https://wttr.in/:help",
            default="",
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

        await ctx.send_response(
            embed=await self._weather_conditions_forecast_core(ctx, location, units)
        )

    @_weather_conditions.command(
        name="forecast", aliases=["fc", "future"], category=cmn.Cats.WEATHER
    )
    async def _weather_conditions_forecast_prefix(
        self, ctx: commands.Context, *, location: str
    ):
        """Gets local weather forecast for the next three days from [wttr.in](http://wttr.in/).
        See help of the `weather` command for possible location types and options."""
        search_result = re.search(self.wttr_units_regex, location)
        if search_result:
            units_arg = search_result.group(1)
        else:
            units_arg = ""

        if units_arg.lower() == "f":
            units = "u"
        elif units_arg.lower() == "c":
            units = "m"
        else:
            units = ""

        await ctx.send(
            embed=await self._weather_conditions_forecast_core(ctx, location, units)
        )

    # endregion

    # region now

    async def _weather_conditions_now_core(
        self,
        ctx: Union[ApplicationContext, commands.Context],
        location: str = "",
        units: str = "",
    ) -> Embed:
        loc = self.wttr_units_regex.sub("", location).strip()

        embed = cmn.embed_factory(ctx)
        embed.title = f"Current Weather for {loc}"
        embed.description = "Data from [wttr.in](https://wttr.in/:help)."
        embed.colour = cmn.colours.good

        loc = loc.replace(" ", "+")
        embed.set_image(url=f"http://wttr.in/{loc}_0{units}pnFQ.png")
        return embed

    @weather_cat.command(
        name="now",
    )
    async def _weather_conditions_now_slash(
        self,
        ctx: ApplicationContext,
        location: Option(
            str,
            description="City name, landmark, airport code, domain, IP, \
area code, or GPS coords. See https://wttr.in/:help",
            default="",
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

        await ctx.send_response(
            embed=await self._weather_conditions_now_core(ctx, location, units)
        )

    async def _weather_conditions_now_prefix(
        self, ctx: commands.Context, *, location: str
    ):
        """Gets current local weather conditions from [wttr.in](http://wttr.in/).
        See help of the `weather` command for possible location types and options."""
        search_result = re.search(self.wttr_units_regex, location)
        if search_result:
            units_arg = search_result.group(1)
        else:
            units_arg = ""

        if units_arg.lower() == "f":
            units = "u"
        elif units_arg.lower() == "c":
            units = "m"
        else:
            units = ""

        await ctx.send(
            embed=await self._weather_conditions_now_core(ctx, location, units)
        )

    # endregion

    # region metar

    async def _metar_core(
        self,
        ctx: Union[ApplicationContext, commands.Context],
        airport: str,
        hours: int = 0,
    ) -> Embed:
        embed = cmn.embed_factory(ctx)
        airport = airport.upper()

        if not re.fullmatch(r"\w(\w|\d){2,3}", airport):
            embed.title = "Invalid airport given!"
            embed.colour = cmn.colours.bad
            return embed

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
        return embed

    @commands.slash_command(
        name="metar",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _metar_slash(
        self,
        ctx: ApplicationContext,
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
        await ctx.defer()
        await ctx.send_response(embed=await self._metar_core(ctx, airport, hours))

    @commands.command(name="metar", category=cmn.Cats.WEATHER)
    async def _metar_prefix(self, ctx: commands.Context, airport: str, hours: int = 0):
        """Gets current raw METAR (Meteorological Terminal Aviation Routine Weather Report) for an airport. \
        Optionally, a number of hours can be given to show a number of hours of historical METAR data.

        Airports should be given as an \
        [ICAO code](https://en.wikipedia.org/wiki/List_of_airports_by_IATA_and_ICAO_code)."""
        with ctx.typing():
            await ctx.send(embed=await self._metar_core(ctx, airport, hours))

    # endregion

    # region taf

    async def _taf_core(
        self, ctx: Union[ApplicationContext, commands.Context], airport: str
    ) -> Embed:
        embed = cmn.embed_factory(ctx)
        airport = airport.upper()

        if not re.fullmatch(r"\w(\w|\d){2,3}", airport):
            embed.title = "Invalid airport given!"
            embed.colour = cmn.colours.bad
            return embed

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
        return embed

    @commands.slash_command(
        name="taf",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _taf_slash(
        self,
        ctx: ApplicationContext,
        airport: Option(
            str,
            "Four character ICAO code identifying an airport.",
            required=True,
            min_length=4,
            max_length=4,
        ),  # type: ignore
    ):
        """Gets forecasted Terminal Aerodrome Forecast data for an airport. Includes the latest METAR data."""
        await ctx.defer()
        await ctx.send_response(embed=await self._taf_core(ctx, airport))

    @commands.command(name="taf", category=cmn.Cats.WEATHER)
    async def _taf_prefix(self, ctx: commands.Context, airport: str):
        """Gets forecasted raw TAF (Terminal Aerodrome Forecast) data for an airport. Includes the latest METAR data.

        Airports should be given as an \
        [ICAO code](https://en.wikipedia.org/wiki/List_of_airports_by_IATA_and_ICAO_code)."""
        with ctx.typing():
            await ctx.send(embed=await self._taf_core(ctx, airport))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(WeatherCog(bot))
