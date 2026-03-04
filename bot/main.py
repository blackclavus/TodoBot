import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.database import init_db

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def load_cogs():
    for filename in os.listdir(os.path.join(os.path.dirname(__file__), "cogs")):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.load_extension(f"bot.cogs.{filename[:-3]}")


@bot.event
async def on_ready():
    await init_db()

    test_guild_id = os.getenv("TEST_GUILD_ID")
    if test_guild_id:
        guild = discord.Object(id=int(test_guild_id))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"Synced commands to test guild {test_guild_id}")
    else:
        await bot.tree.sync()
        print("Synced commands globally (may take up to 1 hour)")

    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} guild(s)")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))


def run():
    asyncio.run(main())
