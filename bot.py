import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from ftp_handler import FTPHandler
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialisation du gestionnaire FTP
ftp_handler = FTPHandler()

# ID du salon spécifique
test_channel_id = 1375046216097988629

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    print(f'Connecté en tant que {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('------')
    
    # Essayer de se connecter au FTP
    try:
        if ftp_handler.test_connection():
            message = "✅ Connexion FTP réussie !"
        else:
            message = "❌ Connexion FTP échouée !"
    except Exception as e:
        message = f"❌ Connexion FTP échouée : {str(e)}"
    
    # Envoyer le message dans le salon spécifique
    channel = bot.get_channel(test_channel_id)
    if channel:
        await channel.send(message)
    else:
        print(f"Le salon avec l'ID {test_channel_id} n'a pas été trouvé")


# Lancer le bot avec le token
bot.run(os.getenv('DISCORD_TOKEN'))
