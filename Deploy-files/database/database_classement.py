import sqlite3
import logging
from config.logging_config import setup_logging

logger = setup_logging()

class DatabaseClassement:
    def __init__(self):
        """Initialise la connexion à la base de données de classement"""
        self.db_path = 'discord.db'
        self.game_db_path = 'game.db'  # Base de données du jeu
        self._initialize_db()

    def _initialize_db(self):
        """Initialise la table de classement si elle n'existe pas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS classement (
                player_id TEXT PRIMARY KEY,
                player_name TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                last_kill TIMESTAMP,
                last_death TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def is_valid_player(self, player_name: str) -> bool:
        """Vérifie si le nom du joueur existe dans la table characters du jeu"""
        conn = sqlite3.connect(self.game_db_path)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT COUNT(*) 
                FROM characters 
                WHERE char_name = ?
            ''', (player_name,))
            count = c.fetchone()[0]
            return count > 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du joueur {player_name}: {e}")
            return False
        finally:
            conn.close()

    def update_kill_stats(self, killer_id: str, killer_name: str, victim_id: str, victim_name: str, is_kill: bool = True):
        """Met à jour les statistiques de kills dans la base de données"""
        # Vérifier si le tueur est un joueur valide
        if is_kill and not self.is_valid_player(killer_name):
            logger.info(f"Kill ignoré car {killer_name} n'est pas un joueur valide")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            if is_kill:
                # Mise à jour du tueur
                c.execute('''
                    INSERT INTO classement (player_id, player_name, kills, last_kill)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(player_id) DO UPDATE SET
                        kills = kills + 1,
                        last_kill = CURRENT_TIMESTAMP,
                        player_name = excluded.player_name
                ''', (killer_id, killer_name))
                
                # Mise à jour de la victime
                c.execute('''
                    INSERT INTO classement (player_id, player_name, deaths, last_death)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(player_id) DO UPDATE SET
                        deaths = deaths + 1,
                        last_death = CURRENT_TIMESTAMP,
                        player_name = excluded.player_name
                ''', (victim_id, victim_name))
            else:
                # Mise à jour de la victime uniquement
                c.execute('''
                    INSERT INTO classement (player_id, player_name, deaths, last_death)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(player_id) DO UPDATE SET
                        deaths = deaths + 1,
                        last_death = CURRENT_TIMESTAMP,
                        player_name = excluded.player_name
                ''', (victim_id, victim_name))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_kill_stats(self):
        """Récupère les statistiques de kills triées par nombre de kills"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # On récupère d'abord les stats de la base de données Discord
            c.execute('''
                SELECT player_name, kills
                FROM classement
                ORDER BY kills DESC
                LIMIT 30
            ''')
            
            stats = c.fetchall()
            
            # On filtre ensuite pour ne garder que les joueurs valides
            valid_stats = []
            for player_name, kills in stats:
                if self.is_valid_player(player_name):
                    valid_stats.append((player_name, kills))
            
            return valid_stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            raise
        finally:
            conn.close()
