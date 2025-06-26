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
        self.processed_kills = set()  # Cache des kills déjà traités
        logger.info(f"DatabaseClassement initialisé avec game_db_path: {self.game_db_path}")

    def _initialize_db(self):
        """Initialise la table de classement si elle n'existe pas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS classement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                original_name TEXT NOT NULL,
                kills INTEGER DEFAULT 0,
                last_kill TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_name)
            )
        ''')
        conn.commit()
        conn.close()

    def check_kills(self, ftp_handler):
        """Vérifie les kills dans la base de données du jeu et retourne True si de nouveaux kills sont détectés"""
        try:
            # Lire la base de données du jeu
            db_data = ftp_handler.read_database(self.game_db_path)
            if db_data is None:
                logger.error("Impossible de lire la base de données du jeu")
                return False

            # Créer un fichier temporaire pour la base de données
            temp_path = self._load_db_from_bytes(db_data)
            conn = sqlite3.connect(temp_path)
            c = conn.cursor()

            # Récupérer SEULEMENT les morts récentes (plus efficace)
            # On utilise lastTimeOnline pour filtrer les morts récentes
            current_time = int(time.time())
            time_threshold = current_time - 300  # 5 minutes en arrière pour être sûr

            c.execute('''
                SELECT c1.char_name as victim, 
                       c1.killerName as killer, 
                       c1.lastTimeOnline as death_time,
                       c2.char_name as killer_confirmed
                FROM characters c1
                INNER JOIN characters c2 ON c1.killerName = c2.char_name
                WHERE c1.isAlive = 0 
                AND c1.killerName IS NOT NULL
                AND c1.killerName != c1.char_name  -- Évite les suicides
                AND c1.lastTimeOnline > ?  -- Seulement les morts récentes
                ORDER BY c1.lastTimeOnline DESC
            ''', (time_threshold,))
            
            recent_kills = c.fetchall()
            conn.close()
            os.remove(temp_path)

            new_kills_detected = False
            
            # Traiter uniquement les nouveaux kills
            for victim_name, killer_name, death_time, killer_confirmed in recent_kills:
                # Créer un identifiant unique pour ce kill
                kill_id = f"{killer_name}_{victim_name}_{death_time}"
                
                # Vérifier si ce kill a déjà été traité
                if kill_id not in self.processed_kills:
                    # Nouveau kill détecté
                    if self.update_kill_stats(killer_name, death_time):
                        self.processed_kills.add(kill_id)
                        new_kills_detected = True
                        logger.info(f"Nouveau kill détecté: {killer_name} a tué {victim_name}")
            
            # Nettoyer le cache des kills traités (garder seulement les 1000 derniers)
            if len(self.processed_kills) > 1000:
                # Convertir en liste, garder les 500 derniers
                kills_list = list(self.processed_kills)
                self.processed_kills = set(kills_list[-500:])
            
            return new_kills_detected

        except Exception as e:
            logger.error(f"Erreur lors de la vérification des kills: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def update_kill_stats(self, killer_name: str, kill_time: int):
        """Met à jour les statistiques de kills dans la base de données"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            # Normaliser le nom pour éviter les doublons (minuscules, espaces supprimés)
            norm_name = killer_name.strip().lower()
            original_name = killer_name.strip()  # Garder le nom original pour l'affichage
            
            # Vérifier si le joueur existe déjà
            c.execute('SELECT kills, last_kill FROM classement WHERE player_name = ?', (norm_name,))
            result = c.fetchone()
            
            if result:
                current_kills, last_kill = result
                # Vérifier si ce kill est plus récent que le dernier enregistré
                if last_kill is None or int(kill_time) > int(last_kill):
                    # Mise à jour : incrémenter kills et mettre à jour last_kill
                    c.execute('''
                        UPDATE classement 
                        SET kills = kills + 1, 
                            last_kill = ?, 
                            original_name = ?
                        WHERE player_name = ?
                    ''', (kill_time, original_name, norm_name))
                    conn.commit()
                    logger.info(f"Kill mis à jour pour {killer_name}: {current_kills + 1} kills")
                    return True
                else:
                    # Kill déjà comptabilisé ou plus ancien
                    return False
            else:
                # Nouveau joueur : insertion
                c.execute('''
                    INSERT INTO classement (player_name, original_name, kills, last_kill) 
                    VALUES (?, ?, ?, ?)
                ''', (norm_name, original_name, 1, kill_time))
                conn.commit()
                logger.info(f"Nouveau joueur ajouté: {killer_name} avec 1 kill")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_kill_stats(self):
        """Récupère les TOP 30 statistiques de kills triées par nombre de kills"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            # Récupérer les 30 meilleurs avec le nom original pour l'affichage
            c.execute('''
                SELECT original_name, kills
                FROM classement
                WHERE player_name IS NOT NULL 
                AND player_name != ''
                AND kills > 0
                ORDER BY kills DESC, original_name ASC
                LIMIT 30
            ''')
            stats = c.fetchall()
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return []
        finally:
            conn.close()

    def get_total_players_count(self):
        """Récupère le nombre total de joueurs dans le classement"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('SELECT COUNT(*) FROM classement WHERE kills > 0')
            count = c.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Erreur lors du comptage des joueurs: {e}")
            return 0
        finally:
            conn.close()

    def _load_db_from_bytes(self, db_data):
        """Crée un fichier temporaire avec les données de la base de données"""
        import tempfile
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(db_data)
        temp.close()
        return temp.name
