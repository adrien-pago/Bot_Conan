from discord.ext import commands
import discord

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="register")
    async def register_command(self, ctx):
        """Démarre le processus d'enregistrement du compte"""
        try:
            # Vérifier si la commande est utilisée en MP
            if not isinstance(ctx.channel, discord.DMChannel):
                await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
                return

            # Vérifier si l'utilisateur est déjà enregistré
            info = self.bot.player_sync.db.get_player_info(str(ctx.author.id))
            if info and info[1]:  # Si player_name existe
                await ctx.send("❌ Votre compte est déjà enregistré !")
                return

            # Générer et envoyer le code de vérification
            await self.bot.player_sync.start_verification(ctx)
        except Exception as e:
            await ctx.send("❌ Une erreur est survenue lors de l'enregistrement.")

async def setup(bot):
    await bot.add_cog(Register(bot)) 