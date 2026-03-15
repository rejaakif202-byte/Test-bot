# 🌸 Mitsuri Kanroji — Telegram Group Management Bot

A powerful Telegram group management bot built with **Pyrogram** and **MongoDB**.

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/mitsuri-bot.git
cd mitsuri-bot
```

### 2. Create `.env` file
```bash
cp .env.example .env
```
Fill in your credentials:
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
MONGO_URI=your_mongodb_uri
OPENAI_API_KEY=your_openai_key
```

### 3. Add start image
Place your start image at: `assets/start.jpg`

### 4. Run with Python
```bash
pip install -r requirements.txt
python bot.py
```

### 5. Run with Docker
```bash
docker build -t mitsuri-bot .
docker run --env-file .env mitsuri-bot
```

---

## 📋 Commands

### 👑 Admin Commands
| Command | Description |
|---------|-------------|
| `/ban` `/unban` `/sban` `/tban` `/dban` | Ban management |
| `/mute` `/unmute` `/smute` `/tmute` `/dmute` | Mute management |
| `/warn` `/unwarn` `/swarn` `/twarn` `/dwarn` | Warn management |
| `/setwarnlimit` | Set warn limit (3-5) |
| `/kick` | Kick a user |
| `/del` | Delete a message |
| `/purge` | Purge messages |
| `/pin` `/unpin` `/unpinall` | Pin management |
| `/lock` `/unlock` `/locktypes` | Lock types |
| `/blacklist` `/unblacklist` `/allblacklist` | Word blacklist |
| `/welcome` `/setwelcome` `/resetwelcome` | Welcome settings |
| `/goodbye` `/setgoodbye` `/resetgoodbye` | Goodbye settings |
| `/deleditmsg` `/setdelmsgtimer` | Edited message deletion |
| `/approve` `/unapprove` `/approveall` `/unapproveall` `/approvelist` | Approve system |
| `/filter` `/stop` `/stopall` `/filters` | Filter system |
| `/promote` `/fullpromote` `/demote` `/demoteall` | Promote system |
| `/tagall` `/stoptagall` | Tag all members |
| `/antiflood` `/setfloodtype` `/setfloodlimit` | Anti-flood |
| `/adminlist` | Show admins |

### ⭐ Sudo Commands
| Command | Description |
|---------|-------------|
| `/gban` `/ungban` `/gbanlist` | Global ban |
| `/gmute` `/ungmute` `/gmutelist` | Global mute |
| `/block` `/unblock` | Block from bot |
| `/blacklistchat` `/whitelistchat` `/allblacklistchats` | Chat blacklist |
| `/stats` | Bot statistics |

### 👤 Owner Only
| Command | Description |
|---------|-------------|
| `/addsudo` `/remsudo` `/sudolist` | Sudo management |
| `/broadcast` | Broadcast message |

### 💬 Member Commands
| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help |
| `/id` | Get user/chat ID |
| `/info` | User information |
| `/afk` | Set AFK status |
| `/font {text}` | Convert text fonts |
| `/gpt {question}` | Ask ChatGPT |
| `/yt {link}` | Download YouTube video |
| `/ig {link}` | Download Instagram reel |
| `/report` or `@admin` | Report to admins |

---

## 🛠️ Tech Stack
- **Pyrogram** — Telegram MTProto API
- **MongoDB + Motor** — Database
- **OpenAI** — GPT integration
- **yt-dlp** — YouTube & Instagram downloads
- **Python 3.11+**

---

## 👤 Owner
Bot by [@mitsuri_Zprobot](https://t.me/mitsuri_Zprobot)
Support: [ANIMEXVERSE](https://t.me/ANIMEXVERSE)
