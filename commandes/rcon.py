from discord.ext import commands

class Rcon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='rcon')
    async def check_rcon(self, ctx):
        """Vérifie la connexion RCON"""
        if ctx.author.guild_permissions.administrator:
            try:
                response = self.bot.rcon_client.execute("version")
                if response:
                    await ctx.send(f"✅ Connexion RCON OK\nRéponse: {response}")
                else:
                    await ctx.send("❌ Pas de réponse du serveur RCON")
            except Exception as e:
                await ctx.send(f"❌ Erreur RCON: {e}")
        else:
            await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

async def setup(bot):
    await bot.add_cog(Rcon(bot)) 