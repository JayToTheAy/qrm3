"""
Grid extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from typing import Union

import gridtools

import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType, SlashCommandGroup

import common as cmn


class GridCog(commands.Cog):
    grid_cat = SlashCommandGroup(
        "grid",
        "Grid Calculation Operations",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # region grid_sq_lookup

    async def _grid_sq_lookup_core(
        self, ctx: Union[ApplicationContext, commands.Context], lat: float, lon: float
    ) -> Embed:
        latlong = gridtools.LatLong(lat, lon)
        grid = gridtools.Grid(latlong)

        embed = cmn.embed_factory(ctx)
        embed.title = (
            f"Maidenhead Grid Locator for {latlong.lat:.5f}, {latlong.long:.5f}"
        )
        embed.description = f"**{grid}**"
        embed.colour = cmn.colours.good
        return embed

    @grid_cat.command(
        name="lat2grid",
    )
    async def _grid_sq_lookup_slash(
        self, ctx: ApplicationContext, lat: float, lon: float
    ):
        (
            """Calculates the grid square for latitude and longitude coordinates."""
            """\n\nCoordinates should be in decimal format, with negative being latitude South and longitude West."""
            """\n\nTo calculate the latitude and longitude from a grid locator, use `/latlong`"""
        )
        await ctx.send_response(embed=await self._grid_sq_lookup_core(ctx, lat, lon))

    @commands.command(name="grid", category=cmn.Cats.CALC)
    async def _grid_sq_lookup_prefix(
        self, ctx: commands.Context, lat: float, lon: float
    ):
        (
            """Calculates the grid square for latitude and longitude coordinates."""
            """\n\nCoordinates should be in decimal format, with negative being latitude South and longitude West."""
            """\n\nTo calculate the latitude and longitude from a grid locator, use `/latlong`"""
        )
        await ctx.send(embed=await self._grid_sq_lookup_core(ctx, lat, lon))

    # endregion

    # region latlong

    async def _location_lookup_core(
        self, ctx: Union[ApplicationContext, commands.Context], grid: str
    ) -> Embed:
        grid_obj = gridtools.Grid(grid)

        embed = cmn.embed_factory(ctx)
        embed.title = f"Latitude and Longitude for {grid_obj}"
        embed.colour = cmn.colours.good
        embed.description = f"**{grid_obj.lat:.5f}, {grid_obj.long:.5f}**"
        return embed

    @grid_cat.command(
        name="latlong",
    )
    async def _location_lookup_slash(self, ctx: ApplicationContext, grid: str):
        (
            """Calculates the latitude and longitude for the center of a grid locator."""
            """\n\nTo calculate the grid locator from a latitude and longitude, use `/grid`"""
        )
        await ctx.send_response(embed=await self._location_lookup_core(ctx, grid))

    @commands.command(
        name="latlong", aliases=["latlon", "loc", "ungrid"], category=cmn.Cats.CALC
    )
    async def _location_lookup_prefix(self, ctx: commands.Context, grid: str):
        (
            """Calculates the latitude and longitude for the center of a grid locator."""
            """\n\nTo calculate the grid locator from a latitude and longitude, use `grid`"""
        )
        await ctx.send(embed=await self._location_lookup_core(ctx, grid))

    # endregion

    # region griddistance

    async def _dist_lookup_core(
        self, ctx: Union[ApplicationContext, commands.Context], grid1: str, grid2: str
    ) -> Embed:
        g1 = gridtools.Grid(grid1)
        g2 = gridtools.Grid(grid2)

        dist, bearing = gridtools.grid_distance(g1, g2)
        dist_mi = 0.6214 * dist

        embed = cmn.embed_factory(ctx)
        embed.title = f"Great Circle Distance and Bearing from {g1} to {g2}"
        embed.description = f"**Distance:** {dist:.1f} km ({dist_mi:.1f} mi)\n**Bearing:** {bearing:.1f}°"
        embed.colour = cmn.colours.good
        return embed

    @grid_cat.command(
        name="distance",
    )
    async def _dist_lookup_slash(self, ctx: ApplicationContext, grid1: str, grid2: str):
        """Calculates the great circle distance and azimuthal bearing between two grid locators."""
        await ctx.send_response(embed=await self._dist_lookup_core(ctx, grid1, grid2))

    @commands.command(
        name="griddistance",
        aliases=["griddist", "distance", "dist"],
        category=cmn.Cats.CALC,
    )
    async def _dist_lookup_prefix(self, ctx: commands.Context, grid1: str, grid2: str):
        """Calculates the great circle distance and azimuthal bearing between two grid locators."""
        await ctx.send(embed=await self._dist_lookup_core(ctx, grid1, grid2))

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(GridCog(bot))
