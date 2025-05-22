import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from ftp_handler import FTPHandler
from database import DatabaseManager
from rcon import ServerQuery

# Configuration et initialisation
load_dotenv()

# Configuration Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialisation des gestionnaires
ftp_handler = FTPHandler()
database = DatabaseManager()
server_query = ServerQuery()

# Événements
@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    print(f'Connecté en tant que {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('------')
    
    # Essayer de se connecter au FTP et télécharger la base de données
    try:
        if ftp_handler.test_connection():
            print("✅ Connexion FTP réussie !")
            
            # Télécharger la base de données
            if database.download_database(ftp_handler):
                print("✅ Base de données téléchargée avec succès !")
            else:
                print("❌ Échec du téléchargement de la base de données")
        else:
            print("❌ Connexion FTP échouée !")
    except Exception as e:
        print(f"❌ Connexion FTP échouée : {str(e)}")

# Commandes
@bot.command(name='structure')
async def show_structure(ctx):
    """Affiche la structure des dossiers FTP"""
    try:
        # Récupérer la structure des dossiers
        directory_structure = ftp_handler.get_directory_structure()
        
        # Convertir la structure en format lisible
        def format_structure(structure, indent=0):
            result = []
            for name, content in structure.items():
                if isinstance(content, dict):
                    result.append(f"{' ' * indent}📁 {name}/")
                    result.extend(format_structure(content, indent + 4))
                else:
                    result.append(f"{' ' * indent}📄 {name} ({content})")
            return result
        
        # Créer le message avec la structure
        message = "**Structure des dossiers :**\n" + '\n'.join(format_structure(directory_structure))
        
        # Diviser le message en plusieurs parties si nécessaire
        max_length = 1900  # Discord limite à 2000 caractères, on prend un peu moins
        message_parts = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        
        for part in message_parts:
            try:
                await ctx.send(part)
            except Exception as e:
                print(f"Erreur lors de l'envoi du message : {str(e)}")
    except Exception as e:
        await ctx.send(f"❌ Erreur : {str(e)}")

@bot.command(name='joueurs')
async def show_players(ctx):
    """Affiche la liste des joueurs connectés et leurs clans"""
    try:
        # Récupérer les joueurs en ligne via la requête serveur
        online_players = server_query.get_online_players()
        
        if not online_players:
            await ctx.send("❌ Impossible de récupérer la liste des joueurs en ligne")
            return
            
        # Récupérer les informations des clans depuis la base de données
        database.download_database(ftp_handler)
        players_and_clans = database.get_players_and_clans()
        
        # Créer un dictionnaire pour une recherche rapide des clans
        player_to_clan = {player: clan for player, clan in players_and_clans}
        
        # Construire le message
        message = "**Joueurs connectés :**\n"
        for player in online_players:
            clan = player_to_clan.get(player, "Pas de clan")
            message += f"- {player} ({clan})\n"
            
        if not online_players:
            message = "Aucun joueur connecté actuellement"
            
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Erreur : {str(e)}")

@bot.command(name='clans')
async def show_clans(ctx):
    """Affiche la liste des clans avec leur nombre de membres"""
    try:
        # Récupérer les informations des clans depuis la base de données
        database.download_database(ftp_handler)
        players_and_clans = database.get_players_and_clans()
        
        if not players_and_clans:
            await ctx.send("❌ Impossible de récupérer les informations des clans")
            return
            
        # Compter les membres par clan
        clan_counts = {}
        for _, clan in players_and_clans:
            if clan:
                clan_counts[clan] = clan_counts.get(clan, 0) + 1
        
        # Construire le message
        message = "**Clans :**\n"
        for clan, count in sorted(clan_counts.items(), key=lambda x: x[1], reverse=True):
            message += f"- {clan} ({count} membres)\n"
            
        if not clan_counts:
            message = "Aucun clan trouvé"
            
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Erreur : {str(e)}")

# Lancement du bot
bot.run(os.getenv('DISCORD_TOKEN'))
