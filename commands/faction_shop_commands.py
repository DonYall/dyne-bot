import discord
from discord.ext import commands
from db.faction_shop_db import purchase_faction_upgrade


class FactionShopCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="faction_shop", description="View faction upgrades available.")
    async def faction_shop(self, ctx):
        embed = discord.Embed(title="Faction Shop", description="Upgrades that benefit all members.")
        embed.add_field(name="Power Training Grounds (+1 power)", value="1000 faction gold", inline=False)
        embed.add_field(name="Scholar's Library (+0.05 hourly multiplier)", value="2000 faction gold", inline=False)
        embed.add_field(name="Armory (+1 attack_bonus)", value="1500 faction gold", inline=False)
        embed.add_field(name="Fortifications (+1 defense_bonus)", value="1500 faction gold", inline=False)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name="purchase_faction_upgrade", description="Purchase a faction upgrade (leader only).")
    async def purchase_faction_upgrade_cmd(self, ctx, upgrade: str):
        user_id = str(ctx.author.id)
        result = await purchase_faction_upgrade(user_id, upgrade)
        await ctx.reply(result)


async def setup(bot):
    await bot.add_cog(FactionShopCommands(bot))
