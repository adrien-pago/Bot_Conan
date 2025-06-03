import sqlite3
import logging
from config.logging_config import setup_logging

logger = setup_logging()

class DatabaseSync:
    def __init__(self):
        """Initialise la connexion à la base de données de synchronisation"""
        self.db_path = 'discord.db'
        self._initialize_db()

    def _initialize_db(self):
        """Initialise la table users si elle n'existe pas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            # Créer la table si elle n'existe pas
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_name TEXT NOT NULL,
                    discord_id TEXT NOT NULL UNIQUE,
                    player_name TEXT,
                    player_id TEXT,
                    wallet INTEGER DEFAULT 0,
                    RP INTEGER DEFAULT 0,
                    date_end_rp TIMESTAMP,
                    verification_code TEXT,
                    verification_timestamp TIMESTAMP,
                    verified BOOLEAN DEFAULT 0,
                    starter_pack BOOLEAN DEFAULT 0,
                    steam_id TEXT,
                    UNIQUE(discord_id, player_id)
                )
            ''')

            # Vérifier si la colonne verified existe
            c.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in c.fetchall()]
            
            # Ajouter la colonne verified si elle n'existe pas
            if 'verified' not in columns:
                c.execute('ALTER TABLE users ADD COLUMN verified BOOLEAN DEFAULT 0')
                logger.info("Colonne 'verified' ajoutée à la table users")
                
            # Ajouter la colonne starter_pack si elle n'existe pas
            if 'starter_pack' not in columns:
                c.execute('ALTER TABLE users ADD COLUMN starter_pack BOOLEAN DEFAULT 0')
                logger.info("Colonne 'starter_pack' ajoutée à la table users")
                
            # Ajouter la colonne steam_id si elle n'existe pas
            if 'steam_id' not in columns:
                c.execute('ALTER TABLE users ADD COLUMN steam_id TEXT')
                logger.info("Colonne 'steam_id' ajoutée à la table users")

            conn.commit()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_verification(self, discord_id: str, discord_name: str, verification_code: str):
        """Crée une nouvelle tentative de vérification"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO users (discord_id, discord_name, verification_code, verification_timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(discord_id) DO UPDATE SET
                    discord_name = excluded.discord_name,
                    verification_code = excluded.verification_code,
                    verification_timestamp = CURRENT_TIMESTAMP
            ''', (discord_id, discord_name, verification_code))
            conn.commit()
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vérification: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def verify_player(self, discord_id: str, player_name: str, player_id: str, steam_id: str = None):
        """Vérifie et met à jour les informations du joueur"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                UPDATE users 
                SET player_name = ?,
                    player_id = ?,
                    steam_id = ?,
                    verification_code = NULL,
                    verification_timestamp = NULL,
                    verified = 1,
                    wallet = 200
                WHERE discord_id = ?
                AND verification_code IS NOT NULL
            ''', (player_name, player_id, steam_id, discord_id))
            conn.commit()
            return c.rowcount > 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du joueur: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_verification_code(self, discord_id: str):
        """Récupère le code de vérification pour un utilisateur Discord"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT verification_code, verification_timestamp
                FROM users
                WHERE discord_id = ?
            ''', (discord_id,))
            return c.fetchone()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du code de vérification: {e}")
            raise
        finally:
            conn.close()

    def get_player_info(self, discord_id: str):
        """Récupère les informations d'un joueur"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT discord_name, player_name, player_id, wallet, RP, date_end_rp, steam_id
                FROM users
                WHERE discord_id = ?
            ''', (discord_id,))
            return c.fetchone()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du joueur: {e}")
            raise
        finally:
            conn.close()

    def update_player_stats(self, discord_id: str, wallet: int = None, rp: int = None, date_end_rp: str = None):
        """Met à jour les statistiques d'un joueur"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            updates = []
            params = []
            if wallet is not None:
                updates.append("wallet = ?")
                params.append(wallet)
            if rp is not None:
                updates.append("RP = ?")
                params.append(rp)
            if date_end_rp is not None:
                updates.append("date_end_rp = ?")
                params.append(date_end_rp)
            
            if updates:
                query = f'''
                    UPDATE users 
                    SET {', '.join(updates)}
                    WHERE discord_id = ?
                '''
                params.append(discord_id)
                c.execute(query, params)
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats du joueur: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_pending_verifications(self):
        """Récupère toutes les vérifications en attente"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                SELECT discord_id, verification_code
                FROM users
                WHERE verification_code IS NOT NULL
                AND verification_timestamp > datetime('now', '-5 minutes')
            ''')
            return c.fetchall()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vérifications en attente: {e}")
            raise
        finally:
            conn.close()

    def has_received_starterpack(self, discord_id: str):
        """Vérifie si un joueur a déjà reçu son starterpack"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('SELECT starter_pack FROM users WHERE discord_id = ?', (discord_id,))
            result = c.fetchone()
            return bool(result and result[0])
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du starterpack: {e}")
            return False
        finally:
            conn.close()

    def set_starterpack_received(self, discord_id: str):
        """Marque le starterpack comme reçu pour un joueur"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('UPDATE users SET starter_pack = 1 WHERE discord_id = ?', (discord_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut du starterpack: {e}")
            conn.rollback()
            return False
        finally:
            conn.close() 