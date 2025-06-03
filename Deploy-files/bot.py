import os
import discord
import ssl
import logging
import sqlite3
import datetime
import traceback
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
from database.init_database import init_database

# Configuration SSL pour Python 3.13
ssl._create_default_https_context = ssl._create_unverified_context

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
        # Configurer le logger
        logger = logging.getLogger('bot')
        
        # Vérifier si le joueur est enregistré et récupérer ses informations
        player_info = bot.player_sync.db.get_player_info(str(ctx.author.id))
        if not player_info or not player_info[1]:  # Si player_name n'existe pas
            await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande `!register` pour vous inscrire.")
            return
            
        # Déballer les informations du joueur dans l'ordre correct
        # Format: discord_name, player_name, player_id, wallet, RP, date_end_rp, steam_id
        discord_name, player_name, player_id, wallet, rp, date_end_rp, steam_id = player_info
        
        # Log pour le débogage
        logger.info(f"Traitement starterpack pour {ctx.author.name} (Discord ID: {ctx.author.id})")
        logger.info(f"Informations joueur : Nom={player_name}, ID={player_id}, Steam ID={steam_id}")
        
        # Vérifier si le Steam ID est disponible
        if not steam_id:
            await ctx.send("❌ Votre compte n'a pas de Steam ID associé. Veuillez contacter un administrateur.")
            logger.error(f"Pas de Steam ID pour le joueur {player_name} (Discord ID: {ctx.author.id})")
            return
        
        # Vérifier si le joueur a déjà reçu son starterpack
        if bot.player_sync.db.has_received_starterpack(str(ctx.author.id)):
            await ctx.send("❌ Vous avez déjà reçu votre pack de départ. Cette commande ne peut être utilisée qu'une seule fois par joueur.")
            return

        # Vérifier si le joueur est connecté
        online_players = bot.player_tracker.rcon_client.get_online_players()
        
        # Log la liste des joueurs connectés pour le débogage
        logger.info(f"Joueurs en ligne: {online_players}")
        
        # Vérifier que la liste des joueurs est valide
        is_valid_player_list = True
        for player in online_players:
            if "Couldn't find the command" in player or "Try \"help\"" in player:
                is_valid_player_list = False
                logger.error(f"Erreur dans la liste des joueurs: {player}")
                break
        
        if not is_valid_player_list:
            # Récupérer directement avec ListPlayers pour contourner le problème
            try:
                resp = bot.player_tracker.rcon_client.execute("ListPlayers")
                logger.info(f"Réponse directe de ListPlayers: {resp}")
                
                # Extraction manuelle des noms de personnages
                online_players = []
                lines = resp.splitlines()
                
                # Ignorer la ligne d'en-tête
                if lines and ("Idx" in lines[0] or "Char name" in lines[0]):
                    lines = lines[1:]
                
                for line in lines:
                    if not line.strip():
                        continue
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 2:
                            char_name = parts[1].strip()
                            if char_name and char_name != "Char name":
                                online_players.append(char_name)
                                logger.info(f"Joueur extrait manuellement: {char_name}")
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction manuelle des joueurs: {e}")
        
        # Option de débogage: afficher la liste des joueurs en ligne
        await ctx.send(f"ℹ️ Joueurs connectés: {', '.join(online_players)}")
        
        # Vérifier si le joueur est en ligne en utilisant ListPlayers et le Steam ID
        resp = bot.player_tracker.rcon_client.execute("ListPlayers")
        logger.info(f"Vérification de la présence du joueur avec Steam ID {steam_id}")
        
        is_player_online = False
        if resp and steam_id:
            lines = resp.splitlines()
            for line in lines:
                if steam_id in line:
                    is_player_online = True
                    logger.info(f"Joueur avec Steam ID {steam_id} trouvé en ligne: {line}")
                    break
        
        if not is_player_online:
            await ctx.send(f"❌ Vous devez être connecté au serveur avec votre personnage '{player_name}' pour recevoir votre pack de départ.")
            return

        # Message d'attente
        await ctx.send("⏳ Préparation de votre pack de départ, veuillez patienter...")
        
        # Log l'exécution de give_starter_pack_by_steam_id
        logger.info(f"Tentative d'envoi du starter pack pour le joueur avec Steam ID {steam_id}")

        # Donner le pack de départ en utilisant le Steam ID
        if await bot.item_manager.give_starter_pack_by_steam_id(steam_id):
            # Marquer le starterpack comme reçu
            bot.player_sync.db.set_starterpack_received(str(ctx.author.id))
            
            await ctx.send(f"✅ Votre pack de départ a été ajouté à votre inventaire!\n"
                          f"Personnage : {player_name}\n"
                          f"Contenu : Piolet stellaire, couteau stellaire, grande hache stellaire, coffre en fer, cheval, selle légère et extrait d'aoles.")
            
            # Enregistrer la transaction dans l'historique
            conn = sqlite3.connect('discord.db')
            c = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                c.execute("INSERT INTO item_transactions (discord_id, player_name, item_id, count, price, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (str(ctx.author.id), player_name, 0, 1, 0, "StarterPack Distribué", timestamp))
                conn.commit()
            except sqlite3.OperationalError:
                # Si la table n'existe pas encore, on l'ignore pour le moment
                pass
            finally:
                conn.close()
        else:
            await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ. Vérifiez que vous êtes bien connecté au serveur.")

    except Exception as e:
        logger.error(f"Erreur dans starterpack_command: {e}")
        logger.error(traceback.format_exc())
        await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ. Veuillez contacter un administrateur.")

@bot.command(name='build')
async def build_command(ctx):
    """Commande !build pour afficher le nombre de pièces de construction"""
    try:
        await ctx.send("⏳ Vérification des constructions en cours...")
        await bot.build_tracker._check_buildings()
        # Mettre à jour le timestamp du dernier build
        bot.item_manager.set_last_build_time()
    except Exception as e:
        await ctx.send(f"❌ Une erreur est survenue lors de la vérification des constructions: {str(e)}")
        print(f"Erreur build_command: {e}")

@bot.command(name='kills_status')
async def kills_status_command(ctx):
    """Commande pour vérifier l'état du KillTracker et forcer son démarrage si nécessaire"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Cette commande est réservée aux administrateurs.")
        return
        
    try:
        # Vérifier si le KillTracker est initialisé
        if not hasattr(bot, 'kill_tracker') or bot.kill_tracker is None:
            await ctx.send("❌ KillTracker n'est pas initialisé.")
            return
            
        # Vérifier si la tâche est en cours d'exécution
        is_running = bot.kill_tracker.update_kills_task.is_running()
        if is_running:
            status_text = "✅ En cours d'exécution"
        else:
            status_text = "❌ Arrêté"
        await ctx.send(f"État actuel du KillTracker: {status_text}")
        
        # Afficher les informations sur le canal
        channel_id = bot.kill_tracker.channel_id
        channel = bot.get_channel(channel_id)
        if channel:
            await ctx.send(f"Canal configuré: {channel.name} (ID: {channel_id})")
        else:
            await ctx.send(f"❌ Canal introuvable (ID: {channel_id})")
        
        # Si la tâche n'est pas en cours, proposer de la démarrer
        if not is_running:
            await ctx.send("⏳ Tentative de démarrage du KillTracker...")
            try:
                # Arrêter d'abord au cas où
                try:
                    bot.kill_tracker.update_kills_task.stop()
                except Exception:
                    pass
                
                # Démarrer la tâche
                await bot.kill_tracker.start()
                
                # Vérifier si le démarrage a réussi
                if bot.kill_tracker.update_kills_task.is_running():
                    await ctx.send("✅ KillTracker démarré avec succès!")
                else:
                    await ctx.send("❌ Échec du démarrage du KillTracker.")
            except Exception as e:
                await ctx.send(f"❌ Erreur lors du démarrage du KillTracker: {str(e)}")
                
        # Forcer une mise à jour immédiate
        await ctx.send("⏳ Exécution manuelle de la mise à jour...")
        try:
            await bot.kill_tracker.display_kills(ctx)
            await ctx.send("✅ Mise à jour effectuée.")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la mise à jour manuelle: {str(e)}")
            
    except Exception as e:
        await ctx.send(f"❌ Erreur: {str(e)}")
        print(f"Erreur kills_status_command: {e}")

# Lancer le bot
bot.run(DISCORD_TOKEN) 