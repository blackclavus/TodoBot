import logging
import re
from datetime import date, datetime, time, timedelta, timezone

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands, tasks

from bot.database import DB_PATH

logger = logging.getLogger(__name__)

DEFAULT_TZ = timezone(timedelta(hours=7))

REPEAT_CHOICES = [
    app_commands.Choice(name="Daily", value="daily"),
    app_commands.Choice(name="Weekly", value="weekly"),
    app_commands.Choice(name="Monthly", value="monthly"),
]

DATE_SUGGESTIONS = ["today", "tomorrow", "next week", "next month"]


def parse_date(text: str) -> date:
    """Parse a date string into a date object. Raises ValueError on failure."""
    text = text.strip().lower()
    now_local = datetime.now(DEFAULT_TZ).date()

    if text == "today":
        return now_local
    if text == "tomorrow":
        return now_local + timedelta(days=1)
    if text == "next week":
        return now_local + timedelta(weeks=1)
    if text == "next month":
        # Advance by one calendar month
        year = now_local.year + (now_local.month // 12)
        month = (now_local.month % 12) + 1
        day = min(now_local.day, 28)  # safe for all months
        return date(year, month, day)

    # Try dd/mm/yy
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        return date(year, month, day)

    raise ValueError(f"Unrecognized date format: `{text}`")


def parse_time(text: str) -> time:
    """Parse HH:MM into a time object. Raises ValueError on failure."""
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text.strip())
    if not m:
        raise ValueError("Time must be in `HH:MM` 24-hour format.")
    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Time must be in `HH:MM` 24-hour format.")
    return time(hour, minute)


def compute_next_occurrence(remind_at: datetime, repeat: str) -> datetime:
    """Advance remind_at to the next future occurrence based on repeat interval."""
    now = datetime.now(timezone.utc)
    dt = remind_at
    while dt <= now:
        if repeat == "daily":
            dt += timedelta(days=1)
        elif repeat == "weekly":
            dt += timedelta(weeks=1)
        elif repeat == "monthly":
            year = dt.year + (dt.month // 12)
            month = (dt.month % 12) + 1
            day = min(dt.day, 28)
            dt = dt.replace(year=year, month=month, day=day)
    return dt


class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.check_reminders.start()

    async def cog_unload(self):
        self.check_reminders.cancel()

    reminder_group = app_commands.Group(
        name="reminder",
        description="Set, list, and cancel reminders",
        guild_only=True,
    )

    @reminder_group.command(name="set", description="Set a new reminder")
    @app_commands.describe(
        date="Date: today, tomorrow, next week, next month, or dd/mm/yy",
        time="Time in HH:MM 24-hour format (UTC+7)",
        text="What to remind you about",
        repeat="Optional repeat interval",
    )
    @app_commands.choices(repeat=REPEAT_CHOICES)
    async def reminder_set(
        self,
        interaction: discord.Interaction,
        date: str,
        time: str,
        text: str,
        repeat: app_commands.Choice[str] | None = None,
    ):
        try:
            parsed_date = parse_date(date)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        try:
            parsed_time = parse_time(time)
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return

        # Combine date + time as UTC+7, then convert to UTC for storage
        local_dt = datetime.combine(parsed_date, parsed_time, tzinfo=DEFAULT_TZ)
        utc_dt = local_dt.astimezone(timezone.utc)

        if utc_dt <= datetime.now(timezone.utc):
            await interaction.response.send_message(
                "That time is in the past. Please pick a future date/time.",
                ephemeral=True,
            )
            return

        repeat_value = repeat.value if repeat else None
        now_iso = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "INSERT INTO reminders (user_id, guild_id, channel_id, text, remind_at, repeat, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    interaction.user.id,
                    interaction.guild.id,
                    interaction.channel.id,
                    text,
                    utc_dt.isoformat(),
                    repeat_value,
                    now_iso,
                ),
            )
            reminder_id = cursor.lastrowid
            await db.commit()

        timestamp = int(utc_dt.timestamp())
        repeat_label = f" (repeats **{repeat.name}**)" if repeat else ""
        embed = discord.Embed(
            title="Reminder set",
            description=f"**{text}**\n<t:{timestamp}:F> (<t:{timestamp}:R>){repeat_label}",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"ID: {reminder_id}")
        await interaction.response.send_message(embed=embed)

    @reminder_set.autocomplete("date")
    async def date_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=s, value=s)
            for s in DATE_SUGGESTIONS
            if current.lower() in s
        ]

    @reminder_group.command(name="list", description="Show your active reminders")
    async def reminder_list(self, interaction: discord.Interaction):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, text, remind_at, repeat FROM reminders "
                "WHERE user_id = ? AND guild_id = ? ORDER BY remind_at",
                (interaction.user.id, interaction.guild.id),
            )
            rows = await cursor.fetchall()

        if not rows:
            await interaction.response.send_message(
                "You have no active reminders.", ephemeral=True
            )
            return

        lines = []
        for rid, text, remind_at, repeat in rows:
            utc_dt = datetime.fromisoformat(remind_at)
            ts = int(utc_dt.timestamp())
            repeat_label = f" [{repeat}]" if repeat else ""
            lines.append(f"**{rid}.** {text} - <t:{ts}:F> (<t:{ts}:R>){repeat_label}")

        embed = discord.Embed(
            title="Your Reminders",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text=f"{len(rows)} reminder{'s' if len(rows) != 1 else ''}"
        )
        await interaction.response.send_message(embed=embed)

    @reminder_group.command(name="cancel", description="Cancel a reminder by ID")
    @app_commands.describe(id="The reminder ID to cancel")
    async def reminder_cancel(self, interaction: discord.Interaction, id: int):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id FROM reminders WHERE id = ? AND user_id = ? AND guild_id = ?",
                (id, interaction.user.id, interaction.guild.id),
            )
            if not await cursor.fetchone():
                await interaction.response.send_message(
                    f"Reminder **#{id}** not found or doesn't belong to you.",
                    ephemeral=True,
                )
                return

            await db.execute("DELETE FROM reminders WHERE id = ?", (id,))
            await db.commit()

        await interaction.response.send_message(f"Reminder **#{id}** cancelled.")

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT id, user_id, channel_id, text, remind_at, repeat "
                "FROM reminders WHERE remind_at <= ?",
                (now_iso,),
            )
            due = await cursor.fetchall()

            for rid, user_id, channel_id, text, remind_at, repeat in due:
                utc_dt = datetime.fromisoformat(remind_at)
                late = (now - utc_dt) > timedelta(minutes=2)

                channel = self.bot.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(channel_id)
                    except discord.NotFound:
                        await db.execute("DELETE FROM reminders WHERE id = ?", (rid,))
                        continue
                    except discord.Forbidden:
                        continue

                late_note = "\n*(delivered late — bot was offline)*" if late else ""
                try:
                    await channel.send(
                        f"Hey <@{user_id}>, reminder: **{text}**{late_note}"
                    )
                except (discord.Forbidden, discord.HTTPException):
                    logger.warning("Could not send reminder %d to channel %d", rid, channel_id)
                    continue

                if repeat:
                    next_dt = compute_next_occurrence(utc_dt, repeat)
                    await db.execute(
                        "UPDATE reminders SET remind_at = ? WHERE id = ?",
                        (next_dt.isoformat(), rid),
                    )
                else:
                    await db.execute("DELETE FROM reminders WHERE id = ?", (rid,))

            await db.commit()

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
