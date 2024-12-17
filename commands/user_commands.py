import discord
import asyncio
from discord.ext import commands
from db.user_db import (
    claim_hourly,
    coinflip,
    get_user_balance,
    heal_user,
    ensure_user_exists,
    get_user_class,
    get_user_faction,
    get_user_health,
    get_user_max_health,
    get_user_power,
    get_user_raid_wins,
    get_user_hourly_multiplier,
    get_user_final_attack,
    get_user_final_defense,
    get_faction_upgrades,
)
from data.classes import classes


class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="claim", description="Claim your hourly gold reward.")
    async def claim(self, ctx):
        user_id = str(ctx.author.id)
        result = await claim_hourly(user_id)
        await ctx.reply(result)

    @commands.hybrid_command(name="heal", description="Heal yourself once every 30 minutes.")
    async def heal(self, ctx):
        user_id = str(ctx.author.id)
        await ctx.reply(await heal_user(user_id))

    @commands.hybrid_command(name="coinflip", description="Challenge another user to a coinflip bet.")
    async def coinflip_command(self, ctx, opponent: discord.Member, amount: int):
        if amount <= 0:
            await ctx.reply("The bet amount must be greater than 0.")
            return

        challenger_id = str(ctx.author.id)
        opponent_id = str(opponent.id)

        def check(m):
            return m.author == opponent and m.channel == ctx.channel and m.content.lower() in ["yes", "no"]

        await ctx.reply(f"{opponent.mention}, do you accept the coinflip bet of {amount} gold? (yes/no)")

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

    @commands.hybrid_command(name="balance", description="Check your current gold balance.")
    async def balance(self, ctx):
        user_id = str(ctx.author.id)
        balance = await get_user_balance(user_id)
        await ctx.reply(f"Your current balance is {balance} gold.")

    @commands.hybrid_command(name="stats", description="View your stats.")
    async def stats(self, ctx):
        user_id = str(ctx.author.id)
        await ensure_user_exists(user_id)

        user_class = await get_user_class(user_id) or "None"
        user_faction = await get_user_faction(user_id) or "None"
        user_gold = await get_user_balance(user_id)
        user_health = await get_user_health(user_id)
        user_max_health = await get_user_max_health(user_id)
        user_power = await get_user_power(user_id)
        user_raid_wins = await get_user_raid_wins(user_id)
        user_hourly_multi = await get_user_hourly_multiplier(user_id)
        user_final_attack = await get_user_final_attack(user_id)
        user_final_defense = await get_user_final_defense(user_id)

        synergy_info = "None"
        if user_class != "None":
            cls_data = classes.get(user_class, {})
            synergies = cls_data.get("synergies", [])
            if synergies:
                synergy_info = ", ".join(synergies)

        faction_upgrades_str = "None"
        if user_faction != "None":
            ups = await get_faction_upgrades(user_faction)
            upgrade_list = []
            if ups["power_bonus"] > 0:
                upgrade_list.append(f"Power +{ups['power_bonus']}")
            if ups["hourly_bonus"] > 0:
                upgrade_list.append(f"Hourly +{ups['hourly_bonus']*100:.1f}%")
            if ups["attack_bonus"] > 0:
                upgrade_list.append(f"Attack +{ups['attack_bonus']}")
            if ups["defense_bonus"] > 0:
                upgrade_list.append(f"Defense +{ups['defense_bonus']}")
            if upgrade_list:
                faction_upgrades_str = ", ".join(upgrade_list)

        embed = discord.Embed(title=f"{ctx.author.display_name}'s Stats", color=discord.Color.blue())
        embed.add_field(name="Class", value=user_class, inline=True)
        embed.add_field(name="Faction", value=user_faction, inline=True)
        embed.add_field(name="Gold", value=str(user_gold), inline=True)

        embed.add_field(name="Health", value=f"{user_health}/{user_max_health}", inline=True)
        embed.add_field(name="Power", value=str(user_power), inline=True)
        embed.add_field(name="Raid Wins", value=str(user_raid_wins), inline=True)

        embed.add_field(name="Hourly Multiplier", value=f"{user_hourly_multi:.2f}x", inline=True)
        embed.add_field(name="Attack", value=str(user_final_attack), inline=True)
        embed.add_field(name="Defense", value=str(user_final_defense), inline=True)

        embed.add_field(name="Class Synergies", value=synergy_info, inline=False)
        embed.add_field(name="Faction Upgrades", value=faction_upgrades_str, inline=False)

        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(UserCommands(bot))
