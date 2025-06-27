from discord.ext import commands
import discord
import sqlite3

class Solde(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="solde")
    async def solde_command(self, ctx):
        """Affiche le solde du portefeuille du joueur"""
        # Vérifier si la commande est utilisée en MP
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
            return

        try:
            # Récupérer les informations du joueur
            conn = sqlite3.connect('discord.db')
            c = conn.cursor()
            
            # Rechercher le joueur dans la base de données
            c.execute('SELECT player_name, wallet FROM users WHERE discord_id = ?', (str(ctx.author.id),))
            result = c.fetchone()
            
            if result:
                player_name, wallet = result
                await ctx.send(f"💰 **Votre solde actuel**\n"
                             f"Personnage : {player_name}\n"
                             f"Portefeuille : {wallet} points")
            else:
                await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande `!register` pour vous inscrire.")
                
        except Exception as e:
            await ctx.send("❌ Une erreur est survenue lors de la récupération de votre solde.")
        finally:
            conn.close()

async def setup(bot):
    await bot.add_cog(Solde(bot)) 