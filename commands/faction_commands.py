import asyncio
import discord
from discord.ext import commands
from db.faction_db import (
    get_faction_members,
    get_faction_upgrades,
    get_faction_resources,
    get_faction_leader,
    get_top_factions_by_score,
    faction_income,
)
from db.user_db import deposit_gold_to_faction, get_user_faction


class FactionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="faction_info", description="View information about your faction.")
    async def faction_info(self, ctx):
        user_id = str(ctx.author.id)
        faction_name = await get_user_faction(user_id)
        if not faction_name:
            await ctx.reply("You are not part of any faction.")
            return

        leader_id = await get_faction_leader(faction_name)
        members = await get_faction_members(faction_name)
        resources = await get_faction_resources(faction_name)
        upgrades = await get_faction_upgrades(faction_name)

        leader_mention = f"<@{leader_id}>" if leader_id else "None"

        member_list_str = ", ".join(f"<@{m}>" for m in members) if members else "No members"

        upgrade_parts = []
        if upgrades["power_bonus"] > 0:
            upgrade_parts.append(f"Power +{upgrades['power_bonus']}")
        if upgrades["hourly_bonus"] > 0:
            upgrade_parts.append(f"Hourly +{upgrades['hourly_bonus'] * 100:.1f}%")
        if upgrades["attack_bonus"] > 0:
            upgrade_parts.append(f"Attack +{upgrades['attack_bonus']}")
        if upgrades["defense_bonus"] > 0:
            upgrade_parts.append(f"Defense +{upgrades['defense_bonus']}")

        upgrades_str = ", ".join(upgrade_parts) if upgrade_parts else "None"

        embed = discord.Embed(title=f"Faction Info: {faction_name}", color=discord.Color.green())
        embed.add_field(name="Leader", value=leader_mention, inline=False)
        embed.add_field(name="Resources", value=str(resources), inline=True)
        embed.add_field(name="Upgrades", value=upgrades_str, inline=True)
        embed.add_field(name="Members", value=member_list_str, inline=False)

        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="leaderboard", description="Check the faction leaderboard.")
    async def leaderboard(self, ctx):
        factions = await get_top_factions_by_score()

        if not factions:
            await ctx.reply("No factions found.")
            return

        leaderboard = "```css\n"
        for index, faction in enumerate(factions):
            leaderboard += f"{index + 1}. {faction['name']} (Score: {faction['score']:.1f}, Resources: {faction['resources']})\n"
        leaderboard += "```"

        await ctx.reply(leaderboard)

    @commands.hybrid_command(name="deposit", description="Deposit gold into your faction.")
    async def deposit(self, ctx, amount: int):
        """
        Allows the user to deposit gold into their faction.
        """
        user_id = str(ctx.author.id)
        result = await deposit_gold_to_faction(user_id, amount)
        await ctx.reply(result)

    @commands.hybrid_command(name="faction_income", description="Trigger daily faction income increase.")
    async def faction_income_cmd(self, ctx):
        user_id = str(ctx.author.id)
        result = await faction_income(user_id)
        await ctx.reply(result)


async def setup(bot):
    await bot.add_cog(FactionCommands(bot))
