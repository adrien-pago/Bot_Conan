from discord.ext import commands

class Start(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='start')
    async def start_tracker(self, ctx):
        """Démarre le suivi des joueurs et des constructions"""
        if ctx.author.guild_permissions.administrator:
            try:
                await self.bot.player_tracker.start()
                await self.bot.build_tracker.start()
                await self.bot.kill_tracker.start()
                await self.bot.player_sync.start()
                await self.bot.vote_tracker.start()
                await ctx.send("Suivi des joueurs, des constructions, du classement et des votes démarré")
            except Exception as e:
                await ctx.send(f"Erreur lors du démarrage: {e}")
        else:
            await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

async def setup(bot):
    await bot.add_cog(Start(bot)) 