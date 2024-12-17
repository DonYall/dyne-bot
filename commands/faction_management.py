import asyncio
import discord
from discord.ext import commands
from db.faction_db import (
    create_faction,
    add_member_to_faction,
    remove_member_from_faction,
    is_faction_name_taken,
    get_faction_members,
    is_leader,
    remove_faction,
)
from db.user_db import get_user_faction


class FactionManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="create_faction", description="Create a new faction.")
    async def create_faction(self, ctx, faction_name: str):
        """
        Creates a new faction with the given name.
        """
        user_id = ctx.author.id

        current_faction = await get_user_faction(user_id)
        if current_faction:
            await ctx.send(f"You are already a member of `{current_faction}`. Leave your current faction first.")
            return

        if await is_faction_name_taken(faction_name):
            await ctx.send("That faction name is already taken. Please choose another name.")
            return

        await create_faction(faction_name, user_id)
        await add_member_to_faction(user_id, faction_name, role="leader")
        await ctx.send(f"Faction `{faction_name}` has been created! You are now the leader.")

    @commands.hybrid_command(name="invite", description="Invite a user to your faction.")
    async def invite(self, ctx, target: discord.Member):
        """
        Invites another user to your faction.
        """
        inviter_id = ctx.author.id
        inviter_faction = await get_user_faction(inviter_id)

        if not inviter_faction:
            await ctx.send("You are not part of a faction. Create one with `/create_faction`.")
            return

        target_faction = await get_user_faction(target.id)
        if target_faction:
            await ctx.send(f"{target.display_name} is already a member of `{target_faction}`.")
            return

        try:
            await target.send(
                f"🚨 **Faction Invite** 🚨\n"
                f"{ctx.author.display_name} has invited you to join their faction `{inviter_faction}`.\n"
                "Do you accept? Reply with 'yes' or 'no'."
            )
        except discord.Forbidden:
            await ctx.send(f"Could not DM {target.display_name}. They may have DMs disabled.")
            return

        await ctx.defer()

        def check(m):
            return m.author == target and m.content.lower() in ["yes", "no"]

        try:
            response = await self.bot.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send(f"{target.display_name} did not respond to the invite in time.")
            return

        if response.content.lower() == "yes":
            await add_member_to_faction(target.id, inviter_faction)
            await ctx.send(f"{target.display_name} has joined your faction `{inviter_faction}`!")
            await target.send(f"You are now a member of `{inviter_faction}`!")
        else:
            await ctx.send(f"{target.display_name} declined the faction invite.")

    @commands.hybrid_command(name="leave_faction", description="Leave your current faction.")
    async def leave_faction(self, ctx):
        """
        Allows a user to leave their faction.
        """
        user_id = ctx.author.id
        current_faction = await get_user_faction(user_id)

        if await is_leader(user_id):
            await ctx.send("You cannot leave the faction as the leader. Disband the faction instead.")
            return

        if not current_faction:
            await ctx.send("You are not part of any faction.")
            return

        await remove_member_from_faction(user_id)
        await ctx.send(f"You have left the faction `{current_faction}`.")

    @commands.hybrid_command(name="disband_faction", description="Disband your faction.")
    async def disband_faction(self, ctx):
        """
        Disbands the user's faction.
        """
        user_id = ctx.author.id
        current_faction = await get_user_faction(user_id)

        if not current_faction:
            await ctx.send("You are not part of any faction.")
            return

        if not await is_leader(user_id):
            await ctx.send("You are not the leader of your faction.")
            return

        await remove_faction(current_faction)
        await ctx.send(f"Your faction `{current_faction}` has been disbanded.")

    @commands.hybrid_command(name="faction_members", description="List members of your faction.")
    async def faction_members(self, ctx):
        """
        Lists all members of the user's faction.
        """
        user_id = ctx.author.id
        current_faction = await get_user_faction(user_id)

        if not current_faction:
            await ctx.send("You are not part of any faction.")
            return

        members = await get_faction_members(current_faction)
        member_list = "\n".join([f"<@{member_id}>" for member_id in members])
        await ctx.send(f"Members of `{current_faction}`:\n{member_list}")


async def setup(bot):
    await bot.add_cog(FactionManagement(bot))
