"""
Contest Calendar extension for qrm
---
Copyright (C) 2021-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

from typing import Union
from datetime import datetime, timedelta
from dateutil import tz

import aiohttp
import icalendar

import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType, ui, Interaction, ButtonStyle

import common as cmn

class ContestCalendarView(ui.View):
    def __init__(self, ctx: Union[ApplicationContext, commands.Context], cal: icalendar.Calendar, rundate: datetime.date):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.cal = cal
        self.rundate = rundate
        self.earliest_rundate: datetime.date = self.cal.events[0].start.date() if 0 < len(self.cal.events) else self.rundate
        self.latest_rundate: datetime.date = self.cal.events[-1].start.date() if 0 < len(self.cal.events) else self.rundate

        self.contestCalendarButton = ui.Button(label="Contest Calendar", style=ButtonStyle.link, url="https://www.contestcalendar.com/weeklycont.php", row=0)
        self.add_item(self.contestCalendarButton)

        self._update_buttons()

    @ui.button(label="Previous Day", style=ButtonStyle.primary, row=0)
    async def previous_day_button_callback(self, button, interaction):
        self.rundate -= timedelta(days=1)
        self._update_buttons()
        embed = self._update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Next Day", style=ButtonStyle.primary, row=0)
    async def next_day_button_callback(self, button: ui.Button, interaction: Interaction):
        self.rundate += timedelta(days=1)
        self._update_buttons()
        embed = self._update_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        self.previous_day_button_callback.disabled = True
        self.next_day_button_callback.disabled = True

        if self.message:
            await self.message.edit(view=self)

    def _update_embed(self):
        embed = Embed()
        embed = cmn.embed_factory(self.ctx)
        embed.title = f"Contest Calendar - {self.rundate}"

        events = self._events_on_rundate()
        desc_building = ""
        if events:
            for event in events:
                desc_building += f"### [{event.get('SUMMARY')}]({event.get('URL')})\n**{event.start.strftime('%Y-%m-%d %H:%M')}Z to {event.end.strftime('%Y-%m-%d %H:%M')}Z**\n"
        embed.description = desc_building if desc_building else "No contests on this date."
        embed.colour = cmn.colours.good
        return embed

    def _update_buttons(self):
        order = [
        self.previous_day_button_callback,
        self.next_day_button_callback,
        self.contestCalendarButton,
    ]
        self.previous_day_button_callback.disabled = self.rundate <= self.earliest_rundate
        self.next_day_button_callback.disabled = self.rundate >= self.latest_rundate
        self.children.sort(key=order.index)

        self.timeout = 180  # Reset the timeout each time a button is pressed
  


    def _events_on_rundate(self) -> list:
        events = []

        for event in self.cal.events:
            if event.start.date() <= self.rundate <= event.end.date():
                events.append(event)
        return events

class ContestCalendarCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rundate = datetime.now(tz=tz.tzutc()).date()

    # region contests

    async def _get_ical(self) -> Union[icalendar.Calendar, None]:
        url = "https://www.contestcalendar.com/weeklycontics.php"
        async with aiohttp.ClientSession(
            connector=self.bot.qrm.connector, connector_owner=False
        ) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.text()
                    calendar = icalendar.Calendar.from_ical(data)
                    return calendar

                else:
                    return None

    @commands.slash_command(
        name="contests",
        integration_types={IntegrationType.guild_install, IntegrationType.user_install},
    )
    async def _contests_slash(self, ctx: ApplicationContext, private: bool = False):
        await ctx.defer(ephemeral=private)
        cal = await self._get_ical()
        view = ContestCalendarView(ctx, cal, self.rundate)
        embed = view._update_embed()
        await ctx.send_followup(embed=embed, view=view, ephemeral=private)

    @commands.command(
        name="contests", aliases=["cc", "tests"], category=cmn.Cats.LOOKUP
    )
    async def _contests_prefix(self, ctx: commands.Context):
        with ctx.typing():
            cal = await self._get_ical()
            view = ContestCalendarView(ctx, cal, self.rundate) # We don't use the view on the prefix command, we just keep it for the embed
            embed = view._update_embed()
            await ctx.send(embed=embed)

    # endregion


def setup(bot: commands.Bot):
    bot.add_cog(ContestCalendarCog(bot))
