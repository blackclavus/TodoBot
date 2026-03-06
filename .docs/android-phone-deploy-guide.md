# Running TodoBot on an Old Android Phone

Use an old Android phone as a lightweight server (like a Raspberry Pi) to run the bot 24/7.

## Option 1: Termux (Easiest, No Root)

1. Install **Termux** from [F-Droid](https://f-droid.org/en/packages/com.termux/) (not Play Store — that version is outdated)
2. Inside Termux:
   ```bash
   pkg update && pkg upgrade
   pkg install python git
   pip install discord.py aiosqlite
   ```
3. Clone or copy your bot files:
   ```bash
   git clone <your-repo-url>
   cd TodoBot
   ```
   Alternatively, use `termux-setup-storage` to access shared storage and copy files manually via USB.
4. Run the bot:
   ```bash
   python bot.py
   ```
5. Keep it running when you close Termux:
   ```bash
   nohup python bot.py &
   ```
6. Install **Termux:Boot** (from F-Droid) to auto-start on reboot:
   - Create `~/.termux/boot/start-bot.sh`:
     ```bash
     #!/data/data/com.termux/files/usr/bin/sh
     cd ~/TodoBot
     python bot.py &
     ```
   - Make it executable:
     ```bash
     chmod +x ~/.termux/boot/start-bot.sh
     ```

## Option 2: UserLAnd (No Root)

- Install **UserLAnd** from the Play Store
- Set up a lightweight Linux distro (Ubuntu or Debian)
- Install Python and dependencies just like on a normal Linux server
- Run the bot inside the Linux environment

## Option 3: Linux Deploy (Root Required)

- Runs a full Linux distro via chroot
- Most "Raspberry Pi-like" experience
- Requires a rooted phone

## Important Android Settings

- **Keep the phone plugged in** — it will run 24/7
- **Disable battery optimization** for Termux so Android doesn't kill it in the background
  - Settings > Apps > Termux > Battery > Unrestricted
- **Disable screen timeout** or use a wakelock app
- **WiFi keep-alive** — make sure WiFi doesn't sleep when the screen is off
  - Settings > WiFi > Advanced > Keep WiFi on during sleep: Always

## Comparison: Android Phone vs Raspberry Pi

| | Old Android Phone | Raspberry Pi |
|---|---|---|
| Cost | Free (you already have it) | ~$35-75 |
| Setup | Termux, ~10 minutes | Flash OS, configure |
| Performance | Usually comparable or better | Depends on model |
| Reliability | Battery acts as built-in UPS | Needs separate UPS |
| Downside | Android may kill background processes | None major |

## Troubleshooting

- **Bot stops when phone sleeps**: Disable battery optimization for Termux and acquire a wakelock
- **WiFi disconnects**: Enable "Keep WiFi on during sleep" in WiFi advanced settings
- **Termux killed by Android**: Some manufacturers aggressively kill background apps — check [Don't Kill My App](https://dontkillmyapp.com/) for device-specific fixes
- **Storage permission issues**: Run `termux-setup-storage` to grant Termux access to shared storage
