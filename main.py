import discord
from env import token, alt_token
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="what the sigma ", intents=intents)


async def main():
    async with bot:
        await bot.load_extension("commands.dev_commands")
        await bot.load_extension("commands.stupid_commands")
        await bot.load_extension("commands.faction_commands")
        await bot.load_extension("commands.faction_management")
        await bot.load_extension("commands.battle_commands")
        await bot.load_extension("commands.user_commands")
        await bot.load_extension("commands.shop_commands")
        await bot.load_extension("commands.faction_shop_commands")
        await bot.load_extension("commands.co_op_commands")
        await bot.start(token)


asyncio.run(main())
