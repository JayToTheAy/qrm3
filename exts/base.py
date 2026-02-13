"""
Base extension for qrm
---
Copyright (C) 2019-2023 classabbyamp, 0x5c

SPDX-License-Identifier: LiLiQ-Rplus-1.1
"""

import inspect
import random
import re
from typing import Iterable, Tuple, Union
import pathlib

import discord
import discord.ext.commands as commands
from discord import ApplicationContext, Embed, IntegrationType
from discord.ext.commands import Command, CommandError

import info
import common as cmn
from data import options as opt


class QrmHelpCommand(commands.HelpCommand):

    def __init__(self):
        super().__init__(
            command_attrs={
                "help": "Shows help about qrm or a command",
                "aliases": ["h"],
                "category": cmn.BoltCats.INFO,
            }
        )
        self.verify_checks = True
        self.context: commands.Context

    async def filter_commands(
        self, commands: Iterable[Command], **kwargs
    ) -> list[Command]:
        def sort_by_cat(cmds):
            ret = []
            bolt_cmds = {}
            for c in cmds:
                cat = c.__original_kwargs__.get("category", cmn.BoltCats.OTHER)
                if isinstance(cat, cmn.BoltCats):
                    if cat in bolt_cmds:
                        bolt_cmds[cat].append(c)
                    else:
                        bolt_cmds[cat] = [c]
                else:
                    ret.append(c)

            ret.sort(key=lambda c: c.__original_kwargs__["category"].name)

            for cat in cmn.BoltCats:
                if cat in bolt_cmds:
                    ret += sorted(bolt_cmds[cat], key=lambda c: c.name)

            return ret

        iterator = (
            commands if self.show_hidden else filter(lambda c: not c.hidden, commands)
        )

        if not self.verify_checks:
            return sort_by_cat(iterator)

        async def predicate(cmd):
            try:
                return await cmd.can_run(self.context)
            except CommandError:
                return False

        cmds = []
        for cmd in iterator:
            if await predicate(cmd):
                cmds.append(cmd)

        return sort_by_cat(cmds)

    async def get_bot_mapping(self):
        bot = self.context.bot
        mapping = {}

        for cmd in await self.filter_commands(bot.commands):
            cat = cmd.__original_kwargs__.get("category", cmn.BoltCats.OTHER)
            if cat in mapping:
                mapping[cat].append(cmd)
            else:
                mapping[cat] = [cmd]
        return mapping

    async def get_command_signature(self, command):
        parent = command.full_parent_name
        if command.aliases != []:
            aliases = ", ".join(command.aliases)
            fmt = command.name
            if parent:
                fmt = f"{parent} {fmt}"
            alias = fmt
            return f"{self.context.prefix}{alias} {command.signature}\n    *Aliases:* {aliases}"
        alias = command.name if not parent else f"{parent} {command.name}"
        return f"{self.context.prefix}{alias} {command.signature}"

    async def send_error_message(self, error):
        embed = cmn.embed_factory(self.context)
        embed.title = "qrm Help Error"
        embed.description = error
        embed.colour = cmn.colours.bad
        await self.context.send(embed=embed)

    async def send_bot_help(self, mapping):
        embed = cmn.embed_factory(self.context)
        embed.title = "qrm Help"
        embed.description = (
            f"For command-specific help and usage, use `{self.context.prefix}help [command name]`."
            " Many commands have shorter aliases."
        )
        if isinstance(self.context.bot.command_prefix, list):
            embed.description += (
                " All of the following prefixes work with the bot: `"
                + "`, `".join(self.context.bot.command_prefix)
                + "`."
            )
        mapping = await mapping

        for cat, cmds in mapping.items():
            if cmds == []:
                continue
            names = sorted([cmd.name for cmd in cmds])
            if cat is not None:
                embed.add_field(name=cat.value, value=", ".join(names), inline=False)
            else:
                embed.add_field(name="Other", value=", ".join(names), inline=False)
        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        if self.verify_checks:
            if not await command.can_run(self.context):
                raise commands.CheckFailure
            for p in command.parents:
                if not await p.can_run(self.context):
                    raise commands.CheckFailure
        embed = cmn.embed_factory(self.context)
        embed.title = await self.get_command_signature(command)
        embed.description = command.help
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        if self.verify_checks and not await group.can_run(self.context):
            raise commands.CheckFailure
        embed = cmn.embed_factory(self.context)
        embed.title = await self.get_command_signature(group)
        embed.description = group.help
        for cmd in await self.filter_commands(group.commands, sort=True):
            embed.add_field(
                name=await self.get_command_signature(cmd),
                value=cmd.help if cmd.help else "",
                inline=False,
            )
        await self.context.send(embed=embed)


class BaseCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.changelog = parse_changelog()
        commit_file = pathlib.Path("git_commit")
        dot_git = pathlib.Path(".git")
        if commit_file.is_file():
            with commit_file.open() as f:
                self.commit = f.readline().strip()[:7]
        elif dot_git.is_dir():
            head_file = pathlib.Path(dot_git, "HEAD")
            if head_file.is_file():
                with head_file.open() as hf:
                    head = hf.readline().split(": ")[1].strip()
                branch_file = pathlib.Path(dot_git, head)
                if branch_file.is_file():
                    with branch_file.open() as bf:
                        self.commit = bf.readline().strip()[:7]
        else:
            self.commit = ""
        self.bot_invite = ""
        if self.bot.user:
            self.bot_invite = (
                f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}"
                f"&scope=bot&permissions={opt.invite_perms}"
            )

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot_invite and self.bot.user:
            self.bot_invite = (
                f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}"
                f"&scope=bot&permissions={opt.invite_perms}"
            )

    # region info

    async def _info_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        """Shows info about qrm."""
        embed = cmn.embed_factory(ctx)
        embed.title = "About qrm"
        embed.description = inspect.cleandoc(info.description)
        embed.add_field(name="Authors", value=", ".join(info.authors))
        embed.add_field(name="License", value=info.license)
        embed.add_field(
            name="Version",
            value=f"v{info.release} {'(`' + self.commit + '`)' if self.commit else ''}",
        )
        embed.add_field(
            name="Contributing", value=inspect.cleandoc(info.contributing), inline=False
        )
        if info.bot_server:
            embed.add_field(name="Official Server", value=info.bot_server, inline=False)
        if info.donating:
            embed.add_field(
                name="Donate",
                value=info.donating,
                inline=False,
            )
        if opt.enable_invite_cmd and (await self.bot.application_info()).bot_public:
            embed.add_field(
                name="Invite qrm to Your Server", value=self.bot_invite, inline=False
            )
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=str(self.bot.user.avatar.url))
        return embed

    @commands.slash_command(
        name="info",
        integration_types={
            IntegrationType.guild_install,
            IntegrationType.user_install,
        },
    )
    async def _info_slash(self, ctx: ApplicationContext):
        """Shows info about qrm."""
        await ctx.send_response(embed=await self._info_core(ctx))

    @commands.command(name="info", aliases=["about"], category=cmn.BoltCats.INFO)
    async def _info_prefix(self, ctx: commands.Context):
        """Shows info about qrm."""
        await ctx.send(embed=await self._info_core(ctx))

    # endregion

    # region ping

    async def _ping_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Tuple[str, Embed]:
        """Shows the current latency to the discord endpoint."""
        embed = cmn.embed_factory(ctx)
        content = ""
        content = ctx.message.author.mention if random.random() < 0.05 else ""
        embed.title = "🏓 **Pong!**"
        embed.description = f"Current ping is {self.bot.latency*1000:.1f} ms"
        return (content, embed)

    @commands.slash_command(
        name="ping",
        integration_types={
            IntegrationType.guild_install,
            IntegrationType.user_install,
        },
    )
    async def _ping_slash(self, ctx: ApplicationContext):
        """Shows the current latency to the discord endpoint."""
        content, embed = await self._ping_core(ctx)
        await ctx.send_response(content, embed=embed)

    @commands.command(name="ping", category=cmn.BoltCats.INFO)
    async def _ping_prefix(self, ctx: commands.Context):
        """Shows the current latency to the discord endpoint."""
        content, embed = await self._ping_core(ctx)
        await ctx.send(content, embed=embed)

    # endregion

    # region changelog

    async def _changelog_core(
        self, ctx: Union[ApplicationContext, commands.Context], version: str = "latest"
    ) -> Embed:
        """Shows what has changed in a bot version. Defaults to the latest version."""
        embed = cmn.embed_factory(ctx)
        embed.title = "qrm Changelog"
        embed.description = (
            "For a full listing, visit [GitHub](https://"
            "github.com/JayToTheAy/qrm3/blob/master/CHANGELOG.md)."
        )
        changelog = self.changelog
        vers = list(changelog.keys())
        vers.remove("Unreleased")

        version = version.lower()

        if version == "latest":
            version = info.release
        if version == "unreleased":
            version = "Unreleased"

        try:
            log = changelog[version]
        except KeyError:
            embed.title += ": Version Not Found"
            embed.description += "\n\n**Valid versions:** latest, "
            embed.description += ", ".join(vers)
            embed.colour = cmn.colours.bad
            return embed

        if "date" in log:
            embed.description += f"\n\n**v{version}** ({log['date']})"
        else:
            embed.description += f"\n\n**v{version}**"
        embed = await format_changelog(log, embed)

        return embed

    @commands.slash_command(
        name="changelog",
        integration_types={
            IntegrationType.guild_install,
            IntegrationType.user_install,
        },
    )
    async def _changelog_slash(self, ctx: ApplicationContext, version: str = "latest"):
        """Shows what has changed in a bot version. Defaults to the latest version."""
        await ctx.send_response(embed=await self._changelog_core(ctx, version))

    @commands.command(name="changelog", aliases=["clog"], category=cmn.BoltCats.INFO)
    async def _changelog_prefix(self, ctx: commands.Context, version: str = "latest"):
        """Shows what has changed in a bot version. Defaults to the latest version."""
        await ctx.send(embed=await self._changelog_core(ctx, version))

    # endregion

    # region issue

    async def _issue_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        """Shows how to create a bug report or feature request about the bot."""
        embed = cmn.embed_factory(ctx)
        embed.title = "Found a bug? Have a feature request?"
        embed.description = inspect.cleandoc(info.issue_tracker)
        return embed

    @commands.slash_command(
        name="issue",
        integration_types={
            IntegrationType.guild_install,
            IntegrationType.user_install,
        },
    )
    async def _issue_slash(self, ctx: ApplicationContext):
        """Shows how to create a bug report or feature request about the bot."""
        await ctx.send_response(embed=await self._issue_core(ctx))

    @commands.command(name="issue", category=cmn.BoltCats.INFO)
    async def _issue_prefix(self, ctx: commands.Context):
        """Shows how to create a bug report or feature request about the bot."""
        await ctx.send(embed=await self._issue_core(ctx))

    # endregion

    # region invite

    async def _invite_core(
        self, ctx: Union[ApplicationContext, commands.Context]
    ) -> Embed:
        """Generates a link to invite the bot to a server."""
        if not (await self.bot.application_info()).bot_public:
            raise commands.DisabledCommand
        embed = cmn.embed_factory(ctx)
        embed.title = "Invite qrm to Your Server!"
        embed.description = self.bot_invite
        return embed

    @commands.slash_command(
        name="invite",
        integration_types={
            IntegrationType.guild_install,
            IntegrationType.user_install,
        },
    )
    async def _invite_slash(self, ctx: ApplicationContext):
        """Generates a link to invite the bot to a server."""
        await ctx.send_response(embed=await self._invite_core(ctx))

    @commands.command(
        name="invite", enabled=opt.enable_invite_cmd, category=cmn.BoltCats.INFO
    )
    async def _invite_prefix(self, ctx: commands.Context):
        """Generates a link to invite the bot to a server."""
        await ctx.send(embed=await self._invite_core(ctx))

    # endregion

    # region echo - prefix only

    @commands.command(name="echo", aliases=["e"], category=cmn.BoltCats.ADMIN)
    @commands.check(cmn.check_if_owner)
    async def _echo(
        self,
        ctx: commands.Context,
        channel: Union[cmn.GlobalChannelConverter, commands.UserConverter],
        *,
        msg: str,
    ):
        """Sends a message in a channel as qrm. Accepts channel/user IDs/mentions.
        Channel names are current-guild only.
        Does not work with the ID of the bot user."""
        if isinstance(channel, discord.ClientUser):
            raise commands.BadArgument("Can't send to the bot user!")
        await ctx.send(msg)

    # endregion


def parse_changelog():
    changelog = {}
    ver = ""
    heading = ""

    with open("CHANGELOG.md") as changelog_file:
        for line in changelog_file.readlines():
            if line.strip() == "":
                continue
            if re.match(r"##[^#]", line):
                ver_match = re.match(
                    r"\[(.+)\](?: - )?(\d{4}-\d{2}-\d{2})?", line.lstrip("#").strip()
                )
                if ver_match is not None:
                    ver = ver_match.group(1)
                    changelog[ver] = dict()
                    if ver_match.group(2):
                        changelog[ver]["date"] = ver_match.group(2)
            elif re.match(r"###[^#]", line):
                heading = line.lstrip("#").strip()
                changelog[ver][heading] = []
            elif ver != "" and heading != "":
                if line.startswith("-"):
                    changelog[ver][heading].append(line.lstrip("-").strip())
    return changelog


async def format_changelog(log: dict, embed: discord.Embed):
    for header, lines in log.items():
        formatted = ""
        if header != "date":
            for line in lines:
                formatted += f"- {line}\n"
            embed.add_field(name=f"**{header}**", value=formatted, inline=False)
    return embed


def setup(bot: commands.Bot):
    bot.add_cog(BaseCog(bot))
    bot._original_help_command = bot.help_command
    bot.help_command = QrmHelpCommand()


def teardown(bot: commands.Bot):
    bot.help_command = bot._original_help_command
