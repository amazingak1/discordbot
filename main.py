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
import webserver


# ─── Start Time ─────────────────────────────────────────────────────────────
start_time = datetime.datetime.utcnow()
uptime_message = None

# ─── Environment Variables ───────────────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
NEWS_API_KEY = os.getenv("NEWS")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


SUPPORT_CHANNEL_ID = 1367611989219741707
UPTIME_CHANNEL_ID = 915291246396833832

if not TOKEN:
    raise ValueError("❌ Discord bot TOKEN is missing from environment variables.")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY is missing from environment variables.")
if not NEWS_API_KEY:
    raise ValueError("❌ NEWS_API_KEY is missing from environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# ─── Bot Setup ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=['!', '`'], intents=intents)
tree = bot.tree

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
                title="\ud83d\udce9 New Support Message",
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
async def hello(ctx):
    await ctx.send('👋 Hello! I am your friendly bot.')

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command()
async def echo(ctx, *, message: str):
    await ctx.send(message)

@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title="🤖 Bot Info",
        description="Details about this bot.",
        color=discord.Color.green()
    )
    embed.add_field(name="Author", value="_amazing_.", inline=False)
    embed.set_footer(text="Thank you for using the bot!")
    await ctx.send(embed=embed)

@bot.command(aliases=["attendance", "at"])
async def attendance_cmd(ctx, total_classes: int, attended_classes: int):
    if total_classes <= 0 or attended_classes < 0 or attended_classes > total_classes:
        return await ctx.send("❌ Please enter valid class numbers.")
    percent = (attended_classes / total_classes) * 100
    resp = f"📊 Current attendance: **{percent:.2f}%**\n"
    if percent >= 75:
        missable = math.floor((attended_classes - 0.75 * total_classes) / 0.75)
        resp += f"✅ You can miss **{missable}** more class{'es' if missable != 1 else ''}."
    else:
        needed = math.ceil((0.75 * total_classes - attended_classes) / 0.25)
        resp += f"⚠️ Attend the next **{needed}** class{'es' if needed != 1 else ''}."
    await ctx.send(resp)

@bot.command()
async def ask(ctx, *, question: str):
    try:
        async with ctx.typing():
            loop = asyncio.get_event_loop()
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = await loop.run_in_executor(None, model.generate_content, question)
            await ctx.send(response.text)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def resetchat(ctx):
    await ctx.send("🔄 Chat session has been reset!")

@bot.command()
async def remindme(ctx, time: str, *, reminder: str):
    seconds = convert_to_seconds(time)
    if seconds <= 0:
        return await ctx.send("❌ Invalid time format! Use `1h`, `5m`, `30s`.")
    await ctx.send(f"⏰ I'll remind you in {time}, {ctx.author.mention}!")
    await asyncio.sleep(seconds)
    await ctx.send(f"🔔 {ctx.author.mention}, reminder: **{reminder}**")

@bot.command()
async def schedule(ctx, time: str, *, event: str):
    seconds = convert_to_seconds(time)
    if seconds <= 0:
        return await ctx.send("❌ Invalid time format! Use `1h`, `5m`, `30s`.")
    await ctx.send(f"📅 Event scheduled in {time}.")
    await asyncio.sleep(seconds)
    await ctx.send(f"🎉 **Scheduled Event:** {event}")

@bot.command()
@commands.has_permissions(administrator=True)
async def send(ctx, channel: discord.TextChannel, *, message: str):
    try:
        await channel.send(message)
        await ctx.send(f"✅ Sent message to {channel.mention}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def dm(ctx, user: discord.User, *, message: str):
    try:
        await user.send(message)
        await ctx.send(f"✅ DM sent to {user.mention}.")
    except discord.Forbidden:
        await ctx.send("❌ Cannot send DM (blocked or DMs disabled).")

@bot.command(name="uptime")
async def uptime(ctx):
    now = datetime.datetime.utcnow()
    delta = now - start_time
    days, remainder = divmod(delta.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    await ctx.send(f"⏱️ Bot has been running for: **{uptime_str}**")

@bot.command()
async def helpme(ctx):
    embed = discord.Embed(
        title="📚 Bot Commands",
        description="Here's a list of what I can do!",
        color=discord.Color.blurple()
    )
    embed.add_field(name="🎯 Basic", value="`!hello`, `!ping`, `!echo <msg>`, `!info`", inline=False)
    embed.add_field(name="🧠 Gemini", value="`!ask <query>`, `!resetchat`", inline=False)
    embed.add_field(name="📅 Scheduling", value="`!remindme`, `!schedule`", inline=False)
    embed.add_field(name="📊 Attendance", value="`!attendance <total> <attended>`", inline=False)
    embed.add_field(name="📬 Messaging", value="`!send`, `!dm`", inline=False)
    embed.add_field(name="🕒 Uptime", value="`!uptime`", inline=False)
    embed.set_footer(text="Use `/` for slash commands too!")
    await ctx.send(embed=embed)

# ─── Slash Commands ──────────────────────────────────────────────────────────
@tree.command(name="send", description="Send a message to any channel")
async def slash_send(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    try:
        await channel.send(message)
        await interaction.response.send_message(f"✅ Message sent to {channel.mention}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

@tree.command(name="avatar", description="Get a user's avatar")
async def slash_avatar(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    embed = discord.Embed(title=f"{user.name}'s Avatar", color=discord.Color.blurple())
    embed.set_image(url=avatar_url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="meme", description="Get a random meme from FingMemes subreddit")
async def slash_meme(interaction: discord.Interaction):
    await interaction.response.defer()
    url = "https://meme-api.com/gimme/FingMemes"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await interaction.followup.send("❌ Failed to fetch meme.")
            data = await resp.json()
    embed = discord.Embed(title=data["title"], color=discord.Color.random())
    embed.set_image(url=data["url"])
    await interaction.followup.send(embed=embed)

@tree.command(name="news", description="Get latest news by country & topic")
@app_commands.describe(
    country="Country code: in, us, gb, etc.",
    topic="Category: business, entertainment, health, science, sports, technology"
)
async def slash_news(interaction: discord.Interaction, country: str = "in", topic: str = "general"):
    await interaction.response.defer()
    url = f"https://newsapi.org/v2/top-headlines?country={country}&category={topic}&apiKey={NEWS_API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await interaction.followup.send("❌ Failed to fetch news.")
            data = await resp.json()
    articles = data.get("articles") or []
    if not articles:
        return await interaction.followup.send(f"❌ No news for `{country}`, `{topic}`.")
    art = articles[0]
    embed = discord.Embed(
        title=art["title"],
        url=art["url"],
        description=art.get("description", "No description."),
        color=discord.Color.blue()
    )
    if art.get("urlToImage"):
        embed.set_image(url=art["urlToImage"])
    await interaction.followup.send(embed=embed)

# ─── Run the Bot ─────────────────────────────────────────────────────────────
# webserver.keep_alive()
bot.run(TOKEN)
