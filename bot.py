import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from features.player_tracker import PlayerTracker
from utils.rcon_client import RCONClient
from utils.ftp_handler import FTPHandler
from features.build_limit import BuildLimitTracker
from features.classement_player import KillTracker
from features.player_sync import PlayerSync
from features.vote_tracker import VoteTracker
from features.item_manager import ItemManager
import sqlite3
import logging
import datetime
from database.init_database import init_database

# Initialiser la base de données
init_database()

# Charger les variables d'environnement
load_dotenv()

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True  # Permet de recevoir les messages privés
intents.members = True      # Permet d'accéder aux informations des membres
bot = commands.Bot(command_prefix='!', intents=intents)

# Récupération des variables d'environnement avec valeurs par défaut
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("Le token Discord n'est pas défini dans le fichier .env")

RENAME_CHANNEL_ID = int(os.getenv('RENAME_CHANNEL_ID', '1375223092892401737'))
BUILD_CHANNEL_ID = int(os.getenv('BUILD_CHANNEL_ID', '1375234869071708260'))
KILLS_CHANNEL_ID = int(os.getenv('KILLS_CHANNEL_ID', '1375234869071708260'))
TOP_SERVER_CHANNEL_ID = int(os.getenv('TOP_SERVER_CHANNEL_ID', '1368550677030109225'))
SERVER_PRIVE_CHANNEL_ID = int(os.getenv('SERVER_PRIVE_CHANNEL_ID', '1369099859574915192'))
LOG_FILE_PATH = os.getenv('FTP_LOG_PATH', 'Saved/Logs/ConanSandbox.log')

print(f"Configuration RCON:")
print(f"- Host: {os.getenv('GAME_SERVER_HOST')}")
print(f"- Port: {os.getenv('RCON_PORT')}")
print(f"- Password: {'*' * len(os.getenv('RCON_PASSWORD', '')) if os.getenv('RCON_PASSWORD') else 'Non défini'}")

# Initialisation des clients et trackers
rcon_client = RCONClient()
ftp_handler = FTPHandler()

@bot.event
async def on_ready():
    print(f'{bot.user} est connecté à Discord!')
    try:
        # Initialisation des trackers
        bot.player_tracker = PlayerTracker(bot=bot, channel_id=RENAME_CHANNEL_ID, rcon_client=rcon_client)
        bot.build_tracker = BuildLimitTracker(bot=bot, channel_id=BUILD_CHANNEL_ID, ftp_handler=ftp_handler)
        bot.kill_tracker = KillTracker(bot=bot, channel_id=KILLS_CHANNEL_ID)
        bot.player_sync = PlayerSync(bot, LOG_FILE_PATH, ftp_handler=ftp_handler)
        bot.vote_tracker = VoteTracker(bot, TOP_SERVER_CHANNEL_ID, SERVER_PRIVE_CHANNEL_ID, ftp_handler=ftp_handler)
        bot.item_manager = ItemManager(bot, ftp_handler=ftp_handler)

        # Démarrage des trackers
        await bot.player_tracker.start()
        await bot.build_tracker.start()
        await bot.kill_tracker.start()
        await bot.player_sync.start()
        await bot.vote_tracker.start()
        
        print("Tous les trackers sont démarrés avec succès!")
        
    except Exception as e:
        print(f"Erreur lors du démarrage des trackers: {e}")

@bot.command(name='stop')
async def stop_tracker(ctx):
    """Arrête le suivi des joueurs et des constructions"""
    if ctx.author.guild_permissions.administrator:
        try:
            await bot.player_tracker.stop()
            await bot.build_tracker.stop()
            await bot.kill_tracker.stop()
            await bot.player_sync.stop()
            await bot.vote_tracker.stop()
            await ctx.send("Suivi des joueurs, des constructions, du classement et des votes arrêté")
        except Exception as e:
            await ctx.send(f"Erreur lors de l'arrêt: {e}")
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

@bot.command(name='start')
async def start_tracker(ctx):
    """Démarre le suivi des joueurs et des constructions"""
    if ctx.author.guild_permissions.administrator:
        try:
            await bot.player_tracker.start()
            await bot.build_tracker.start()
            await bot.kill_tracker.start()
            await bot.player_sync.start()
            await bot.vote_tracker.start()
            await ctx.send("Suivi des joueurs, des constructions, du classement et des votes démarré")
        except Exception as e:
            await ctx.send(f"Erreur lors du démarrage: {e}")
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

@bot.command(name='rcon')
async def check_rcon(ctx):
    """Vérifie la connexion RCON"""
    if ctx.author.guild_permissions.administrator:
        try:
            response = rcon_client.execute("version")
            if response:
                await ctx.send(f"✅ Connexion RCON OK\nRéponse: {response}")
            else:
                await ctx.send("❌ Pas de réponse du serveur RCON")
        except Exception as e:
            await ctx.send(f"❌ Erreur RCON: {e}")
    else:
        await ctx.send("Vous n'avez pas la permission d'utiliser cette commande")

# Commande Register pour Syncroniser compte disord et player in game
@bot.command(name="register")
async def register_command(ctx):
    """Démarre le processus d'enregistrement du compte"""
    try:
        # Vérifier si la commande est utilisée en MP
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
            return

        # Vérifier si l'utilisateur est déjà enregistré
        info = bot.player_sync.db.get_player_info(str(ctx.author.id))
        if info and info[1]:  # Si player_name existe
            await ctx.send("❌ Votre compte est déjà enregistré !")
            return

        # Générer et envoyer le code de vérification
        await bot.player_sync.start_verification(ctx)
    except Exception as e:
        await ctx.send("❌ Une erreur est survenue lors de l'enregistrement.")

@bot.command(name="info")
async def info_command(ctx):
    """Affiche les informations du joueur"""
    # Vérifier si la commande est utilisée en MP
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
        return
    await bot.player_sync.get_player_info(ctx)

@bot.command(name="solde")
async def solde_command(ctx):
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

@bot.command(name="starterpack")
async def starterpack_command(ctx):
    """Donne un pack de départ au joueur"""
    # Vérifier si la commande est utilisée en MP
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
        return

    try:
        # Récupérer les informations du joueur
        conn = sqlite3.connect('discord.db')
        c = conn.cursor()
        
        # Rechercher le joueur dans la base de données
        c.execute('SELECT player_name, player_id FROM users WHERE discord_id = ?', (str(ctx.author.id),))
        result = c.fetchone()
        
        if not result:
            await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande `!register` pour vous inscrire.")
            return

        player_name, player_id = result

        # Vérifier si le joueur est connecté
        online_players = bot.player_tracker.rcon_client.get_online_players()
        if player_name not in online_players:
            await ctx.send(f"❌ Vous devez être connecté au serveur pour recevoir votre pack de départ. Actuellement connectés: {', '.join(online_players)}")
            return

        # Message d'attente
        await ctx.send("⏳ Préparation de votre pack de départ, veuillez patienter...")

        # Donner le pack de départ
        if await bot.item_manager.give_starter_pack(player_id):
            await ctx.send(f"✅ Votre pack de départ a été ajouté à votre inventaire!\n"
                          f"Personnage : {player_name}\n"
                          f"Contenu : Épée, bouclier, armure, nourriture, eau, bandages, outils, et plus encore.")
            
            # Enregistrer la transaction dans l'historique
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                c.execute("INSERT INTO item_transactions (discord_id, player_name, item_id, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                         (str(ctx.author.id), player_name, 0, "StarterPack Distribué", timestamp))
                conn.commit()
            except sqlite3.OperationalError:
                # Si la table n'existe pas encore, on l'ignore pour le moment
                pass
        else:
            await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ. Vérifiez que vous êtes bien connecté au serveur.")

    except Exception as e:
        print(f"Erreur starterpack: {e}")
        await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ.")
    finally:
        conn.close()

@bot.command(name='build')
async def build_command(ctx):
    """Commande !build pour afficher le nombre de pièces de construction"""
    await bot.build_tracker._check_buildings()
    # Mettre à jour le timestamp du dernier build
    bot.item_manager.set_last_build_time()

# Lancer le bot
bot.run(DISCORD_TOKEN) 