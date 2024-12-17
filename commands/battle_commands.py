from discord.ext import commands
import discord
import asyncio
import re
from db.user_db import (
    get_user_class,
    set_user_class,
    duel,
    update_user_gold,
    get_user_balance,
)
from db.battle_db import multi_duel
from data.classes import classes


class BattleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="class_effectiveness",
        description="View the effectiveness of all classes.",
    )
    async def class_effectiveness(self, ctx):
        response = ""
        for class_name, class_data in classes.items():
            response += f"## {class_name}\n"
            response += f"**Vulnerabilities:** {', '.join(class_data['vulnerabilities'])}\n"
            response += f"**Resistances:** {', '.join(class_data['resistances'])}\n"
            response += f"**Synergies:** {', '.join(class_data['synergies'])}\n\n"
        await ctx.reply(response)

    @commands.hybrid_command(name="class", description="View your class information")
    async def view_class(self, ctx):
        user_class = await get_user_class(str(ctx.author.id))
        if user_class is None:
            await ctx.reply("You have not selected a class yet. Use /select_class to choose a class.")
            return
        await ctx.reply(f"Your current class is {user_class}.")

    @commands.hybrid_command(name="select_class", description="Select your class.")
    async def select_class(self, ctx, *, user_class: str):
        if await get_user_class(str(ctx.author.id)) is not None:
            await ctx.reply("You have already selected a class.")
            return

        if user_class not in classes:
            await ctx.reply("Invalid class.")
            return

        await ctx.reply(f"You have selected the {user_class} class.")
        await set_user_class(str(ctx.author.id), user_class)

    @commands.hybrid_command(name="duel", description="Challenge another user to a duel.")
    async def duel_command(self, ctx, opponent: discord.Member, bet: int = 0):
        challenger_id = str(ctx.author.id)
        opponent_id = str(opponent.id)

        if bet < 0:
            await ctx.reply("Bet amount cannot be negative.")
            return

        if bet > 0:
            challenger_balance = await get_user_balance(challenger_id)
            opponent_balance = await get_user_balance(opponent_id)
            if challenger_balance < bet:
                await ctx.reply("You don't have enough gold to place that bet.")
                return
            if opponent_balance < bet:
                await ctx.reply("Opponent doesn't have enough gold to match that bet.")
                return

        def check(m):
            return m.author == opponent and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

        bet_msg = f" with a bet of {bet} gold each" if bet > 0 else ""
        await ctx.reply(f"{opponent.mention}, do you accept the duel challenge{bet_msg}? (yes/no)")

        try:
            confirmation = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.reply("Duel challenge timed out.")
            return

        if confirmation.content.lower() == "no":
            await ctx.reply("Duel challenge declined.")
            return

        if bet > 0:
            challenger_balance = await get_user_balance(challenger_id)
            opponent_balance = await get_user_balance(opponent_id)
            await update_user_gold(challenger_id, challenger_balance - bet)
            await update_user_gold(opponent_id, opponent_balance - bet)

        result, winner_id, loser_id = await duel(challenger_id, opponent_id)

        if bet > 0:
            if winner_id is None:
                challenger_balance = await get_user_balance(challenger_id)
                opponent_balance = await get_user_balance(opponent_id)
                await update_user_gold(challenger_id, challenger_balance + bet)
                await update_user_gold(opponent_id, opponent_balance + bet)
                result += "\nThe duel was inconclusive. Bets have been refunded."
            else:
                winner_balance = await get_user_balance(winner_id)
                await update_user_gold(winner_id, winner_balance + (bet * 2))
                result += f"\n<@{winner_id}> wins the bet and takes home {bet*2} gold!"

        await ctx.reply(result)

    @commands.hybrid_command(name="team_battle", description="Start a team battle. Format: /team_battle @user1 @user2 vs @user3 @user4")
    async def team_battle(self, ctx, *, input_line: str):
        # Parse input_line for something like "@user1 @user2 vs @user3 @user4"
        # This is a rough parsing approach. Adjust as needed.
        parts = input_line.split(" vs ")
        if len(parts) != 2:
            await ctx.reply("Invalid format. Use `/team_battle @user1 @user2 vs @user3 @user4`")
            return

        team1_part = parts[0].strip()
        team2_part = parts[1].strip()

        # Extract user mentions
        mention_pattern = r"<@!?(\d+)>"
        team1_ids = re.findall(mention_pattern, team1_part)
        team2_ids = re.findall(mention_pattern, team2_part)

        if not team1_ids or not team2_ids:
            await ctx.reply("No valid mentions found.")
            return

        if len(team1_ids) > 4 or len(team2_ids) > 4:
            await ctx.reply("Maximum team size is 4.")
            return

        all_ids = team1_ids + team2_ids
        for uid in all_ids:
            member = ctx.guild.get_member(int(uid))
            if member is None:
                await ctx.reply(f"<@{uid}> is not in the server.")
                return

        response, winning_team, losing_team = await multi_duel(team1_ids, team2_ids)
        await ctx.reply(response)


async def setup(bot):
    await bot.add_cog(BattleCommands(bot))
