import discord
from discord.ext import commands
import random


class StupidCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.messages_until_false = 5
        self.stupid_words = [
            "skibidi toilet",
            "sigma",
            "riyyan",
            "noughty",
            "mohamed mazen hasan hasnain elsaban",
            "yemen gate",
            "homosexual",
            "~dessert",
            "sussy",
            "caught on penis",
            "jenna ortega is 21",
            "ava mckenny",
            "call the embassy",
            "found the aparattice",
            "yo this is peak",
            "hawk tuah",
            "prof hua",
            "WÆEH",
            "is maahir in the kitchen again",
            "im going back to 920",
        ]

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
        if message.author.bot:
            return

        if self.messages_until_false == 0:
            await message.reply("false")
            self.messages_until_false = random.randint(15, 20)
        else:
            self.messages_until_false -= 1

    @commands.hybrid_command(name="spam")
    async def spam_ping(self, ctx, user: discord.Member):
        for _ in range(10):
            await ctx.channel.send(
                user.mention + " " + random.choice(self.stupid_words)
            )


async def setup(bot):
    await bot.add_cog(StupidCommands(bot))
