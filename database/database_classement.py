import sqlite3
import logging
from config.logging_config import setup_logging
import time
import os
from dotenv import load_dotenv

load_dotenv()

logger = setup_logging()

class DatabaseClassement:
    def __init__(self):
        """Initialise la connexion à la base de données de classement"""
        self.db_path = 'discord.db'
        self.game_db_path = os.getenv('FTP_GAME_DB', 'ConanSandbox/Saved/game.db')
        self._initialize_db()
        self.last_check_time = 0
        logger.info(f"DatabaseClassement initialisé avec game_db_path: {self.game_db_path}")

    def _initialize_db(self):
        """Initialise la table de classement si elle n'existe pas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS classement (
                player_name TEXT PRIMARY KEY,
                kills INTEGER DEFAULT 0,
                last_kill TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def check_kills(self, ftp_handler):
        """Vérifie les kills dans la base de données du jeu"""
        try:
            # Lire la base de données du jeu
            db_data = ftp_handler.read_database(self.game_db_path)
            if db_data is None:
                logger.error("Impossible de lire la base de données du jeu")
                return

            # Créer un fichier temporaire pour la base de données
            temp_path = self._load_db_from_bytes(db_data)
            conn = sqlite3.connect(temp_path)
            c = conn.cursor()

            # Récupérer les joueurs morts avec leur tueur
            # On vérifie que le killerName existe bien comme joueur dans la table
            c.execute('''
                SELECT c1.char_name, c1.killerName, c1.lastTimeOnline
                FROM characters c1
                INNER JOIN characters c2 ON c1.killerName = c2.char_name
                WHERE c1.isAlive = 0 
                AND c1.killerName IS NOT NULL
                AND c1.killerName != c1.char_name  -- Évite les suicides
                ORDER BY c1.lastTimeOnline DESC
            ''')
            
            kills = c.fetchall()
            conn.close()
            os.remove(temp_path)

            # Mettre à jour les stats
            for victim_name, killer_name, last_time in kills:
                self.update_kill_stats(killer_name, last_time)

        except Exception as e:
            logger.error(f"Erreur lors de la vérification des kills: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def update_kill_stats(self, killer_name: str, kill_time: int):
        """Met à jour les statistiques de kills dans la base de données"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # Vérifier si le kill a déjà été comptabilisé
            c.execute('''
                SELECT last_kill FROM classement 
                WHERE player_name = ?
            ''', (killer_name,))
            
            result = c.fetchone()
            if result and result[0] and int(result[0]) >= kill_time:
                return  # Le kill a déjà été comptabilisé
            
            # Mettre à jour ou insérer les stats
            c.execute('''
                INSERT OR REPLACE INTO classement (player_name, kills, last_kill)
                VALUES (
                    ?,
                    COALESCE((SELECT kills + 1 FROM classement WHERE player_name = ?), 1),
                    ?
                )
            ''', (killer_name, killer_name, kill_time))
            
            conn.commit()
            logger.info(f"Stats mises à jour pour {killer_name}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_kill_stats(self):
        """Récupère les statistiques de kills triées par nombre de kills"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT DISTINCT player_name, kills
                FROM classement
                WHERE player_name IS NOT NULL 
                AND player_name != ''
                ORDER BY kills DESC, player_name ASC
                LIMIT 30
            ''')
            
            stats = c.fetchall()
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return []
        finally:
            conn.close()

    def _load_db_from_bytes(self, db_data):
        """Crée un fichier temporaire avec les données de la base de données"""
        import tempfile
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(db_data)
        temp.close()
        return temp.name
