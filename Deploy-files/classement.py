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

    def _initialize_db(self):
        """Crée la base de données et la table classement si elles n'existent pas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS classement (
                    player_id TEXT PRIMARY KEY,
                    player_name TEXT,
                    kills INTEGER DEFAULT 0,
                    deaths INTEGER DEFAULT 0,
                    last_kill TIMESTAMP,
                    last_death TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Base de données de classement initialisée")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
            raise

    def update_kill_stats(self, player_id: str, player_name: str, is_kill: bool):
        """Met à jour les statistiques de kills pour un joueur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier si le joueur existe déjà
            cursor.execute("SELECT * FROM classement WHERE player_id = ?", (player_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Mettre à jour les statistiques existantes
                if is_kill:
                    cursor.execute("""
                        UPDATE classement 
                        SET kills = kills + 1, 
                            last_kill = CURRENT_TIMESTAMP 
                        WHERE player_id = ?
                    """, (player_id,))
                else:
                    cursor.execute("""
                        UPDATE classement 
                        SET deaths = deaths + 1, 
                            last_death = CURRENT_TIMESTAMP 
                        WHERE player_id = ?
                    """, (player_id,))
            else:
                # Créer une nouvelle entrée
                cursor.execute("""
                    INSERT INTO classement (player_id, player_name, kills, deaths, last_kill, last_death)
                    VALUES (?, ?, ?, ?, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END, 
                            CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END)
                """, (player_id, player_name, 1 if is_kill else 0, 1 if not is_kill else 0, is_kill, not is_kill))
            
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
                ORDER BY kills DESC
                LIMIT 10
            """)
            
            stats = cursor.fetchall()
            conn.close()
            
            # Calculer le ratio pour chaque joueur
            formatted_stats = []
            for row in stats:
                player_name = row[0]
                kills = row[1]
                deaths = row[2]
                
                # Calculer le ratio (kills - deaths)
                ratio = kills - deaths if deaths > 0 else kills
                
                formatted_stats.append({
                    'player_name': player_name,
                    'kills': kills,
                    'deaths': deaths,
                    'ratio': ratio
                })
            
            return formatted_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
            raise
