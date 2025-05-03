import os
import re
import math
import asyncio
import aiohttp
import google.generativeai as genai
import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import logging
import webserver

# ─── Start Time ─────────────────────────────────────────────────────────────
start_time = datetime.datetime.utcnow()
uptime_message = None
reminders = []  # In-memory reminders list

# ─── Environment Variables ───────────────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SUPPORT_CHANNEL_ID = 1367611989219741707
UPTIME_CHANNEL_ID = 915291246396833832
LOG_CHANNEL_ID = 123456789012345678  # Replace with your log channel ID

if not TOKEN:
    raise ValueError("❌ Discord bot TOKEN is missing from environment variables.")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing from environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# ─── Bot Setup ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=['!', '`'], intents=intents)
tree = bot.tree

# ─── Logging Setup ───────────────────────────────────────────────────────────
class DiscordLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    async def send_log(self, log_entry):
        await bot.wait_until_ready()
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(f"📝 Log: `{log_entry}`")

    def emit(self, record):
        log_entry = self.format(record)
        asyncio.run_coroutine_threadsafe(self.send_log(log_entry), bot.loop)

logger = logging.getLogger("discord_logger")
logger.setLevel(logging.INFO)
logger.addHandler(DiscordLogHandler())

# ─── Uptime Task ─────────────────────────────────────────────────────────────
@tasks.loop(minutes=1)
async def send_uptime():
    global uptime_message
    now = datetime.datetime.utcnow()
    delta = now - start_time
    days, rem = divmod(delta.total_seconds(), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

    embed = discord.Embed(
        title="\u23f1\ufe0f Bot Uptime",
        description=f"**{uptime_str}**",
        color=discord.Color.green()
    )

    channel = bot.get_channel(UPTIME_CHANNEL_ID)
    if uptime_message:
        try:
            await uptime_message.edit(embed=embed)
        except discord.NotFound:
            uptime_message = await channel.send(embed=embed)
    else:
        if channel:
            embed.description += "\n✅ Bot is now online!"
            uptime_message = await channel.send(embed=embed)

# ─── Utility Functions ───────────────────────────────────────────────────────
def convert_to_seconds(time_str: str) -> int:
    pattern = r"(\d+)([hms])"
    matches = re.findall(pattern, time_str.lower())
    seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit == 'h':
            seconds += value * 3600
        elif unit == 'm':
            seconds += value * 60
        elif unit == 's':
            seconds += value
    return seconds

# ─── Bot Events ──────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    await tree.sync()
    print(f'✅ Logged in as {bot.user} and synced slash commands!')
    logger.info("Bot is online and commands synced.")
    if not send_uptime.is_running():
        send_uptime.start()
    await bot.change_presence(activity=discord.Game(name="!helpme for commands"))

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.content.lower() == "who is your daddy":
        await message.channel.send(f"My daddy is <@769919104702218300> 😎")

    if isinstance(message.channel, discord.DMChannel):
        support_channel = bot.get_channel(SUPPORT_CHANNEL_ID)
        if support_channel:
            embed = discord.Embed(
                title="📩 New Support Message",
                description=message.content,
                color=discord.Color.orange()
            )
            avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
            embed.set_author(name=f"{message.author}", icon_url=avatar_url)
            embed.set_footer(text=f"User ID: {message.author.id}")
            await support_channel.send(embed=embed)
            await message.channel.send("✅ Your message has been forwarded to the support team.")
        else:
            await message.channel.send("❌ Support channel not found.")
        return

    await bot.process_commands(message)

# ─── Commands ────────────────────────────────────────────────────────────────

@bot.command()
async def update(ctx):
    now = datetime.datetime.utcnow()
    delta = now - start_time
    days, remainder = divmod(delta.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    await ctx.send(f"🔄 Bot updated successfully!")
    logger.info(f"Bot manually updated by {ctx.author}. Uptime: {uptime_str}")

# (rest of your commands stay unchanged)

@bot.command()
async def helpme(ctx):
    embed = discord.Embed(
        title="📚 Bot Commands",
        description="Here's a list of what I can do!",
        color=discord.Color.blurple()
    )
    embed.add_field(name="🎯 Basic", value="`!hello`, `!ping`, `!echo <msg>`, `!info`", inline=False)
    embed.add_field(name="🧠 Gemini", value="`!ask <query>`", inline=False)
    embed.add_field(name="📅 Scheduling", value="`!remindme`, `!schedule`", inline=False)
    embed.add_field(name="📊 Attendance", value="`!at <total> <attended>`", inline=False)
    embed.add_field(name="📬 Messaging", value="`!send`, `!dm`", inline=False)
    embed.add_field(name="🕒 Uptime", value="`!uptime`, `!update`", inline=False)
    embed.set_footer(text="Use `/` for slash commands too!")
    await ctx.send(embed=embed)

# ─── Run the Bot ─────────────────────────────────────────────────────────────
webserver.keep_alive()
bot.run(TOKEN)
