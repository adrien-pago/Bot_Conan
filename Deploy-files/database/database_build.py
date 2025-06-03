import os
import sqlite3
from utils.ftp_handler import FTPHandler

def _load_db_from_bytes(db_data):
    """Crée un fichier temporaire avec les données de la base de données"""
    import tempfile
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(db_data)
    temp.close()
    return temp.name

class DatabaseBuildManager:
    def __init__(self):
        """Initialise le chemin de la base de données sur le FTP"""
        self.remote_db = os.getenv('FTP_GAME_DB', 'ConanSandbox/Saved/game.db')  # Valeur par défaut ajoutée

    def get_constructions_by_player(self, ftp_handler: FTPHandler) -> list[dict]:
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
