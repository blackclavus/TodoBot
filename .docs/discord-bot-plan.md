# Discord Bot Plan — Python + discord.py

## Context
A comprehensive Discord bot built incrementally using Python and discord.py. Started with a minimal working bot with basic slash commands, then layered on AI and database features.

---

## Milestone 1: Minimal Bot
> Goal: A bot that comes online and responds to basic slash commands.

### 1.1 — Prerequisites
- **Python 3.10+** installed
- **Discord account** with a server you own/admin
- **Git** for version control
- **Code editor** (VS Code recommended)

### 1.2 — Discord Developer Portal Setup

**Create Application & Bot:**
1. Go to https://discord.com/developers/applications
2. Click **"New Application"** → name it → Create
3. Note down the **Application ID**
4. Go to **"Bot"** tab → Click **"Add Bot"** → confirm
5. Click **"Reset Token"** → copy and save securely (**never commit to git**)

**Configure Intents:**
- Under Bot tab, enable **Message Content Intent** (needed for AI features)

**Generate Invite Link:**
1. Go to **OAuth2 → URL Generator**
2. **Scopes**: select `bot` and `applications.commands`
3. **Bot Permissions**: Send Messages, Use Slash Commands, Embed Links
4. Copy the generated URL

**Invite Bot:**
1. Paste URL in browser → select your test server → Authorize
2. Bot appears in member list (offline until you run it)

### 1.3 — Project Structure (Milestone 1 — minimal)
```
discord-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point, bot startup
│   └── cogs/
│       ├── __init__.py
│       └── general.py        # Basic slash commands (/ping, /help)
├── .env                      # Secrets (NEVER commit)
├── .env.example              # Template for .env
├── .gitignore
└── requirements.txt
```

### 1.4 — Core Bot Code
- `bot/main.py` — Bot entry point with `commands.Bot`, cog loading, `on_ready` sync
- `bot/cogs/general.py` — `/ping`, `/hello`, `/serverinfo`

### 1.5 — Run & Verify
```bash
python -m bot
```
- Bot comes online in Discord
- `/ping` → responds with latency
- `/hello` → greets you
- Slash commands appear in Discord's command menu

---

## Milestone 2: Database Persistence
> Goal: Store data (command usage, chat history) in SQLite.

### Added Files
```
bot/services/db_service.py    # Async DB operations via aiosqlite
data/bot.db                   # Auto-created SQLite file
```

### Tables
- `command_logs` — tracks command usage (user, guild, command, timestamp)
- `user_settings` — per-user preferences
- `chat_history` — conversation history for `/chat` command

---

## Milestone 3: Claude AI Chat
> Goal: Bot responds to questions using Claude API.

### Added Files
```
bot/services/ai_service.py    # Claude API wrapper
bot/cogs/ai_chat.py           # /ask, /chat, /clearchat commands
```

### Features
- `/ask <question>` — single question → Claude response
- `/chat <message>` — persistent conversation with history stored in DB
- `/clearchat` — clear conversation history
- Long responses automatically split to fit Discord's 2000-char limit

---

## Milestone 4: Polish & Production Readiness
> Goal: Error handling, logging, admin tools.

### Added Files
```
bot/cogs/error_handler.py     # Global error handler
bot/cogs/admin.py             # /status, /reload, /sync
bot/config.py                 # Centralized settings
bot/utils/helpers.py          # Utility functions
```

### Final Project Structure
```
discord-bot/
├── bot/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── config.py
│   ├── cogs/
│   │   ├── __init__.py
│   │   ├── general.py
│   │   ├── ai_chat.py
│   │   ├── admin.py
│   │   └── error_handler.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   └── db_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── data/
│   └── bot.db
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── discord-bot-plan.md
├── setup-guide.md
└── commands-reference.md
```

---

## Milestone 5: Deployment

### Option A — Local (Development Only)
```bash
python -m bot
```

### Option B — Railway (Recommended)
1. Push to GitHub
2. https://railway.app → New Project → Deploy from GitHub
3. Add env vars (DISCORD_TOKEN, ANTHROPIC_API_KEY, DATABASE_PATH)
4. Auto-detects Python, deploys

### Option C — Render
1. Push to GitHub
2. https://render.com → New → Background Worker
3. Build: `pip install -r requirements.txt`
4. Start: `python -m bot`

### Option D — Self-hosted (VPS / Raspberry Pi)
Use systemd service for auto-restart:
```ini
[Unit]
Description=Discord Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/discord-bot
ExecStart=/home/youruser/discord-bot/venv/bin/python -m bot
Restart=always
EnvironmentFile=/home/youruser/discord-bot/.env

[Install]
WantedBy=multi-user.target
```

---

## Milestone 6: Adding Bot to More Servers

### Invite Flow
1. Use OAuth2 URL from Milestone 1.2
2. Share link with server admins → they authorize

### Permissions Summary
| Permission | Why |
|-----------|-----|
| Send Messages | Respond to commands |
| Use Slash Commands | Register `/commands` |
| Read Message History | AI conversation context |
| Embed Links | Rich embed responses |
