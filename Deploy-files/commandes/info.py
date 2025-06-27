from discord.ext import commands
import discord

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="info")
    async def info_command(self, ctx):
        """Affiche les informations du joueur"""
        # Vérifier si la commande est utilisée en MP
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
            return
        await self.bot.player_sync.get_player_info(ctx)

async def setup(bot):
    await bot.add_cog(Info(bot)) 