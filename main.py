import discord
from env import token
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="what the sigma ", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is connected. version {discord.__version__}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(e)


@bot.hybrid_command()
async def ping(ctx):
    await ctx.send("pong")


@bot.hybrid_command()
async def riyyan(ctx):
    await ctx.send("homosexual")


bot.run(token)
