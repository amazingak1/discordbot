## 🛠️ Looking for Contributors: ModMail Feature
I'm currently looking for someone to help implement a ModMail system in this Discord bot.

### 🔧 Feature Description:
* Allow users to DM the bot and create a private thread or channel in a server (ModMail).
* Allow moderators to reply from the server channel, and the bot should forward messages back to the user's DMs.
* Optional: Support message logging, user blacklist, or mod-only reply options.
If you're interested in contributing or have questions, feel free to open an issue or submit a pull request!
---

# 🤖 MultiPurpose Discord Bot

A powerful and customizable multipurpose Discord bot built using `discord.py`.  
Includes features like polls, reminders, memes, subreddit integration, Gemini AI, and more.


## 🚀 Features

### 🎯 Basic Commands
- `!hello` — The bot greets you!
- `!ping` — Check the bot’s latency.
- `!info` — Get bot information.
- `!echo <message>` — Bot repeats your message.

### 📝 Polling
- `!poll <question> <option1> <option2> ...` — Create a reaction-based poll.
- `/poll` — Slash command with buttons and multiple options.

### ⏰ Reminders & Scheduling
- `!remindme <time> <task>` — Get reminded after a certain time (e.g. 1h30m).
- `!schedule <time> <event>` — Schedule an event/announcement.

### 🎨 Fun & Media
- `/meme` — Sends a random meme from the r/FingMemes subreddit.
- `/avatar [user]` — Shows avatar of the mentioned user (or yours).
- `!r <subreddit> [count]` — Sends images from a specified subreddit.
- `!food` — Delicious food pics from the subreddit.

### 📬 Messaging
- `!send <#channel> <message>` — Send messages to a channel (admin only).
- `/send` — Slash version of `!send`.

### 💡 AI Integration (Gemini)
- `!ask <query>` — Ask the Gemini AI a question.

### 📊 Attendance Calculator
- `!attendance/at <total_classes> <attended>` — Find how many classes you can miss and still have 75% attendance.

---

## ⚙️ Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourbotname.git
   cd yourbotname

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
3. Set up your `.env` file or directly add your Discord token in the config section.
4. Run the bot:
   ```bash
   python bot.py
---
# 📌 To-Do / Upcoming Features
* Custom prefix support
* Logging system
* Persistent reminders
* Slash command expansion
* Moderation utilities

# 🧠 Tech Stack
* Python 3.10+
* discord.py 
* Flask (optional web features)
* Google Gemini API
* Reddit JSON API
