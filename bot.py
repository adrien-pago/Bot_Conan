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

# --------------------------
# 5) Commande !joueurs
# --------------------------
@bot.command(name='joueurs')
async def joueurs(ctx):
    """
    !joueurs → affiche simplement le nombre de joueurs actuellement connectés.
    """
    # 1) Récupérer la liste des joueurs en ligne via RCON
    try:
        rcon = RconClient()
        online = rcon.get_online_players()
        rcon.close()
    except Exception as e:
        return await ctx.send(f"❌ Erreur RCON : {e}")

    # 2) Calculer et afficher uniquement le nombre
    total_slots = 40  # Remplacez par le nombre max réel de votre serveur
    count = len(online)
    await ctx.send(f"Nombre joueur connecté : {count}/{total_slots}")

# --------------------------
# 6) Commande !build
# --------------------------
@bot.command(name='build')
async def build(ctx):
    """
    !build → affiche le nombre de pièces de construction par joueur
    """
    try:
        # Récupérer les données depuis le FTP
        database = DatabaseManager()
        constructions = database.get_constructions_by_player(ftp_handler)
        
        if not constructions:
            return await ctx.send("Aucune construction trouvée.")

        # Construire le message
        lines = ["**Nombre de pièces de construction par joueur :**"]
        
        # Trier les joueurs par nombre d'instances
        constructions.sort(key=lambda x: x['instances'], reverse=True)
        
        for player in constructions:
            if player['instances'] > 0:
                # Simplifier les types de constructions pour l'affichage
                building_types = []
                for btype in player['building_types']:
                    # Extraire le nom simple du type de construction
                    simple_type = btype.split('/')[-1].replace('_C', '')
                    building_types.append(simple_type)
                
                types_str = ", ".join(building_types) if building_types else "N/A"
                line = f"- {player['name']} ({player['clan']}) : {player['instances']} pièces - Types: {types_str}"
                lines.append(line)
            else:
                lines.append(f"- {player['name']} ({player['clan']}) : Pas de construction")

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

        # Envoyer les messages
        for message in messages:
            await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Erreur : {e}")
        print(f"Erreur dans la commande !build: {e}")

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
