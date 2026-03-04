import os
import platform
import sys
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.now(timezone.utc)

    @app_commands.command(name="sync", description="Sync slash commands (owner only)")
    @app_commands.describe(guild_only="Sync to test guild only (instant)")
    async def sync(
        self, interaction: discord.Interaction, guild_only: bool = False
    ):
        if not await interaction.client.is_owner(interaction.user):
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        if guild_only:
            test_guild_id = os.getenv("TEST_GUILD_ID")
            if not test_guild_id:
                await interaction.followup.send(
                    "TEST_GUILD_ID is not set in the environment."
                )
                return
            guild = discord.Object(id=int(test_guild_id))
            self.bot.tree.copy_global_to(guild=guild)
            synced = await self.bot.tree.sync(guild=guild)
            await interaction.followup.send(
                f"Synced {len(synced)} command(s) to test guild."
            )
        else:
            synced = await self.bot.tree.sync()
            await interaction.followup.send(
                f"Synced {len(synced)} command(s) globally."
            )

    @app_commands.command(name="status", description="Show bot status (owner only)")
    async def status(self, interaction: discord.Interaction):
        if not await interaction.client.is_owner(interaction.user):
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        uptime = datetime.now(timezone.utc) - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(title="Bot Status", color=discord.Color.green())
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms"
        )
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)))
        embed.add_field(
            name="Uptime", value=f"{hours}h {minutes}m {seconds}s"
        )
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="discord.py", value=discord.__version__)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="reload", description="Hot-reload a cog (owner only)")
    @app_commands.describe(cog="Name of the cog to reload (e.g. todo, general, admin)")
    async def reload(self, interaction: discord.Interaction, cog: str):
        if not await interaction.client.is_owner(interaction.user):
            await interaction.response.send_message(
                "Only the bot owner can use this command.", ephemeral=True
            )
            return

        extension = f"bot.cogs.{cog}"
        try:
            await self.bot.reload_extension(extension)
        except commands.ExtensionError as e:
            await interaction.response.send_message(
                f"Failed to reload **{cog}**: {e}", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Reloaded **{cog}** successfully.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
