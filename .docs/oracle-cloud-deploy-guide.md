# Deploying TodoBot on Oracle Cloud Free Tier

## Overview

Oracle Cloud offers an **always-free** ARM VM instance — no trial, no expiration. Once your instance is running, it stays up permanently at zero cost.

### What You Get (Free Tier)

| Resource | Amount |
|---|---|
| VM | 1 Ampere ARM instance (up to 4 CPU / 24 GB RAM) |
| Storage | 200 GB block storage |
| Network | 10 TB/month outbound |
| OS | Ubuntu 22.04+ recommended |

A Discord bot uses a tiny fraction of this. You can run multiple bots on one instance.

---

## Step 1: Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in your details — a **credit card is required for verification only** (you will not be charged)
4. **Choose your home region carefully** — you cannot change it later
   - Pick a **less popular region** for better availability (e.g., US Midwest/Chicago, Canada/Toronto, Japan/Tokyo)
   - Avoid US East (Ashburn) and US West (Phoenix) — highest demand

---

## Step 2: Create a Compute Instance

1. Go to **Menu → Compute → Instances → Create Instance**
2. Configure:
   - **Name**: `discord-bot` (or whatever you like)
   - **Image**: Ubuntu 22.04 (or 24.04 if available) — **Canonical Ubuntu** under "Change image"
   - **Shape**: Click **"Change shape"** → **Ampere** → `VM.Standard.A1.Flex`
     - Set **1 OCPU** and **6 GB RAM** (plenty for multiple bots)
   - **Networking**: Use defaults (creates a VCN automatically)
   - **SSH Key**: Click **"Generate a key pair"** → **Download both keys** (save them safely!)
     - Or upload your own public key if you already have one (`~/.ssh/id_rsa.pub`)
3. Click **"Create"**

### If You Get "Out of Capacity" Error

This is common. The free ARM instances are in high demand. Options:
- **Retry manually** every few hours, especially early morning (UTC)
- **Try a different shape config** (e.g., 1 OCPU / 2 GB instead of 1/6)
- Be patient — it may take a few days

Once created, the instance **will not be reclaimed** as long as it's running.

---

## Step 3: Configure Firewall (Security List)

Oracle blocks most traffic by default. For a Discord bot you only need **outbound** access (which is allowed by default), but you need SSH access:

1. Go to **Menu → Networking → Virtual Cloud Networks**
2. Click your VCN → **Security Lists** → **Default Security List**
3. Verify there's an **ingress rule** for TCP port **22** (SSH) — it should exist by default
4. No other ports needed — the bot connects outbound to Discord

---

## Step 4: SSH Into Your Instance

Find your instance's **public IP** on the instance details page.

```bash
# On your PC (Git Bash on Windows, or terminal on Mac/Linux)

# If you downloaded Oracle's generated key:
chmod 600 ~/Downloads/ssh-key-*.key
ssh -i ~/Downloads/ssh-key-*.key ubuntu@<YOUR_INSTANCE_IP>

# If you used your own SSH key:
ssh ubuntu@<YOUR_INSTANCE_IP>
```

You should see the Ubuntu prompt. You're in.

---

## Step 5: Server Setup

### Install dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-venv python3-pip git -y
```

### Clone the project

```bash
cd ~
git clone https://github.com/blackclavus/TodoBot.git
cd TodoBot
```

### Create virtual environment and install packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure environment

```bash
cp .env.example .env
nano .env
```

Fill in:
- `DISCORD_TOKEN=your_bot_token_here`
- `TEST_GUILD_ID=your_test_guild_id` (optional)

Save: `Ctrl+O`, `Enter`, `Ctrl+X`

### Test run

```bash
python -m bot
```

Verify the bot comes online in Discord and responds to commands. Then `Ctrl+C` to stop.

---

## Step 6: Set Up systemd Service (Auto-Start on Boot)

This ensures the bot runs 24/7 and auto-restarts if it crashes or the server reboots.

### Create the service file

```bash
sudo nano /etc/systemd/system/todobot.service
```

Paste the following:

```ini
[Unit]
Description=TodoBot Discord Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/TodoBot
ExecStart=/home/ubuntu/TodoBot/venv/bin/python -m bot
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/TodoBot/.env

[Install]
WantedBy=multi-user.target
```

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

### Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable todobot     # start on boot
sudo systemctl start todobot      # start now
```

### Useful commands

```bash
sudo systemctl status todobot     # check if running
sudo journalctl -u todobot -f     # view live logs
sudo systemctl restart todobot    # restart after code changes
sudo systemctl stop todobot       # stop the bot
```

---

## Step 7: Updating the Bot

When you push changes to GitHub:

```bash
cd ~/TodoBot
git pull
sudo systemctl restart todobot
```

---

## Oracle Free Tier Idle Policy

Oracle may reclaim **idle** always-free instances. An instance is considered idle if **all** of these are true for 7 days:
- CPU utilization < 10%
- Network usage < 10%
- Memory utilization < 10%

A Discord bot maintaining a WebSocket connection to Discord should keep the instance active enough. If you're worried, you can add a simple cron job:

```bash
# Optional: add a small CPU ping every hour to prevent idle detection
(crontab -l 2>/dev/null; echo "0 * * * * dd if=/dev/urandom bs=1M count=10 of=/dev/null 2>/dev/null") | crontab -
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Out of Capacity" on instance creation | Retry later, try smaller shape, or different config |
| Can't SSH in | Check security list has port 22 open, verify correct key file |
| Bot crashes after SSH disconnect | Make sure you're using the systemd service, not running directly |
| Bot not responding to commands | Check logs: `sudo journalctl -u todobot -f` |
| `pip install` fails | Ensure venv is activated: `source venv/bin/activate` |
| Permission denied on .env | `chmod 600 .env` |

---

## Summary

| What | Detail |
|---|---|
| Cost | $0 forever |
| Uptime | 99.9% (Oracle's SLA) |
| Multiple bots | Yes — plenty of resources |
| SQLite | Works perfectly (persistent disk) |
| Maintenance | Occasional `sudo apt update && sudo apt upgrade` |
