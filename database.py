# database.py
import sqlite3
import os
from dotenv import load_dotenv
import tempfile
import uuid

load_dotenv()

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
        self.local_db = 'game.db.local'
        self.remote_db = os.getenv('FTP_DB_PATH')  # ex. "ConanSandbox/Saved/1388322/game.db"

    def download_database(self, ftp_handler) -> bool:
        if not ftp_handler.download_file(self.remote_db, self.local_db):
            return False
        
        # Vérifier si la base de données est accessible
        try:
            conn = sqlite3.connect(self.local_db)
            conn.close()
            print(f"✅ Base de données {self.local_db} téléchargée et accessible")
            return True
        except Exception as e:
            print(f"❌ Impossible d'accéder à la base de données : {e}")
            return False

    def get_constructions_by_player(self, ftp_handler) -> list[dict]:
        """
        Récupère le nombre de constructions par joueur, avec le nombre d'instances.
        Retourne une liste de dictionnaires avec les clés:
        - name: nom du joueur
        - clan: nom du clan
        - buildings: nombre de constructions
        - instances: nombre d'instances
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

            # Récupérer les informations détaillées pour comprendre la structure des données
            debug_query = """
                SELECT 
                    c.id as char_id,
                    c.char_name,
                    c.guild,
                    b.object_id,
                    bi.instance_id,
                    bi.class as building_class
                FROM characters c
                LEFT JOIN buildings b ON c.id = b.owner_id
                LEFT JOIN building_instances bi ON b.object_id = bi.object_id
                WHERE c.isAlive = 1
                ORDER BY c.char_name, b.object_id, bi.instance_id
            """
            
            cur.execute(debug_query)
            debug_results = cur.fetchall()
            
            # Créer un dictionnaire pour stocker les données par joueur
            player_buildings = {}
            for row in debug_results:
                char_id, name, guild_id, object_id, instance_id, building_class = row
                if name not in player_buildings:
                    player_buildings[name] = {
                        'guild_id': guild_id,
                        'buildings': set(),
                        'instances': set(),
                        'classes': set()
                    }
                if object_id:
                    player_buildings[name]['buildings'].add(object_id)
                    if instance_id:
                        player_buildings[name]['instances'].add(instance_id)
                        if building_class:
                            player_buildings[name]['classes'].add(building_class)

            # Construire le résultat final
            results = []
            for name, data in player_buildings.items():
                clan_name = clans.get(data['guild_id'], "Pas de clan") if data['guild_id'] else "Pas de clan"
                results.append({
                    'name': name,
                    'clan': clan_name,
                    'buildings': len(data['buildings']),
                    'instances': len(data['instances']),
                    'building_types': list(data['classes']) if data['classes'] else []
                })

            # Récupérer les noms des clans
            cur.execute("SELECT guildId, name FROM guilds")
            clans = {row[0]: row[1] for row in cur.fetchall()}

            # Construire la liste des résultats
            results = []
            for player_id, name, guild_id, building_count, instance_count in players:
                clan_name = clans.get(guild_id, "Pas de clan") if guild_id else "Pas de clan"
                results.append({
                    'name': name,
                    'clan': clan_name,
                    'buildings': building_count,
                    'instances': instance_count
                })

            conn.close()
            os.remove(temp_path)
            return results

        except Exception as e:
            print(f"❌ Erreur dans get_constructions_by_player: {e}")
            return []
