# classement.py
import sqlite3
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class ClassementManager:
    def __init__(self):
        """Initialise la base de données locale pour le classement"""
        self.db_path = 'discord.db'
        self._initialize_db()
        self.last_update_time = 0

    def _initialize_db(self):
        """Crée la base de données et la table classement si elles n'existent pas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Supprimer la table si elle existe
            cursor.execute("DROP TABLE IF EXISTS classement")
            
            # Créer la table avec les bonnes colonnes
            cursor.execute('''
                CREATE TABLE classement (
                    player_id TEXT PRIMARY KEY,
                    player_name TEXT,
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_death_time INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Base de données de classement initialisée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
            raise

    def update_from_game_db(self, player_data):
        """Met à jour les statistiques à partir des données du jeu"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Format des données: id, char_name, level, rank, guild, isAlive, killerName, lastTimeOnline, killerId, lastServerTimeOnline
            player_id = str(player_data[0])
            player_name = player_data[1]
            is_alive = player_data[5]
            killer_name = player_data[6]
            last_time_online = player_data[7]
            
            # Vérifier si le joueur existe déjà
            cursor.execute("SELECT * FROM classement WHERE player_id = ?", (player_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Si le joueur est mort
                if not is_alive:
                    # Vérifier si c'est une nouvelle mort
                    if last_time_online > existing[5]:
                        # Mettre à jour les stats
                        cursor.execute("""
                            UPDATE classement 
                            SET deaths = deaths + 1,
                                last_update = CURRENT_TIMESTAMP,
                                last_death_time = ?
                            WHERE player_id = ?
                        """, (last_time_online, player_id))
                        
                        # Si le joueur a un tueur, mettre à jour ses kills
                        if killer_name:
                            cursor.execute("""
                                UPDATE classement 
                                SET kills = kills + 1,
                                    last_update = CURRENT_TIMESTAMP
                                WHERE player_name = ?
                            """, (killer_name,))
                            
                            # Si le tueur n'existe pas encore, le créer
                            cursor.execute("SELECT COUNT(*) FROM classement WHERE player_name = ?", (killer_name,))
                            if cursor.fetchone()[0] == 0:
                                cursor.execute("""
                                    INSERT INTO classement (player_id, player_name, kills, last_update)
                                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                                """, (f"killer_{killer_name}", killer_name))
            else:
                # Créer une nouvelle entrée
                cursor.execute("""
                    INSERT INTO classement (player_id, player_name, deaths, last_update, last_death_time)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (player_id, player_name, 1 if not is_alive else 0, last_time_online if not is_alive else 0))
                
                # Si le joueur est mort et a un tueur, mettre à jour les kills du tueur
                if not is_alive and killer_name:
                    cursor.execute("""
                        UPDATE classement 
                        SET kills = kills + 1,
                            last_update = CURRENT_TIMESTAMP
                        WHERE player_name = ?
                    """, (killer_name,))
                    
                    # Si le tueur n'existe pas encore, le créer
                    cursor.execute("SELECT COUNT(*) FROM classement WHERE player_name = ?", (killer_name,))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("""
                            INSERT INTO classement (player_id, player_name, kills, last_update)
                            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                        """, (f"killer_{killer_name}", killer_name))
            
            conn.commit()
            conn.close()
            logger.info(f"Statistiques mises à jour pour {player_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des statistiques: {str(e)}")
            raise

    def get_kill_stats(self) -> list[dict]:
        """Retourne les statistiques des kills triées par nombre de kills"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT player_name, kills, deaths
                FROM classement 
                ORDER BY kills DESC, deaths ASC
                LIMIT 30
            """)
            
            stats = cursor.fetchall()
            conn.close()
            
            # Formater les stats
            formatted_stats = []
            for row in stats:
                player_name = row[0]
                kills = row[1]
                deaths = row[2]
                
                formatted_stats.append({
                    'player_name': player_name,
                    'kills': kills,
                    'deaths': deaths
                })
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            raise
