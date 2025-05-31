# database.py
import sqlite3
import os
from dotenv import load_dotenv
import tempfile
import uuid
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# --------------------------
# 1) Charger les créer un fichier temporaire
# --------------------------
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
# 2) Compter le nombre de pièce par joueur
# --------------------------
class DatabaseManager:
    def __init__(self):
        """Initialise le chemin de la base de données sur le FTP"""
        self.remote_db = os.getenv('FTP_DB_PATH')  # ex. "ConanSandbox/Saved/game.db"

    def get_constructions_by_player(self, ftp_handler) -> list[dict]:
        """
        Récupère le nombre de constructions par joueur, avec le nombre d'instances.
        Retourne une liste de dictionnaires avec les clés:
        - name: nom du joueur
        - clan: nom du clan
        - buildings: nombre de constructions
        - instances: nombre d'instances
        - building_types: liste des types de constructions
        """
        try:
            # Lire la base de données depuis le FTP
            db_data = ftp_handler.read_database(self.remote_db)
            if db_data is None:
                print("❌ Impossible de lire la base de données depuis le FTP")
                return []

            # Créer un fichier temporaire pour la base de données
            temp_path = _load_db_from_bytes(db_data)
            conn = sqlite3.connect(temp_path)
            cur = conn.cursor()

            # Récupérer les noms des clans
            cur.execute("SELECT guildId, name FROM guilds")
            clans = {row[0]: row[1] for row in cur.fetchall()}

            # Requête principale pour obtenir les statistiques de construction
            query = """
                WITH player_buildings AS (
                    SELECT 
                        c.id as char_id,
                        c.char_name,
                        c.guild,
                        b.object_id,
                        COUNT(bi.instance_id) as instance_count
                    FROM characters c
                    LEFT JOIN buildings b ON 
                        CASE 
                            WHEN c.guild IS NULL THEN c.id = b.owner_id
                            ELSE c.guild = b.owner_id
                        END
                    LEFT JOIN building_instances bi ON b.object_id = bi.object_id
                    WHERE c.isAlive = 1
                    GROUP BY c.id, c.char_name, c.guild, b.object_id
                )
                SELECT 
                    char_name,
                    guild,
                    SUM(instance_count) as total_instances,
                    GROUP_CONCAT(DISTINCT object_id) as building_ids
                FROM player_buildings
                GROUP BY char_id, char_name, guild
                ORDER BY total_instances DESC, char_name
            """
            
            cur.execute(query)
            results = []
            
            for row in cur.fetchall():
                name, guild_id, instances, building_ids = row
                clan_name = clans.get(guild_id, "Pas de clan") if guild_id else "Pas de clan"
                
                # Convertir la chaîne de building_ids en liste
                building_types = building_ids.split(',') if building_ids else []
                
                results.append({
                    'name': name,
                    'clan': clan_name,
                    'buildings': 0,  # On ne compte plus les buildings
                    'instances': instances or 0,
                    'building_types': building_types
                })

            conn.close()
            os.remove(temp_path)
            return results

        except Exception as e:
            print(f"❌ Erreur dans get_constructions_by_player: {e}")
            return []

    def get_clans_and_players(self, ftp_handler) -> list[dict]:
        """
        Récupère la liste des clans avec leurs membres et les joueurs sans clan.
        Retourne une liste de dictionnaires avec les clés:
        - name: nom du clan
        - members: liste des membres du clan
        - solo_players: liste des joueurs sans clan
        """
        try:
            # Lire la base de données depuis le FTP
            db_data = ftp_handler.read_database(self.remote_db)
            if db_data is None:
                print("❌ Impossible de lire la base de données depuis le FTP")
                return []

            # Créer un fichier temporaire pour la base de données
            temp_path = _load_db_from_bytes(db_data)
            conn = sqlite3.connect(temp_path)
            cur = conn.cursor()

            # Requête pour obtenir les clans et leurs membres
            query = """
                WITH clan_members AS (
                    SELECT 
                        g.guildId,
                        g.name as clan_name,
                        c.char_name,
                        c.level,
                        c.lastTimeOnline
                    FROM guilds g
                    LEFT JOIN characters c ON g.guildId = c.guild
                    WHERE c.isAlive = 1
                ),
                solo_players AS (
                    SELECT 
                        char_name,
                        level,
                        lastTimeOnline
                    FROM characters
                    WHERE guild IS NULL AND isAlive = 1
                )
                SELECT 
                    clan_name,
                    GROUP_CONCAT(char_name || ' (Niveau ' || level || ')') as members,
                    (SELECT GROUP_CONCAT(char_name || ' (Niveau ' || level || ')')
                     FROM solo_players) as solo_players
                FROM clan_members
                GROUP BY clan_name
                ORDER BY clan_name
            """
            
            cur.execute(query)
            results = []
            
            for row in cur.fetchall():
                clan_name, members, solo_players = row
                
                # Convertir les chaînes en listes
                members_list = members.split(',') if members else []
                solo_players_list = solo_players.split(',') if solo_players else []
                
                results.append({
                    'name': clan_name,
                    'members': members_list,
                    'solo_players': solo_players_list
                })

            conn.close()
            os.remove(temp_path)
            return results

        except Exception as e:
            print(f"❌ Erreur dans get_clans_and_players: {e}")
            return []

    def get_player_stats(self, ftp_handler):
        """Récupère les statistiques des joueurs depuis la base de données du jeu"""
        temp_db_path = None
        conn = None
        try:
            # Utiliser le chemin depuis les variables d'environnement
            game_db_path = os.getenv('FTP_DB_PATH')
            if not game_db_path:
                logger.error("FTP_DB_PATH non défini dans les variables d'environnement")
                return []
            
            # Lire la base de données depuis le FTP
            db_bytes = ftp_handler.read_database(game_db_path)
            if not db_bytes:
                logger.error("Impossible de lire la base de données du jeu")
                return []
            
            # Écrire la base de données dans un fichier temporaire
            temp_db_path = _load_db_from_bytes(db_bytes)
            
            # Se connecter à la base de données
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Requête pour obtenir les statistiques des joueurs
            cursor.execute("""
                SELECT 
                    id,
                    char_name,
                    level,
                    rank,
                    guild,
                    isAlive,
                    killerName,
                    lastTimeOnline,
                    killerId,
                    lastServerTimeOnline
                FROM characters
                WHERE isAlive IS NOT NULL
                ORDER BY lastTimeOnline DESC
            """)
            
            stats = cursor.fetchall()
            cursor.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {str(e)}")
            return []
        finally:
            # Fermer la connexion
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    logger.error(f"Erreur lors de la fermeture de la connexion: {str(e)}")
            
            # Supprimer le fichier temporaire
            if temp_db_path and os.path.exists(temp_db_path):
                try:
                    os.remove(temp_db_path)
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression du fichier temporaire: {str(e)}")
