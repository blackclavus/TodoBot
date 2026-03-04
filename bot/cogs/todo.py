from datetime import datetime, timezone

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands

from bot.database import DB_PATH


class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="start", description="Create a new todo/grocery list")
    @app_commands.guild_only()
    @app_commands.describe(name="Name for the new list")
    async def start(self, interaction: discord.Interaction, name: str):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM todo_lists WHERE user_id = ? AND guild_id = ? AND name = ?",
                (user_id, guild_id, name),
            )
            if await cursor.fetchone():
                await interaction.response.send_message(
                    f"You already have a list named **{name}**.", ephemeral=True
                )
                return

            await db.execute(
                "INSERT INTO todo_lists (user_id, guild_id, name, created_at) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, name, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()

        await interaction.response.send_message(
            f"Created list **{name}**! Use `/add` to start adding items."
        )

    @app_commands.command(name="add", description="Add an item to your most recent list")
    @app_commands.guild_only()
    @app_commands.describe(item="The item to add")
    async def add(self, interaction: discord.Interaction, item: str):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, name FROM todo_lists WHERE user_id = ? AND guild_id = ? ORDER BY id DESC LIMIT 1",
                (user_id, guild_id),
            )
            row = await cursor.fetchone()
            if not row:
                await interaction.response.send_message(
                    "You don't have any lists yet. Use `/start` to create one.",
                    ephemeral=True,
                )
                return

            list_id, list_name = row
            await db.execute(
                "INSERT INTO todo_items (list_id, content, added_at) VALUES (?, ?, ?)",
                (list_id, item, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()

        await interaction.response.send_message(
            f"Added **{item}** to **{list_name}**."
        )

    @app_commands.command(name="show", description="Show all items in a list")
    @app_commands.guild_only()
    @app_commands.describe(name="Name of the list to show")
    async def show(self, interaction: discord.Interaction, name: str):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM todo_lists WHERE user_id = ? AND guild_id = ? AND name = ?",
                (user_id, guild_id, name),
            )
            row = await cursor.fetchone()
            if not row:
                await interaction.response.send_message(
                    f"No list named **{name}** found.", ephemeral=True
                )
                return

            list_id = row[0]
            cursor = await db.execute(
                "SELECT content FROM todo_items WHERE list_id = ? ORDER BY id",
                (list_id,),
            )
            items = await cursor.fetchall()

        embed = discord.Embed(title=name, color=discord.Color.green())
        if items:
            body = "\n".join(f"{i}. {row[0]}" for i, row in enumerate(items, 1))
            embed.description = body
        else:
            embed.description = "This list is empty. Use `/add` to add items."
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Show all your lists in this server")
    @app_commands.guild_only()
    async def list_cmd(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                """
                SELECT tl.name, COUNT(ti.id) as item_count
                FROM todo_lists tl
                LEFT JOIN todo_items ti ON ti.list_id = tl.id
                WHERE tl.user_id = ? AND tl.guild_id = ?
                GROUP BY tl.id
                ORDER BY tl.id
                """,
                (user_id, guild_id),
            )
            lists = await cursor.fetchall()

        if not lists:
            await interaction.response.send_message(
                "You don't have any lists yet. Use `/start` to create one.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title="Your Lists", color=discord.Color.blue())
        lines = []
        for name, count in lists:
            lines.append(f"- **{name}** ({count} item{'s' if count != 1 else ''})")
        embed.description = "\n".join(lines)
        embed.set_footer(text=f"{len(lists)} list{'s' if len(lists) != 1 else ''}")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="complete", description="Mark a list as complete and delete it")
    @app_commands.guild_only()
    @app_commands.describe(name="Name of the list to complete")
    async def complete(self, interaction: discord.Interaction, name: str):
        user_id = interaction.user.id
        guild_id = interaction.guild.id

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM todo_lists WHERE user_id = ? AND guild_id = ? AND name = ?",
                (user_id, guild_id, name),
            )
            row = await cursor.fetchone()
            if not row:
                await interaction.response.send_message(
                    f"No list named **{name}** found.", ephemeral=True
                )
                return

            list_id = row[0]
            await db.execute("DELETE FROM todo_items WHERE list_id = ?", (list_id,))
            await db.execute("DELETE FROM todo_lists WHERE id = ?", (list_id,))
            await db.commit()

        await interaction.response.send_message(f"List **{name}** completed and removed!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Todo(bot))
