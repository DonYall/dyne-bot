import discord
from discord.ext import commands
import random


class StupidCommands(commands.Cog):
    messages_until_false = 5

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx):
        await ctx.send("pong")

    @commands.hybrid_command(name="riyyan")
    async def riyyan(self, ctx):
        await ctx.send("homosexual")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is connected.")
        try:
            activity = discord.Streaming(
                name="Minecraft", url="https://youtube.com/watch?v=QMXBGUeX_c4"
            )
            await self.bot.change_presence(activity=activity)
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message(self, message):
        global messages_until_false
        if message.author.bot:
            return

        if messages_until_false == 0:
            await message.reply("false")
            messages_until_false = random.randint(15, 40)
        else:
            messages_until_false -= 1


async def setup(bot):
    await bot.add_cog(StupidCommands(bot))
