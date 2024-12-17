import discord
from discord.ext import commands
from db.raid_db import (
    create_raid,
    add_raid_participant,
    ready_participant,
    start_raid_battle,
    invite_to_raid,
    is_raid_leader,
    get_raid_info,
    cancel_raid,
)
from data.bosses import bosses
from db.user_db import get_user_faction


class CoOpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="start_raid", description="Start a raid against a boss.")
    async def start_raid(self, ctx, boss_name: str):
        user_id = str(ctx.author.id)
        faction = await get_user_faction(user_id)
        if faction is None:
            await ctx.reply("You must be in a faction to start a co-op battle.")
            return
        if boss_name not in bosses:
            await ctx.reply("Invalid boss name. Available: " + ", ".join(bosses.keys()))
            return

        result = await create_raid(user_id, faction, boss_name)
        await ctx.reply(result)

    @commands.hybrid_command(name="invite_raid", description="Invite a faction member to your raid.")
    async def invite_raid(self, ctx, member: discord.Member):
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        result = await invite_to_raid(user_id, target_id)
        await ctx.reply(result)

    @commands.hybrid_command(name="join_raid", description="Join the raid you were invited to.")
    async def join_raid(self, ctx):
        user_id = str(ctx.author.id)
        result = await add_raid_participant(user_id)
        await ctx.reply(result)

    @commands.hybrid_command(name="ready_raid", description="Mark yourself as ready for the raid.")
    async def ready_raid_command(self, ctx):
        user_id = str(ctx.author.id)
        result = await ready_participant(user_id)
        await ctx.reply(result)

    @commands.hybrid_command(name="begin_raid", description="Leader starts the raid when all are ready.")
    async def begin_raid(self, ctx):
        user_id = str(ctx.author.id)
        if not await is_raid_leader(user_id):
            await ctx.reply("You must be the raid leader to start the battle.")
            return
        response = await start_raid_battle(user_id)
        await ctx.reply(response)

    @commands.hybrid_command(name="raid_info", description="Get info about your current raid.")
    async def raid_info_command(self, ctx):
        user_id = str(ctx.author.id)
        info = await get_raid_info(user_id)
        await ctx.reply(info)

    @commands.hybrid_command(name="cancel_raid", description="Cancel your raid (leader only).")
    async def cancel_raid_command(self, ctx):
        user_id = str(ctx.author.id)
        result = await cancel_raid(user_id)
        await ctx.reply(result)


async def setup(bot):
    await bot.add_cog(CoOpCommands(bot))
