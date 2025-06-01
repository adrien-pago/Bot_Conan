import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from features.player_tracker import PlayerTracker
from utils.rcon_client import RCONClient

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Récupération des variables d'environnement avec valeurs par défaut
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("Le token Discord n'est pas défini dans le fichier .env")

DISCORD_CHANNEL_ID = int(os.getenv('TEST_CHANNEL_ID', '1375046216097988629'))
RCON_HOST = os.getenv('GAME_SERVER_HOST', '176.57.178.12')
RCON_PORT = int(os.getenv('RCON_PORT', '28316'))
RCON_PASSWORD = os.getenv('RCON_PASSWORD', '102633')

print(f"Configuration RCON:")
print(f"- Host: {RCON_HOST}")
print(f"- Port: {RCON_PORT}")
print(f"- Password: {'*' * len(RCON_PASSWORD) if RCON_PASSWORD else 'Non défini'}")

# Initialisation du client RCON
rcon_client = RCONClient(
    host=RCON_HOST,
    port=RCON_PORT,
    password=RCON_PASSWORD
)

# Initialisation du tracker de joueurs
player_tracker = PlayerTracker(
    bot=bot,
    channel_id=DISCORD_CHANNEL_ID,
    rcon_client=rcon_client
)

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord!')
    print(f'Canal de suivi : {DISCORD_CHANNEL_ID}')
    try:
        await player_tracker.start()
    except Exception as e:
        print(f"Erreur lors du démarrage du tracker: {e}")

@bot.command(name='stop')
async def stop_tracker(ctx):
    """Arrête le suivi des joueurs"""
    if ctx.author.guild_permissions.administrator:
        await player_tracker.stop()
        await ctx.send("Suivi des joueurs arrêté")
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

@bot.command(name='start')
async def start_tracker(ctx):
    """Démarre le suivi des joueurs"""
    if ctx.author.guild_permissions.administrator:
        try:
            await player_tracker.start()
            await ctx.send("Suivi des joueurs démarré")
        except Exception as e:
            await ctx.send(f"Erreur lors du démarrage: {e}")
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

@bot.command(name='rcon')
async def check_rcon(ctx):
    """Vérifie la connexion RCON"""
    if ctx.author.guild_permissions.administrator:
        try:
            response = await rcon_client.send_command("version")
            if response:
                await ctx.send(f"✅ Connexion RCON OK\nRéponse: {response}")
            else:
                await ctx.send("❌ Pas de réponse du serveur RCON")
        except Exception as e:
            await ctx.send(f"❌ Erreur RCON: {e}")
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

# Lancer le bot
bot.run(DISCORD_TOKEN) 