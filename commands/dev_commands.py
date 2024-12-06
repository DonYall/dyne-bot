from discord.ext import commands


class DevCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="reload", description="Reload a cog.")
    async def reload(self, ctx, cog: str):
        """
        Reloads a cog.
        """
        try:
            await self.bot.reload_extension(f"commands.{cog}")
            await ctx.send(f"Reloaded {cog}.")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"{cog} is not loaded.")
        except commands.ExtensionNotFound:
            await ctx.send(f"{cog} is not found.")
        except commands.ExtensionFailed:
            await ctx.send(f"{cog} failed to reload.")


async def setup(bot):
    await bot.add_cog(DevCommands(bot))
