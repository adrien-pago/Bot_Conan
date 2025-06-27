from discord.ext import commands

class Build(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='build')
    async def build_command(self, ctx):
        """Commande !build pour afficher le nombre de pièces de construction"""
        try:
            await ctx.send("⏳ Vérification des constructions en cours...")
            await self.bot.build_tracker._check_buildings()
            self.bot.item_manager.set_last_build_time()
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue lors de la vérification des constructions: {str(e)}")
            print(f"Erreur build_command: {e}")

async def setup(bot):
    await bot.add_cog(Build(bot)) 