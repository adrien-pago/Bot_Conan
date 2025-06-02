# bot.py

import os
import sqlite3
import tempfile
import uuid
from dotenv import load_dotenv
import discord
import asyncio
load_dotenv()
from discord.ext import commands
from ftp_handler import FTPHandler
from rcon import RconClient
from database import DatabaseManager
import time
import datetime
from discord.ext import tasks
import asyncio
import logging
import traceback

# Configuration du logging détaillé
logging.basicConfig(
    level=logging.DEBUG,  # Niveau de débogage plus bas
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Créer des loggers spécifiques pour différentes parties du bot
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)

# Logger spécifique pour RCON
rcon_logger = logging.getLogger('rcon')

# Logger spécifique pour le KillTracker
killtracker_logger = logging.getLogger('killtracker')

# Configuration du logger Discord
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)

# Masquer les avertissements PyNaCl qui ne sont pas pertinents pour nous
discord_logger.propagate = False
for handler in discord_logger.handlers:
    handler.setLevel(logging.INFO)

# Logger spécifique pour le bot
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)

# Logger spécifique pour RCON
rcon_logger = logging.getLogger('rcon')

# Logger spécifique pour le KillTracker
killtracker_logger = logging.getLogger('killtracker')

# --------------------------
# 1) Charger les variables
# --------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN or DISCORD_TOKEN.count('.') != 2:
    raise RuntimeError("Le token Discord est manquant ou invalide dans votre .env")

TEST_CHANNEL_ID = int(os.getenv('TEST_CHANNEL_ID', '1375046216097988629'))

# --------------------------
# 2) Initialiser le Bot
# --------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --------------------------
# 3) Helpers
# --------------------------
def _load_db_from_bytes(db_bytes: bytes):
    """
    Écrit db_bytes dans un fichier temporaire sur disque, et renvoie son chemin.
    Il faut fermer le fichier avant de l'ouvrir avec sqlite3 sur Windows.
    """
    logger.debug("Début du chargement de la base de données depuis bytes")
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(db_bytes)
            logger.debug(f"Base de données temporaire créée: {temp_file.name}")
            return temp_file.name
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la base de données: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise

ftp_handler = FTPHandler()
last_channel_update = 0  # Timestamp de la dernière mise à jour du salon
UPDATE_COOLDOWN = 300  # 5 minutes en secondes

# --------------------------
# 4) on_ready
# --------------------------
@bot.event
async def on_ready():
    try:
        logger.info("Début de l'initialisation du bot")
        logger.info(f"Bot connecté en tant que {bot.user.name}")
        logger.info(f"ID du bot: {bot.user.id}")
        logger.info(f"Nombre de guildes: {len(bot.guilds)}")
        
        # Vérifier les permissions
        guild = bot.guilds[0]
        me = guild.me
        logger.info(f"Permissions du bot: {me.guild_permissions.value}")
        
        # Initialiser le KillTracker
        logger.info("Initialisation du KillTracker...")
        #await kill_tracker.start_event_monitor(bot)
        
        # Démarrer les tâches planifiées
        logger.info("Démarrage des tâches planifiées...")
        update_channel_name_task.start()
        build_task.start()
        #update_kills_task.start()
        logger.info("Tâches planifiées démarrées")
        
        logger.info("Bot prêt et toutes les tâches démarrées")
        
        # Faire une première mise à jour immédiate
        logger.info("Première mise à jour immédiate...")
        await update_channel_name()
        logger.info("Première mise à jour terminée")
        
    except Exception as e:
        logger.error(f"Erreur critique lors de l'initialisation du bot: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise

# --------------------------
# 5) update_channel_name Fonction
# --------------------------
async def update_channel_name():
    """Met à jour le nom du salon avec le nombre de joueurs"""
    try:
        logger.info("Début de la mise à jour du nom du salon...")
        online = []
        try:
            # Récupérer la liste des joueurs en ligne via RCON
            rcon = RconClient()
            online = rcon.get_online_players()
            rcon.close()
            logger.info(f"Nombre de joueurs en ligne : {len(online)}")
        except Exception as e:
            logger.error(f"Erreur RCON : {str(e)}")
            online = []

        # Calculer le nombre
        total_slots = 40
        count = len(online)
        
        # Vérifier si c'est le raid time
        now = datetime.datetime.now()
        is_raid_time = (
            now.weekday() in [2, 5, 6] and  # Mercredi (2), Samedi (5), Dimanche (6)
            19 <= now.hour < 22  # Entre 19h et 22h
        )
        logger.info(f"Raid time : {is_raid_time}")
        
        # Renommer le salon
        channel = bot.get_channel(1375223092892401737)
        if channel:
            if is_raid_time:
                await channel.edit(name=f"🟢【{count}︱40】Raid On")
            else:
                await channel.edit(name=f"🟢【{count}︱40】Raid Off")
            logger.info("Nom du salon mis à jour avec succès")
        else:
            logger.error("Salon non trouvé")
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit
            retry_after = e.retry_after
            logger.warning(f"Rate limit atteint. Nouvelle tentative dans {retry_after} secondes")
            await asyncio.sleep(retry_after)
            await update_channel_name()
        else:
            logger.error(f"Erreur Discord : {str(e)}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {str(e)}")
        logger.error(traceback.format_exc())
        # En cas d'erreur, mettre à jour avec le statut d'erreur
        channel = bot.get_channel(1375223092892401737)
        if channel:
            await channel.edit(name="🔴【0︱40】")
            logger.error("Salon mis à jour avec le statut d'erreur")

# --------------------------
# 6) update_channel_name_task Boucle
# --------------------------
@tasks.loop(minutes=8)
async def update_channel_name_task():
    """Tâche planifiée pour mettre à jour le nom du salon toutes les 5 minutes"""
    try:
        logger.info("Exécution de la tâche de mise à jour du salon...")
        await update_channel_name()
        logger.info("Mise à jour du salon réussie")
    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limit
            retry_after = e.retry_after
            logger.warning(f"Rate limit atteint. Nouvelle tentative dans {retry_after} secondes")
            await asyncio.sleep(retry_after)
            # Réessayer une fois après le délai
            try:
                await update_channel_name()
                logger.info("Mise à jour réussie après le rate limit")
            except Exception as e2:
                logger.error(f"Erreur après le rate limit : {str(e2)}")
        else:
            logger.error(f"Erreur Discord : {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du salon : {str(e)}")
        logger.error(traceback.format_exc())


# --------------------------
# 7) Commande !build
# --------------------------
@bot.command(name='build')
async def build_command(ctx):
    """Commande !build pour afficher le nombre de pièces de construction"""
    await build()

async def build(ctx=None):
    """
    Affiche le nombre de pièces de construction par joueur
    Peut être appelé manuellement avec !build ou automatiquement via la tâche planifiée
    """
    try:
        # Récupérer les données depuis le FTP
        database = DatabaseManager()
        constructions = database.get_constructions_by_player(ftp_handler)
        
        if not constructions:
            message = "Aucune construction trouvée."
            channel = bot.get_channel(1375234869071708260)
            await channel.send(message)
            return

        # Constante pour la limite de construction
        LIMITE_CONSTRUCTION = 12000

        # Regrouper les constructions par clan
        clans = {}
        for player in constructions:
            clan = player['clan'] if player['clan'] else "Sans clan"
            if clan not in clans:
                clans[clan] = {'total': 0, 'players': 0}
            clans[clan]['total'] += player['instances']
            clans[clan]['players'] += 1
        
        # Calculer la moyenne par joueur pour chaque clan
        clans_list = []
        for clan_name, data in clans.items():
            if data['players'] > 0:  # Éviter la division par zéro
                average = data['total'] / data['players']
                clans_list.append({
                    'name': clan_name,
                    'total': data['total'],
                    'players': data['players'],
                    'average': round(average)  # Arrondir à l'entier
                })
        
        # Trier les clans par moyenne d'instances
        clans_list.sort(key=lambda x: x['average'], reverse=True)
        
        # Construire le message
        message = ""
        
        # Ajouter le titre et la ligne de séparation
        message += f"Nombre de pièces de construction par clan (Limite: {LIMITE_CONSTRUCTION} pièces) :\n"
        message += "----------------------------------------\n\n"
        
        # Ajouter uniquement les clans qui dépassent la limite
        has_exceeded_limit = False
        for clan in clans_list:
            if clan['average'] > 0 and clan['average'] > LIMITE_CONSTRUCTION:
                has_exceeded_limit = True
                excess = clan['average'] - LIMITE_CONSTRUCTION
                message += f"❌ **Clan ({clan['name']})** : {clan['average']} pièces (+{excess} au-dessus de la limite)\n\n"

        # Si aucun clan ne dépasse la limite, ajouter le message de félicitations
        if not has_exceeded_limit:
            message += f"✅ **Bravo ! Tous les clans respectent la limite de construction ({LIMITE_CONSTRUCTION} pièces maximum) !**"

        # Envoyer le message uniquement dans le salon de rapport
        report_channel = bot.get_channel(1375234869071708260)
        if report_channel:
            try:
                # Supprimer tous les messages existants
                await report_channel.purge(limit=10)
                
                # Attendre un court instant pour s'assurer que les messages sont supprimés
                await asyncio.sleep(1)
                
                # Envoyer le nouveau message
                await report_channel.send(message)
            except Exception as e:
                print(f"Erreur lors de l'envoi des messages : {e}")

    except Exception as e:
        error_message = f"❌ Erreur : {e}"
        channel = bot.get_channel(1375234869071708260)
        if channel:
            await channel.send(error_message)
        print(f"Erreur dans la commande !build: {e}")

# Ajouter une variable pour suivre la dernière exécution
last_build_time = 0
BUILD_COOLDOWN = 60  # 60 secondes de cooldown

# --------------------------
# 8) build_task Boucle
# --------------------------
@tasks.loop(hours=1)
async def build_task():
    """Tâche planifiée pour exécuter la commande build toutes les heures"""
    global last_build_time
    current_time = time.time()
    
    # Vérifier si assez de temps s'est écoulé depuis la dernière exécution
    if current_time - last_build_time >= BUILD_COOLDOWN:
        try:
            await build()
            last_build_time = current_time
            # Ajouter un délai pour éviter le rate limit
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Erreur dans la tâche build : {e}")

# --------------------------
# 9) Commande !clans
# --------------------------
@bot.command(name='clans')
async def clans(ctx):
    """
    !clans → affiche la liste des clans avec leurs membres et les joueurs sans clan
    """
    try:
        # Récupérer les données depuis le FTP
        database = DatabaseManager()
        clans_data = database.get_clans_and_players(ftp_handler)
        
        if not clans_data:
            return await ctx.send("Aucune donnée de clan trouvée.")

        # Construire le message
        messages = []
        current_message = "**Liste des clans et joueurs :**\n\n"
        
        # Afficher d'abord les clans
        for clan in clans_data:
            clan_section = f"**{clan['name']}**\n"
            if clan['members']:
                clan_section += "Membres :\n"
                for member in clan['members']:
                    clan_section += f"- {member}\n"
            else:
                clan_section += "Aucun membre\n"
            clan_section += "\n"
            
            # Vérifier si on dépasse la limite de caractères
            if len(current_message) + len(clan_section) > 1800:
                messages.append(current_message)
                current_message = clan_section
            else:
                current_message += clan_section
        
        # Afficher les joueurs sans clan
        if clans_data and clans_data[0]['solo_players']:
            solo_section = "**Joueurs sans clan :**\n"
            for player in clans_data[0]['solo_players']:
                solo_section += f"- {player}\n"
            
            if len(current_message) + len(solo_section) > 1800:
                messages.append(current_message)
                current_message = solo_section
            else:
                current_message += solo_section
        
        # Ajouter le dernier message s'il n'est pas vide
        if current_message:
            messages.append(current_message)

        # Envoyer les messages
        for message in messages:
            await ctx.send(message)
            
    except Exception as e:
        await ctx.send(f"❌ Erreur : {e}")
        print(f"Erreur dans la commande !clans: {e}")

# --------------------------
# 10) Classe KillTracker
# --------------------------
from classement import ClassementManager
import rcon

class KillTracker:
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.classement_manager = ClassementManager()
        self.rcon = rcon.RconClient()
        self.rcon.add_event_callback(self.handle_kill_event)
        self.event_task = None
        self.last_kill_timestamp = None  # Pour éviter les doublons

    async def start_event_monitor(self, bot):
        """Démarre la surveillance des événements du jeu"""
        try:
            self.bot = bot
            self.monitoring = True
            logger.info("Surveillance des événements démarrée")
            # Démarrage de la tâche de surveillance
            self.event_task = asyncio.create_task(self.rcon.monitor_events())
            killtracker_logger.info("Tâche de surveillance des événements démarrée")
            
        except Exception as e:
            killtracker_logger.error(f"Erreur lors du démarrage de la surveillance: {str(e)}")
            killtracker_logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

    async def handle_kill_event(self, event):
        """Gère les événements de kill"""
        if event['type'] == 'kill':
            try:
                killtracker_logger.debug(f"Nouvel événement kill reçu: {event}")
                
                # Vérifier si c'est un kill déjà traité
                if self.last_kill_timestamp and event['timestamp'] <= self.last_kill_timestamp:
                    killtracker_logger.debug(f"Kill ignoré (déjà traité): {event['timestamp']}")
                    return

                # Mettre à jour la base de données locale
                killtracker_logger.info(f"Mise à jour des stats pour {event['killer']} qui a tué {event['victim']}")
                self.classement_manager.update_kill_stats(
                    event['victim'],
                    event['killer'],
                    True
                )
                
                # Envoyer le message dans Discord
                channel = bot.get_channel(self.channel_id)
                if channel:
                    killtracker_logger.debug(f"Channel Discord trouvé: {channel.name}")
                    
                    # Limiter le nombre de messages par minute
                    now = datetime.now()
                    if not hasattr(self, 'last_message_time') or (now - self.last_message_time).total_seconds() > 10:
                        killtracker_logger.info(f"Envoi du message kill dans Discord")
                        await channel.send(f"**Kill** - {event['killer']} a tué {event['victim']} à {event['timestamp']}")
                        self.last_message_time = now
                    else:
                        killtracker_logger.debug("Trop tôt pour envoyer un nouveau message")
                else:
                    killtracker_logger.error("Channel Discord non trouvé")
                
                # Mettre à jour le timestamp du dernier kill
                killtracker_logger.debug(f"Mise à jour du timestamp: {event['timestamp']}")
                self.last_kill_timestamp = event['timestamp']
                
            except Exception as e:
                killtracker_logger.error(f"Erreur lors de la gestion de l'événement kill: {str(e)}")
                killtracker_logger.debug(f"Traceback: {traceback.format_exc()}")

    async def stop_event_monitor(self):
        """Arrêter la surveillance des événements"""
        if self.event_task:
            self.event_task.cancel()
            try:
                await self.event_task
            except asyncio.CancelledError:
                pass
            self.event_task = None
            await self.rcon.disconnect()

    async def update_kills(self, bot):
        """Mise à jour des kills (pour maintenir la compatibilité)"""
        try:
            await self.start_event_monitor(bot)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des kills: {str(e)}")
            raise

async def format_kill_stats(kill_tracker):
    try:
        stats = kill_tracker.classement_manager.get_kill_stats()

        if not stats:
            return """```
Classement des joueurs

Player     | Kills | Deaths | Ratio
-----------------------------------
Aucun joueur enregistré
```"""

        message = """```
Classement des joueurs

Player     | Kills | Deaths | Ratio
-----------------------------------
"""

        for stat in stats:
            player_name = stat['player_name'][:10].ljust(10)
            kills = str(stat['kills']).rjust(5)
            deaths = str(stat['deaths']).rjust(6)
            ratio = str(stat['ratio']).rjust(5)
            message += f"{player_name} | {kills} | {deaths} | {ratio}\n"

        message += "```"
        return message

    except Exception as e:
        logger.error(f"Erreur lors du formatage des stats: {str(e)}")
        return f"Erreur: {str(e)}"

kill_tracker = KillTracker(os.getenv('KILLS_CHANNEL_ID'))
# --------------------------
# 11) Commande !kills
# --------------------------
@bot.command(name='kills')
async def kills_command(ctx):
    """Affiche le classement des kills"""
    try:
        logger.info(f"Commande !kills appelée par {ctx.author.name}")
        stats = format_kill_stats(kill_tracker)
        await ctx.send(stats)
    except Exception as e:
        logger.error(f"Erreur dans la commande !kills: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        await ctx.send(f"❌ Erreur : {e}")

# --------------------------
# 14) Tâche de mise à jour des kills
# --------------------------
@tasks.loop(seconds=5)  # Mise à jour toutes les 5 secondes
async def update_kills_task():
    try:
        # Mettre à jour les kills
        await kill_tracker.update_kills(bot)
        logger.info("Vérification des kills effectuée")
        
        # Mettre à jour le tableau dans le salon
        channel = bot.get_channel(KILLS_CHANNEL_ID)
        if channel:
            stats = await format_kill_stats(kill_tracker)
            await channel.send(stats)
    except Exception as e:
        logger.error(f"Erreur dans la tâche update_kills: {str(e)}")
        # En cas d'erreur, attendre 10 secondes avant de réessayer
        await asyncio.sleep(10)
        # Réessayer une fois
        try:
            await kill_tracker.update_kills(bot)
            channel = bot.get_channel(KILLS_CHANNEL_ID)
            if channel:
                stats = await format_kill_stats(kill_tracker)
                await channel.send(stats)
        except Exception as e:
            logger.error(f"Erreur lors de la réessai: {str(e)}")
            return  # Arrêter la boucle en cas d'échec
        # En cas d'erreur, attendre 10 secondes avant de réessayer
        await asyncio.sleep(10)
        # Réessayer une fois
        try:
            await kill_tracker.update_kills(bot)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des kills: {str(e)}")
            return  # Arrêter la boucle en cas d'échec
# --------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --------------------------
# 16) on_ready
# --------------------------
@bot.event
async def on_ready():
    try:
        logger.info(f"Bot connecté en tant que {bot.user.name}")
        logger.info(f"ID du bot: {bot.user.id}")
        logger.info(f"Nombre de guildes: {len(bot.guilds)}")
        
        # Vérifier les permissions
        guild = bot.guilds[0]
        me = guild.me
        logger.info(f"Permissions du bot: {me.guild_permissions.value}")
        
        # Initialiser le KillTracker
        await kill_tracker.start_event_monitor(bot)
        
        # Démarrer les tâches planifiées
        update_channel_name_task.start()
        build_task.start()
        update_kills_task.start()
        
        logger.info("Bot prêt et toutes les tâches démarrées")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du bot: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise
    
    # Faire une première mise à jour immédiate
    print("Première mise à jour immédiate...")
    await update_channel_name()
    print("Première mise à jour terminée")

# --------------------------
# 15) Tâche de mise à jour des kills
# --------------------------
@tasks.loop(seconds=5)  # Mise à jour toutes les 5 secondes
async def update_kills_task():
    try:
        # Mettre à jour les kills
        await kill_tracker.update_kills(bot)
        logger.info("Vérification des kills effectuée")
        
        # Mettre à jour le tableau dans le salon
        channel_id = int(os.getenv('KILLS_CHANNEL_ID'))
        channel = bot.get_channel(channel_id)
        if channel:
            stats = await format_kill_stats(kill_tracker)
            await channel.send(stats)
        
    except Exception as e:
        logger.error(f"Erreur dans la tâche update_kills: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # En cas d'erreur, attendre 10 secondes avant de réessayer
        await asyncio.sleep(10)
        
        # Réessayer une fois
        try:
            logger.info("Réessai après erreur...")
            await kill_tracker.update_kills(bot)
            channel_id = int(os.getenv('KILLS_CHANNEL_ID'))
            channel = bot.get_channel(channel_id)
            if channel:
                stats = await format_kill_stats(kill_tracker)
                await channel.send(stats)
                logger.info("Réessai réussi")
        except Exception as e:
            logger.error(f"Erreur lors du premier réessai: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            # Attendre encore avant le deuxième réessai
            await asyncio.sleep(10)
            
            # Deuxième réessai
            try:
                logger.info("Deuxième réessai après erreur...")
                await kill_tracker.update_kills(bot)
                logger.info("Deuxième réessai réussi")
            except Exception as e:
                logger.error(f"Erreur lors du deuxième réessai: {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                logger.error("Arrêt de la tâche après deux échecs")
                return  # Arrêter la boucle en cas d'échec

bot.run(DISCORD_TOKEN)
