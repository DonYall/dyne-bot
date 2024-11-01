import discord
from env import token
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="what the sigma ", intents=intents)


async def main():
    async with bot:
        await bot.load_extension("commands.stupid_commands")
        await bot.start(token)


asyncio.run(main())
