# database.py
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
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

    def get_constructions_by_clan(self, ftp_handler) -> list[tuple[str, int]]:
        """Récupère le nombre de constructions par clan en lisant directement depuis le FTP"""
        try:
            # Lire la base de données depuis le FTP
            db_data = ftp_handler.read_database(self.remote_db)
            if db_data is None:
                return []
            
            # Créer une connexion SQLite en mémoire
            from io import BytesIO
            
            # Créer une base de données temporaire en mémoire
            with BytesIO(db_data) as f:
                # Sauvegarder temporairement la base de données
                temp_path = 'temp.db'
                with open(temp_path, 'wb') as temp_file:
                    temp_file.write(f.read())
                
                # Ouvrir la base de données temporaire
                conn = sqlite3.connect(temp_path)
                cur = conn.cursor()
                
                # D'abord récupérer tous les clans
                cur.execute("SELECT guildId, name FROM guilds ORDER BY name")
                all_guilds = cur.fetchall()
                
                # Ensuite récupérer les constructions
                query = """
                    SELECT 
                        g.name AS GuildName,
                        COUNT(b.object_id) AS BuildingCount,
                        COUNT(DISTINCT bi.instance_id) AS InstanceCount
                    FROM guilds g
                    LEFT JOIN buildings b ON g.guildId = b.owner_id
                    LEFT JOIN building_instances bi ON b.object_id = bi.object_id
                    GROUP BY g.guildId, g.name
                    ORDER BY BuildingCount DESC
                """
                
                cur.execute(query)
                constructions = cur.fetchall()
                
                # Construire le résultat final
                results = []
                for guild_id, guild_name in all_guilds:
                    # Chercher les données de construction pour ce clan
                    found = False
                    for clan_name, building_count, instance_count in constructions:
                        if clan_name == guild_name:
                            found = True
                            results.append((guild_name, building_count, instance_count))
                            break
                    
                    # Si le clan n'a pas de construction, l'ajouter avec 0
                    if not found:
                        results.append((guild_name, 0, 0))
                
                conn.close()
                
                # Nettoyer le fichier temporaire
                import os
                os.remove(temp_path)
                
                return results
            
        except Exception as e:
            print(f"❌ Erreur dans get_constructions_by_clan: {e}")
            return []

    def get_players_and_clans(self, ftp_handler=None) -> dict:
        """Récupère les clans et leurs membres, ainsi que les joueurs sans clan"""
        try:
            # Lire la base de données depuis le FTP si spécifié, sinon utiliser la locale
            if ftp_handler:
                db_data = ftp_handler.read_database(self.remote_db)
                if db_data is None:
                    return {}
                
                # Créer une base de données temporaire
                from io import BytesIO
                with BytesIO(db_data) as f:
                    temp_path = 'temp.db'
                    with open(temp_path, 'wb') as temp_file:
                        temp_file.write(f.read())
                    conn = sqlite3.connect(temp_path)
            else:
                conn = sqlite3.connect(self.local_db)
            
            cur = conn.cursor()
            
            # Récupérer tous les clans
            cur.execute("SELECT guildId, name FROM guilds ORDER BY name")
            clans = {row[0]: row[1] for row in cur.fetchall()}
            
            # Récupérer tous les joueurs
            query = """
                SELECT 
                    c.id,
                    c.char_name,
                    c.guild,
                    c.level,
                    c.rank
                FROM characters c
                WHERE c.isAlive = 1
                ORDER BY c.guild, c.char_name
            """
            
            cur.execute(query)
            players = cur.fetchall()
            
            # Construire la structure des données
            result = {
                'clans': {},
                'sans_clan': []
            }
            
            # Organiser les joueurs par clan
            for player_id, name, guild_id, level, rank in players:
                if guild_id in clans:
                    clan_name = clans[guild_id]
                    if clan_name not in result['clans']:
                        result['clans'][clan_name] = []
                    result['clans'][clan_name].append({
                        'name': name,
                        'level': level,
                        'rank': rank
                    })
                else:
                    result['sans_clan'].append({
                        'name': name,
                        'level': level,
                        'rank': rank
                    })
            
            conn.close()
            
            if ftp_handler:
                import os
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            print(f"❌ Erreur dans get_players_and_clans: {e}")
            return {}
