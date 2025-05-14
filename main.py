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
import requests
import random

# ─── Start Time ─────────────────────────────────────────────────────────────
start_time = datetime.datetime.utcnow()
uptime_message = None

# ─── Environment Variables ───────────────────────────────────────────────────
TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#replace with your main server channel ids
SUPPORT_CHANNEL_ID = 1367611989219741707
UPTIME_CHANNEL_ID = 915291246396833832
LOG_CHANNEL_ID = 1368296589583585361  

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
# async def echo(ctx, *, message: str):
#     await ctx.send(message)
async def echo(interaction: discord.Interaction, message: str):
    if "@everyone" in message or "@here" in message:
        await interaction.response.send_message("You can't use @everyone or @here in this command.", ephemeral=True)
        return
    await interaction.response.send_message(message)

# @tree.command(name="avatar", description="Get a user's avatar")
# @app_commands.describe(user="The user to get avatar of (optional)")
# async def avatar(interaction: discord.Interaction, user: discord.User = None):
#     user = user or interaction.user  # Defaults to command user
#     avatar_url = user.avatar.url if user.avatar else user.default_avatar.url

#     embed = discord.Embed(title=f"{user.name}'s Avatar", color=discord.Color.blurple())
#     embed.set_image(url=avatar_url)

#     await interaction.response.send_message(embed=embed)


@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title="🤖 Bot Info",
        description="Details about this bot.",
        color=discord.Color.green()
    )
    embed.add_field(name="Author", value="`_amazing_.`", inline=False)
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
async def poll(ctx, question: str, *options: str):
    if len(options) < 2:
        return await ctx.send("❗ You need at least two options to create a poll (e.g., `!poll Favorite color? Red Blue`).")
    if len(options) > 9:
        return await ctx.send("❗ You can only provide up to 9 options.")

    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    
    description = ""
    for i, option in enumerate(options):
        description += f"{emojis[i]} {option}\n"

    embed = discord.Embed(
        title=question,
        description=description,
        color=discord.Color.orange()
    )
    embed.set_footer(text="React below to vote!")

    message = await ctx.send(embed=embed)
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

import akinator
@bot.command()
async def aki(ctx):  # renamed from `akinator` to `aki`
    aki = akinator.Akinator()
    await ctx.send("🧠 Starting Akinator...")

    try:
        q = aki.start_game()
    except Exception as e:
        return await ctx.send(f"Failed to start game: {e}")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    while aki.progression <= 80:
        await ctx.send(f"❓ {q} (yes/y, no/n, idk, probably/p, probably not/pn)")
        try:
            msg = await bot.wait_for("message", check=check, timeout=60.0)
        except:
            await ctx.send("⏰ Timed out.")
            return

        a = msg.content.lower()
        if a not in ["yes", "y", "no", "n", "idk", "probably", "p", "probably not", "pn"]:
            await ctx.send("❗ Please answer with yes, no, idk, probably, or probably not.")
            continue

        try:
            q = aki.answer(a)
        except akinator.AkiNoQuestions:
            break

    aki.win()
    await ctx.send(f"🎉 I guess: **{aki.first_guess['name']}**!\n{aki.first_guess['description']}")
    await ctx.send(aki.first_guess['absolute_picture_path'])



@bot.command(name="helpme")
async def helpme(ctx):
    embed = discord.Embed(
        title="Here's a list of what I can do!",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🎯 Basic Commands",
        value=(
            "`!hello` ➔ I greet you!\n"
            "`!ping` ➔ Check bot latency.\n"
            "`!uptime` ➔ See how long I've been running.\n"
            "`!echo <message>` ➔ I repeat what you say.\n"
            "`!info` ➔ Get a bot info embed."
        ),
        inline=False
    )

    embed.add_field(
        name="📝 Polling",
        value=(
            "`!poll <question>` ➔ Create a poll with 👍👎.\n"
            "`/poll` ➔ Slash command for polls with buttons and multiple options!"
        ),
        inline=False
    )

    embed.add_field(
        name="⏰ Reminders & Scheduling",
        value=(
            "`!remind <time> <task>` ➔ Get reminded (e.g., 1h30m).\n"
            "`!schedule <time> <event>` ➔ Schedule an announcement."
        ),
        inline=False
    )

    embed.add_field(
        name="🎨 Fun Stuff",
        value=(
            "`!avatar <user>` ➔ View your or someone else's profile picture.\n"
            "`!meme` ➔ Get a random meme from r/memes!"
        ),
        inline=False
    )

    embed.add_field(
        name="📬 Messaging",
        value=(
            "`!send <#channel> <message>` ➔ Send a custom message (admin only).\n"
            "`/send` ➔ Slash command to send message to a channel."
        ),
        inline=False
    )

    embed.add_field(
        name="💡 Gemini AI",
        value=(
            "`!ask <query>` ➔ Query the Gemini API for information.\n"
        ),
        inline=False
    )

    embed.add_field(
        name="🧮 Utilities",
        value=(
            "`!at <total> <attended>` → How many classes you can miss and still maintain 75%."
        ),
        inline=False
    )

    embed.set_footer(text="Use these wisely! 🤖")
    await ctx.send(embed=embed)
@bot.command()
@commands.is_owner()
async def servers(ctx):
    guilds = bot.guilds
    response = "\n".join(f"{i+1}. {guild.name} (ID: {guild.id})" for i, guild in enumerate(guilds))
    if len(response) > 1900:  # To avoid hitting Discord's message limit
        response = response[:1900] + "\n...and more."
    await ctx.send(f"I'm currently in {len(guilds)} servers:\n{response}")


# ─── Slash Commands ──────────────────────────────────────────────────────────
# @tree.command(name="send", description="Send a message to any channel")
# async def slash_send(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
#     try:
#         await channel.send(message)
#         await interaction.response.send_message(f"✅ Message sent to {channel.mention}", ephemeral=True)
#     except Exception as e:
#         await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
@bot.tree.command(name="send", description="Send a message to a specific channel.")
@app_commands.describe(channel="The channel to send to", message="The message to send")
async def send(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need admin permissions to use this command.", ephemeral=True)
        return
    await channel.send(message)
    await interaction.response.send_message(f"Message sent to {channel.mention}", ephemeral=True)



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


@bot.command()
async def r(ctx, subreddit: str):
    """Fetches a random top post from the specified subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=50&t=day"
    headers = {"User-agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return await ctx.send("❌ Could not fetch subreddit. Make sure it exists and is public.")

    data = response.json().get("data", {}).get("children", [])
    if not data:
        return await ctx.send("😕 No posts found in this subreddit.")

    post = random.choice(data)["data"]

    embed = discord.Embed(
        title=post["title"],
        url=f"https://reddit.com{post['permalink']}",
        color=discord.Color.blurple()
    )
    if "url_overridden_by_dest" in post:
        embed.set_image(url=post["url_overridden_by_dest"])
    embed.set_footer(text=f"👍 {post['ups']} | 💬 {post['num_comments']} | r/{subreddit}")

    await ctx.send(embed=embed)

@bot.command()
async def food(ctx):
    """Sends a random food image from r/foodporn"""
    url = "https://www.reddit.com/r/foodporn/top.json?limit=50&t=day"
    headers = {"User-agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return await ctx.send("Failed to fetch food pics. Reddit might be down.")

    posts = response.json()["data"]["children"]
    post = random.choice(posts)["data"]

    if post["over_18"]:
        return await ctx.send("⚠️ NSFW content detected. Skipping.")

    embed = discord.Embed(
        title=post["title"],
        url=f"https://reddit.com{post['permalink']}",
        color=discord.Color.orange()
    )
    embed.set_image(url=post["url"])
    embed.set_footer(text=f"👍 {post['ups']} | 💬 {post['num_comments']} | r/foodporn")

    await ctx.send(embed=embed)




@bot.command()
async def rr(ctx, subreddit: str):
    """Fetches a random top image post from the specified subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=50&t=day"
    headers = {"User-agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return await ctx.send("❌ Could not fetch subreddit. Make sure it exists and is public.")

    data = response.json().get("data", {}).get("children", [])
    if not data:
        return await ctx.send("😕 No posts found in this subreddit.")

    # Filter out posts without an image URL
    image_posts = [post for post in data if
                   "url_overridden_by_dest" in post["data"] and post["data"]["url_overridden_by_dest"].endswith(
                       (".jpg", ".jpeg", ".png", ".gif"))]

    if not image_posts:
        return await ctx.send("😕 No image posts found in this subreddit.")

    post = random.choice(image_posts)["data"]

    embed = discord.Embed(
        title=post["title"],
        url=f"https://reddit.com{post['permalink']}",
        color=discord.Color.blurple()
    )
    embed.set_image(url=post["url_overridden_by_dest"])
    embed.set_footer(text=f"👍 {post['ups']} | 💬 {post['num_comments']} | r/{subreddit}")

    await ctx.send(embed=embed)


# ─── Run Bot ─────────────────────────────────────────────────────────────────
webserver.keep_alive()
bot.run(TOKEN)

