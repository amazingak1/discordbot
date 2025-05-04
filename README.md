# 🤖 MultiPurpose Discord Bot

A powerful and customizable multipurpose Discord bot built using `discord.py`.  
Includes features like polls, reminders, memes, subreddit integration, Gemini AI, and more.

---

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
- `!avatar [user]` — Shows avatar of the mentioned user (or yours).
- `!r <subreddit> [count]` — Sends images from a specified subreddit.
- `!nsfw <subreddit> [count]` — Sends NSFW content (image, video, gif) in NSFW channels only.
- `!foodporn` — Delicious food pics from the subreddit.

### 📬 Messaging
- `!send <#channel> <message>` — Send messages to a channel (admin only).
- `/send` — Slash version of `!send`.

### 💡 AI Integration (Gemini)
- `!ask <query>` — Ask the Gemini AI a question.
- `!resetchat` — Reset the conversation thread with Gemini.

### 📊 Attendance Calculator
- `!attendance <total_classes> <attended>` — Find how many classes you can miss and still have 75% attendance.

---

## ⚙️ Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/yourbotname.git
   cd yourbotname
