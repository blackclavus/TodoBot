# TodoBot

A Discord bot for managing todo and grocery lists using slash commands. Each user gets their own per-server lists stored in SQLite.

## Features

- Create named lists per server
- Add items to your most recent list
- View list contents with numbered items
- See all your lists at a glance
- Mark lists as complete to remove them

## Commands

| Command | Description |
|---------|-------------|
| `/start <name>` | Create a new list |
| `/add <item>` | Add an item to your most recent list |
| `/show <name>` | Show all items in a list |
| `/list` | Show all your lists in this server |
| `/complete <name>` | Mark a list as complete and delete it |

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/blackclavus/TodoBot.git
   cd TodoBot
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in:
   - `DISCORD_TOKEN` — Your bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
   - `TEST_GUILD_ID` — (Optional) A guild ID for instant slash command sync during development

4. **Run the bot**
   ```bash
   python -m bot
   ```

## Tech Stack

- [discord.py](https://discordpy.readthedocs.io/) — Discord API wrapper
- [aiosqlite](https://aiosqlite.omnilib.dev/) — Async SQLite
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Environment variable loading
