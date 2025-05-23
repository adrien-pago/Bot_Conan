# bot.py

import os
import sqlite3
import tempfile
import uuid
from dotenv import load_dotenv
import discord
from discord.ext import commands
from ftp_handler import FTPHandler
from rcon import RconClient
from database import DatabaseManager
import time
import datetime
from discord.ext import tasks
import asyncio

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
ftp_handler = FTPHandler()
last_channel_update = 0  # Timestamp de la dernière mise à jour du salon
UPDATE_COOLDOWN = 300  # 5 minutes en secondes

def _load_db_from_bytes(db_bytes: bytes) -> str:
    """
    Écrit db_bytes dans un fichier temporaire sur disque, et renvoie son chemin.
    Il faut fermer le fichier avant de l'ouvrir avec sqlite3 sur Windows.
    """
    tmp_dir = tempfile.gettempdir()
    tmp_name = f"conan_db_{uuid.uuid4().hex}.db"
    tmp_path = os.path.join(tmp_dir, tmp_name)
    with open(tmp_path, 'wb') as f:
        f.write(db_bytes)
    return tmp_path

async def update_channel_name():
    """Met à jour le nom du salon avec le nombre de joueurs"""
    try:
        print("Début de la mise à jour du nom du salon...")
        # Récupérer la liste des joueurs en ligne via RCON
        rcon = RconClient()
        online = rcon.get_online_players()
        rcon.close()
        print(f"Nombre de joueurs en ligne : {len(online)}")

        # Calculer le nombre
        total_slots = 40
        count = len(online)
        
        # Vérifier si c'est le raid time
        now = datetime.datetime.now()
        is_raid_time = (
            now.weekday() in [2, 5, 6] and  # Mercredi (2), Samedi (5), Dimanche (6)
            19 <= now.hour < 22  # Entre 19h et 22h
        )
        print(f"Raid time : {is_raid_time}")
        
        # Renommer le salon
        channel = bot.get_channel(1375223092892401737)
        if channel:
            if is_raid_time:
                await channel.edit(name=f"🟢〔{count}〕Players ⚔️")
            else:
                await channel.edit(name=f"🟢〔{count}〕Players 🛡️")
            print("Nom du salon mis à jour avec succès")
        else:
            print("Salon non trouvé")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du salon : {e}")
        # En cas d'erreur, mettre à jour avec le statut d'erreur
        channel = bot.get_channel(1375223092892401737)
        if channel:
            await channel.edit(name="🔴 〔0-40〕 ")
            print("Salon mis à jour avec le statut d'erreur")

@tasks.loop(minutes=5)
async def update_channel_name_task():
    """Tâche planifiée pour mettre à jour le nom du salon toutes les 5 minutes"""
    print("Exécution de la tâche de mise à jour du salon...")
    try:
        await update_channel_name()
        print("Mise à jour du salon réussie")
        # Ajouter un délai pour éviter le rate limit
        await asyncio.sleep(2)
    except Exception as e:
        print(f"Erreur dans la tâche de mise à jour du salon : {e}")

# --------------------------
# 4) on_ready
# --------------------------
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user} (ID: {bot.user.id})")
    channel = bot.get_channel(TEST_CHANNEL_ID)
    if not channel:
        return print(f"❌ Salon {TEST_CHANNEL_ID} introuvable")
    await channel.send("✅ Bot démarré, connexion FTP OK !" if ftp_handler.test_connection()
                       else "❌ Connexion FTP échouée !")
    
    # Démarrer les tâches planifiées
    print("Démarrage des tâches planifiées...")
    update_channel_name_task.start()
    build_task.start()
    print("Tâches planifiées démarrées")
    
    # Faire une première mise à jour immédiate
    print("Première mise à jour immédiate...")
    await update_channel_name()
    await build(None)
    print("Première mise à jour terminée")

# --------------------------
# 5) Commande !build
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

        # Construire le message
        lines = [f"**Nombre de pièces de construction par clan (Limite: {LIMITE_CONSTRUCTION} pièces) :**"]
        
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
        
        # Variables pour suivre les dépassements
        has_exceeded_limit = False
        has_under_limit = False
        
        for clan in clans_list:
            if clan['average'] > 0:
                # Vérifier si la limite est dépassée
                if clan['average'] > LIMITE_CONSTRUCTION:
                    has_exceeded_limit = True
                    excess = clan['average'] - LIMITE_CONSTRUCTION
                    line = f"\n❌ **Clan ({clan['name']})** : {clan['average']} pièces (+{excess} au-dessus de la limite)"
                    lines.append(line)
                else:
                    has_under_limit = True

        # Ajouter un message pour les clans sous la limite
        if has_under_limit:
            lines.append("\n✅ Pour les autres clans, tout est bon !")

        # Ajouter un message de félicitations si personne ne dépasse la limite
        if not has_exceeded_limit:
            lines.append("\n✅ **Bravo ! Tous les clans respectent la limite de construction !**")

        # Diviser le message en plusieurs parties si nécessaire
        max_length = 1800  # Laisser un peu de marge
        current_message = ""
        messages = []
        
        for line in lines:
            if len(current_message) + len(line) + 1 > max_length and current_message:
                messages.append(current_message)
                current_message = line
            else:
                if current_message:
                    current_message += "\n"
                current_message += line
        
        if current_message:
            messages.append(current_message)

        # Envoyer les messages uniquement dans le salon de rapport
        report_channel = bot.get_channel(1375234869071708260)
        if report_channel:
            try:
                # Supprimer tous les messages existants
                await report_channel.purge(limit=10)
                
                # Attendre un court instant pour s'assurer que les messages sont supprimés
                await asyncio.sleep(1)
                
                # Envoyer les nouveaux messages
                for message in messages:
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

@tasks.loop(hours=1)
async def build_task():
    """Tâche planifiée pour exécuter la commande build toutes les heures"""
    global last_build_time
    current_time = time.time()
    
    # Vérifier si assez de temps s'est écoulé depuis la dernière exécution
    if current_time - last_build_time >= BUILD_COOLDOWN:
        try:
            await build(None)
            last_build_time = current_time
            # Ajouter un délai pour éviter le rate limit
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Erreur dans la tâche build : {e}")

# --------------------------
# 7) Commande !clans
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
# 8) Démarrage du Bot
# --------------------------
bot.run(DISCORD_TOKEN)
