from discord.ext import commands

class Stop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='stop')
    async def stop_tracker(self, ctx):
        """Arrête le suivi des joueurs et des constructions"""
        if ctx.author.guild_permissions.administrator:
            try:
                await self.bot.player_tracker.stop()
                await self.bot.build_tracker.stop()
                await self.bot.kill_tracker.stop()
                await self.bot.player_sync.stop()
                await self.bot.vote_tracker.stop()
                await ctx.send("Suivi des joueurs, des constructions, du classement et des votes arrêté")
            except Exception as e:
                await ctx.send(f"Erreur lors de l'arrêt: {e}")
        else:
            await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

async def setup(bot):
    await bot.add_cog(Stop(bot)) 