import asyncio
import discord
from discord.ext import commands
from db.faction_db import (
    claim_hourly,
    coinflip,
    get_user_balance,
    get_top_factions,
    deposit_gold_to_faction,
)


class FactionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="claim", description="Claim your hourly gold reward.")
    async def claim(self, ctx):
        """
        Allows the user to claim their hourly reward.
        """
        user_id = str(ctx.author.id)
        result = await claim_hourly(user_id)
        await ctx.reply(result)

    @commands.hybrid_command(
        name="coinflip", description="Challenge another user to a coinflip bet."
    )
    async def coinflip(self, ctx, opponent: discord.Member, amount: int):
        """
        Executes a coinflip between the command user and the mentioned user.
        """
        challenger_id = str(ctx.author.id)
        opponent_id = str(opponent.id)

        if amount <= 0:
            await ctx.reply("The bet amount must be greater than 0.")
            return

        def check(m):
            return (
                m.author == opponent
                and m.channel == ctx.channel
                and m.content.lower() in ["yes", "no"]
            )

        await ctx.reply(
            f"{opponent.mention}, do you accept the coinflip bet of {amount} gold? (yes/no)"
        )

        try:
            confirmation = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.reply("Coinflip bet timed out.")
            return

        if confirmation.content.lower() == "no":
            await ctx.reply("Coinflip bet declined.")
            return

        result = await coinflip(challenger_id, opponent_id, amount)
        await ctx.reply(result)

    @commands.hybrid_command(
        name="balance", description="Check your current gold balance."
    )
    async def balance(self, ctx):
        """
        Allows the user to check their current gold balance.
        """
        user_id = str(ctx.author.id)
        balance = await get_user_balance(user_id)
        await ctx.reply(f"Your current balance is {balance} gold.")

    @commands.hybrid_command(
        name="leaderboard", description="Check the faction leaderboard."
    )
    async def leaderboard(self, ctx):
        """
        Displays the top 10 factions by gold balance.
        """
        factions = await get_top_factions()

        if not factions:
            await ctx.reply("No factions found.")
            return

        leaderboard = "```css\n"
        for index, faction in enumerate(factions):
            leaderboard += (
                f"{index + 1}. {faction['name']} ({faction['resources']} gold)\n"
            )
        leaderboard += "```"

        await ctx.reply(leaderboard)

    @commands.hybrid_command(
        name="deposit", description="Deposit gold into your faction."
    )
    async def deposit(self, ctx, amount: int):
        """
        Allows the user to deposit gold into their faction.
        """
        user_id = str(ctx.author.id)
        result = await deposit_gold_to_faction(user_id, amount)
        await ctx.reply(result)


async def setup(bot):
    await bot.add_cog(FactionCommands(bot))
