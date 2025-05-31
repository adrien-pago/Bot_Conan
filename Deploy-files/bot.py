# -*- coding: utf-8 -*-
# bot.py

import os
import sqlite3
import tempfile
import uuid
import time
from dotenv import load_dotenv
import discord
import asyncio
load_dotenv()
from discord.ext import commands, tasks
from ftp_handler import FTPHandler
from rcon import RconClient
from database import DatabaseManager
import datetime
import logging
import traceback
import aiohttp

# Configuration du logging détaillé
logging.basicConfig(
    level=logging.DEBUG,
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
rcon_logger.setLevel(logging.DEBUG)

# Logger spécifique pour le KillTracker
killtracker_logger = logging.getLogger('killtracker')
killtracker_logger.setLevel(logging.DEBUG)

# Configuration du logger Discord
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

# Masquer les avertissements PyNaCl qui ne sont pas pertinents pour nous
discord_logger.propagate = False
for handler in discord_logger.handlers:
    handler.setLevel(logging.DEBUG)

# --------------------------
# 1) Charger les variables
# --------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN or DISCORD_TOKEN.count('.') != 2:
    raise RuntimeError("Le token Discord est manquant ou invalide dans votre .env")

TEST_CHANNEL_ID = int(os.getenv('TEST_CHANNEL_ID', '1375046216097988629'))
KILLS_CHANNEL_ID = int(os.getenv('KILLS_CHANNEL_ID', '1375046216097988629'))

# --------------------------
# 2) Initialiser le Bot
# --------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --------------------------
# 3) Helpers et tâches planifiées
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

async def update_channel_name():
    """Met à jour le nom du salon avec le nombre de joueurs et le statut du raid."""
    try:
        logger.info("Début de la mise à jour du nom du salon...")
        logger.debug("Tentative de connexion RCON...")
        
        # Utilisation de wait_for au lieu de timeout
        try:
            rcon = RconClient()
            await rcon.initialize()  # Initialisation asynchrone
            players = await asyncio.wait_for(rcon.get_online_players(), timeout=10.0)
            logger.debug(f"Nombre de joueurs calculé : {len(players)}")
            rcon.close()
        except asyncio.TimeoutError:
            logger.warning("Timeout lors de la récupération des joueurs")
            players = []
        except Exception as e:
            logger.error(f"Erreur RCON : {str(e)}")
            logger.debug(f"Traceback RCON : {traceback.format_exc()}")
            logger.warning("Utilisation de la valeur par défaut (0 joueurs) suite à l'échec RCON")
            players = []

        # Si RCON échoue, utiliser une valeur par défaut
        if not players:
            logger.warning("Utilisation de la valeur par défaut (0 joueurs) suite à l'échec RCON")
            count = 0
        else:
            count = len(players)
        logger.debug(f"Nombre de joueurs calculé : {count}")
        
        # Vérifier si c'est le raid time
        now = datetime.datetime.now()
        is_raid_time = (
            now.weekday() in [2, 5, 6] and  # Mercredi (2), Samedi (5), Dimanche (6)
            19 <= now.hour < 22  # Entre 19h et 22h
        )
        logger.info(f"Raid time : {is_raid_time}")
        
        # Renommer le salon
        logger.debug("Tentative de récupération du salon...")
        channel = bot.get_channel(1375223092892401737)
        if channel:
            logger.debug("Salon trouvé, mise à jour du nom...")
            try:
                if is_raid_time:
                    new_name = f"🟢【{count}︱40】Raid On"
                else:
                    new_name = f"🟢【{count}︱40】Raid Off"
                logger.debug(f"Nouveau nom du salon : {new_name}")
                await channel.edit(name=new_name)
                logger.info("Nom du salon mis à jour avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du nom : {str(e)}")
                logger.debug(f"Traceback mise à jour nom : {traceback.format_exc()}")
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
            logger.debug(f"Traceback Discord : {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Erreur inattendue : {str(e)}")
        logger.error(traceback.format_exc())
        # En cas d'erreur, mettre à jour avec le statut d'erreur
        try:
            channel = bot.get_channel(1375223092892401737)
            if channel:
                await channel.edit(name="🔴【0︱40】")
                logger.error("Salon mis à jour avec le statut d'erreur")
        except Exception as e2:
            logger.error(f"Erreur lors de la mise à jour du statut d'erreur : {str(e2)}")
            logger.debug(f"Traceback statut d'erreur : {traceback.format_exc()}")

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

ftp_handler = FTPHandler()
last_channel_update = 0  # Timestamp de la dernière mise à jour du salon
UPDATE_COOLDOWN = 300  # 5 minutes en secondes

# Définir les tâches planifiées
@tasks.loop(minutes=8)
async def update_channel_name_task():
    """Tâche planifiée pour mettre à jour le nom du salon toutes les 8 minutes"""
    try:
        logger.info("Exécution de la tâche de mise à jour du salon...")
        await update_channel_name()
        logger.info("Mise à jour du salon réussie")
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du salon : {str(e)}")
        logger.error(traceback.format_exc())

@tasks.loop(minutes=5)
async def build_task():
    """Tâche planifiée pour vérifier les constructions"""
    try:
        logger.info("Exécution de la tâche de vérification des constructions...")
        await build()  # Utilisation de la fonction build existante
        logger.info("Vérification des constructions terminée")
    except Exception as e:
        logger.error(f"Erreur dans la tâche de vérification des constructions: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")

# --------------------------
# 4) Classe KillTracker et initialisation
# --------------------------
from classement import ClassementManager
import rcon

async def format_kill_stats(kill_tracker):
    """Formate les statistiques de kills pour l'affichage"""
    try:
        stats = kill_tracker.classement_manager.get_kill_stats()

        if not stats:
            return """```
Classement des joueurs

Player     | Clan          | Kills | Deaths | Ratio
----------------------------------------------
Aucun joueur enregistré
```"""

        message = """```
Classement des joueurs

Player     | Clan          | Kills | Deaths | Ratio
----------------------------------------------
"""

        for stat in stats:
            player_name = stat['player_name'][:10].ljust(10)
            clan = (stat['clan'] or "Sans clan")[:12].ljust(12)
            kills = str(stat['kills']).rjust(5)
            deaths = str(stat['deaths']).rjust(6)
            ratio = str(stat['ratio']).rjust(5)
            message += f"{player_name} | {clan} | {kills} | {deaths} | {ratio}\n"

        message += "```"
        return message

    except Exception as e:
        logger.error(f"Erreur lors du formatage des stats: {str(e)}")
        return f"Erreur: {str(e)}"

class KillTracker:
    def __init__(self, channel_id: int, rcon_client):
        self.channel_id = channel_id
        self.rcon = rcon_client
        self.monitoring = False
        self.bot = None
        self.update_task = None
        self.classement_manager = ClassementManager()
        self.database = DatabaseManager()
        self.last_message = None  # Pour stocker le dernier message envoyé

    async def start_monitoring(self, bot):
        """Démarre la surveillance des statistiques"""
        self.bot = bot
        self.monitoring = True
        
        # Forcer une mise à jour immédiate
        await self._update_stats()
        
        # Mettre à jour les stats toutes les minutes
        self.update_task = asyncio.create_task(self._periodic_update())
        
    async def _periodic_update(self):
        while self.monitoring:
            try:
                await self._update_stats()
                await asyncio.sleep(60)  # 1 minute
            except Exception as e:
                logger.error(f"Erreur dans la mise à jour périodique: {str(e)}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur

    async def _update_stats(self):
        """Met à jour les statistiques depuis game.db"""
        try:
            # Récupérer les stats depuis game.db
            stats = self.database.get_player_stats(ftp_handler)
            
            if not stats:
                logger.error("Aucune statistique récupérée de game.db")
                return
                
            logger.info(f"Récupération de {len(stats)} joueurs depuis game.db")
            
            # Mettre à jour la base de données locale
            for player_data in stats:
                self.classement_manager.update_from_game_db(player_data)
            
            # Mettre à jour l'affichage Discord
            await self._update_discord_channel()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def _update_discord_channel(self):
        """Met à jour le canal Discord avec le classement"""
        try:
            channel = self.bot.get_channel(int(self.channel_id))
            if channel is None:
                logger.error(f"Canal Discord {self.channel_id} non trouvé")
                return

            # Supprimer tous les messages du canal
            try:
                await channel.purge(limit=100)  # Supprimer les 100 derniers messages
                logger.info("Canal nettoyé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage du canal: {str(e)}")

            # Récupérer les stats
            stats = self.classement_manager.get_kill_stats()
            
            if not stats:
                logger.warning("Aucune statistique trouvée dans la base de données locale")
                return
            
            # Construire les messages
            messages = []
            current_message = "```\nClassement des 30 meilleurs joueurs\n\n"
            current_message += "Rang | Nom          | Kills\n"
            current_message += "-------------------------\n"
            
            for i, stat in enumerate(stats, 1):
                rank = str(i).rjust(3)
                name = stat['player_name'][:12].ljust(12)
                kills = str(stat['kills']).rjust(5)
                line = f"{rank} | {name} | {kills}\n"
                
                # Si le message dépasse 1900 caractères, on le coupe
                if len(current_message) + len(line) > 1900:
                    current_message += "```"
                    messages.append(current_message)
                    current_message = "```\nClassement des 30 meilleurs joueurs (suite)\n\n"
                    current_message += "Rang | Nom          | Kills\n"
                    current_message += "-------------------------\n"
                
                current_message += line
            
            # Ajouter le dernier message s'il n'est pas vide
            if current_message:
                current_message += "```"
                messages.append(current_message)
            
            # Envoyer les messages
            for message in messages:
                await channel.send(message)
                await asyncio.sleep(1)  # Attendre 1 seconde entre chaque message
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du canal Discord: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def stop_monitoring(self):
        """Arrête la surveillance des statistiques"""
        self.monitoring = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

# Initialiser le KillTracker
kill_tracker = KillTracker(os.getenv('KILLS_CHANNEL_ID'), RconClient())

# --------------------------
# 5) on_ready
# --------------------------
@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    try:
        logger.info("Début de l'initialisation du bot")
        logger.info(f"Bot connecté en tant que {bot.user.name}")
        logger.info(f"ID du bot: {bot.user.id}")
        logger.info(f"Nombre de guildes: {len(bot.guilds)}")
        logger.info(f"Permissions du bot: {bot.intents.value}")

        # Démarrer les tâches planifiées
        logger.info("Démarrage des tâches planifiées...")
        update_channel_name_task.start()
        build_task.start()
        logger.info("Tâches planifiées démarrées")

        # Première mise à jour immédiate
        logger.info("Première mise à jour immédiate...")
        await update_channel_name()
        logger.info("Première mise à jour terminée")

        # Initialiser le KillTracker
        logger.info("Initialisation du KillTracker...")
        # Démarrer la surveillance des kills
        await kill_tracker.start_monitoring(bot)
        logger.info("KillTracker initialisé et démarré")

        logger.info("Bot prêt et toutes les tâches démarrées")

    except Exception as e:
        logger.error(f"Erreur dans l'événement on_ready: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise

# --------------------------
# 6) Gestion des erreurs de connexion
# --------------------------
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Erreur dans l'événement {event}: {str(args)}")
    logger.debug(f"Traceback: {traceback.format_exc()}")

@bot.event
async def on_disconnect():
    logger.warning("Bot déconnecté de Discord")

@bot.event
async def on_connect():
    logger.info("Bot connecté à Discord")

# --------------------------
# 7) Fonction de démarrage du bot
# --------------------------
async def start_bot():
    retry_count = 0
    max_retries = 5
    retry_delay = 5

    while retry_count < max_retries:
        try:
            await bot.start(DISCORD_TOKEN)
            break
        except aiohttp.ClientError as e:
            retry_count += 1
            logger.error(f"Erreur de connexion Discord (tentative {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                logger.info(f"Tentative de reconnexion dans {retry_delay} secondes...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Augmenter le délai exponentiellement
            else:
                logger.error("Nombre maximum de tentatives de reconnexion atteint")
                raise
        except Exception as e:
            logger.error(f"Erreur inattendue lors du démarrage du bot: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise

# --------------------------
# 8) Point d'entrée principal
# --------------------------
if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise

# --------------------------
# 9) Commande !build
# --------------------------
@bot.command(name='build')
async def build_command(ctx):
    """Commande !build pour afficher le nombre de pièces de construction"""
    await build()

# Ajouter une variable pour suivre la dernière exécution
last_build_time = 0
BUILD_COOLDOWN = 60  # 60 secondes de cooldown

# --------------------------
# 10) Commande !clans
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
# 11) Commande !kills
# --------------------------
@bot.command(name='kills')
async def kills_command(ctx):
    """Affiche le classement des kills"""
    try:
        stats = await format_kill_stats(kill_tracker)
        await ctx.send(stats)
    except Exception as e:
        logger.error(f"Erreur dans la commande !kills: {e}")
        await ctx.send(f"❌ Erreur : {e}")

async def check_builds():
    """Vérifie les constructions et met à jour le rapport"""
    try:
        logger.info("Vérification des constructions en cours...")
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
                logger.info("Rapport de constructions mis à jour avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du rapport : {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")

    except Exception as e:
        logger.error(f"Erreur lors de la vérification des constructions : {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        error_message = f"❌ Erreur : {e}"
        channel = bot.get_channel(1375234869071708260)
        if channel:
            await channel.send(error_message)
