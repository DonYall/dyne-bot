import discord
from discord.ext import commands
from db.user_db import (
    ensure_user_exists,
    get_user_balance,
    update_user_gold,
    get_user_power,
    update_user_power,
    get_user_max_health,
    update_user_max_health,
)
from db.client import supabase


class ShopCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="shop", description="View items available for purchase.")
    async def shop(self, ctx):
        embed = discord.Embed(title="Shop", description="Purchase upgrades for your character!")
        embed.add_field(
            name="Power Upgrade",
            value="Increases your power by 1 per 100 gold.",
            inline=False,
        )
        embed.add_field(
            name="Max Health Upgrade",
            value="Increases your max health by 10 per 200 gold.",
            inline=False,
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="buy", description="Buy an upgrade from the shop.")
    async def buy(self, ctx, item: str, amount: int):
        user_id = str(ctx.author.id)
        await ensure_user_exists(user_id)

        if amount <= 0:
            await ctx.reply("Please specify a positive amount.")
            return

        current_gold = await get_user_balance(user_id)

        if item.lower() == "power":
            cost = 100 * amount
            if current_gold < cost:
                await ctx.reply("You don't have enough gold for that purchase.")
                return
            user_power = await get_user_power(user_id)
            await update_user_power(user_id, user_power + amount)
            await update_user_gold(user_id, current_gold - cost)
            await ctx.reply(f"You have increased your power by {amount}!")
        elif item.lower() == "health":
            cost = 200 * amount
            if current_gold < cost:
                await ctx.reply("You don't have enough gold for that purchase.")
                return
            user_max_health = await get_user_max_health(user_id)
            await update_user_max_health(user_id, user_max_health + (amount * 10))
            await update_user_gold(user_id, current_gold - cost)
            await ctx.reply(f"You have increased your max health by {amount * 10}!")
        else:
            await ctx.reply("Invalid item. Available items: power, health.")

    @commands.hybrid_command(name="buy_hourly_upgrade", description="Increase your hourly claim multiplier.")
    async def buy_hourly_upgrade(self, ctx, amount: int = 1):
        user_id = str(ctx.author.id)
        if amount <= 0:
            await ctx.reply("Invalid amount.")
            return
        cost_per = 500
        total_cost = cost_per * amount
        current_gold = await get_user_balance(user_id)
        if current_gold < total_cost:
            await ctx.reply("You don't have enough gold.")
            return
        resp = supabase.table("users").select("hourly_multiplier").eq("id", user_id).execute()
        current_multi = resp.data[0]["hourly_multiplier"]
        new_multi = current_multi + (0.1 * amount)
        await update_user_gold(user_id, current_gold - total_cost)
        supabase.table("users").update({"hourly_multiplier": new_multi}).eq("id", user_id).execute()
        await ctx.reply(f"Your hourly gold claim multiplier is now {new_multi:.2f}!")


async def setup(bot):
    await bot.add_cog(ShopCommands(bot))
