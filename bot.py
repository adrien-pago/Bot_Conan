import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from ftp_handler import FTPHandler
from database import DatabaseManager
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialisation des gestionnaires
ftp_handler = FTPHandler()
database = DatabaseManager()

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    print(f'Connecté en tant que {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('------')
    # Créer la table si elle n'existe pas
    database.create_table()

@bot.command(name='afficher_info')
async def afficher_info(ctx):
    """Commande pour afficher les informations depuis le FTP"""
    try:
        # Récupérer les données du FTP
        data = ftp_handler.get_data()
        
        # Enregistrer dans la base de données
        database.insert_data(data)
        
        # Préparer le message
        message = "Voici les informations récupérées :\n\n"
        message += f"Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"Nombre d'entrées : {len(data)}\n"
        
        # Envoyer le message
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"Une erreur est survenue : {str(e)}")

@bot.command(name='stats')
async def stats(ctx):
    """Commande pour afficher les statistiques"""
    try:
        stats = database.get_stats()
        message = "Statistiques :\n\n"
        message += f"Total d'entrées : {stats['total']}\n"
        message += f"Dernière mise à jour : {stats['last_update']}\n"
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"Une erreur est survenue : {str(e)}")

# Lancer le bot avec le token
bot.run(os.getenv('DISCORD_TOKEN'))
