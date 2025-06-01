import logging
import sqlite3
import aiosqlite
from datetime import datetime
from config.logging_config import setup_logging
from config.settings import *

logger = setup_logging()

class DatabaseManager:
    def __init__(self):
        self.db_path = "discord.db"
        self.ftp_handler = None
        
    async def init_db(self):
        """Initialise la base de données"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Table des joueurs
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS players (
                        id INTEGER PRIMARY KEY,
                        char_name TEXT UNIQUE,
                        level INTEGER,
                        guild TEXT,
                        isAlive BOOLEAN,
                        killerName TEXT,
                        lastTimeOnline TIMESTAMP,
                        killerId INTEGER,
                        lastServerTimeOnline TIMESTAMP
                    )
                ''')
                
                # Table des kills
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS kills (
                        id INTEGER PRIMARY KEY,
                        killer_id INTEGER,
                        victim_id INTEGER,
                        timestamp TIMESTAMP,
                        FOREIGN KEY (killer_id) REFERENCES players (id),
                        FOREIGN KEY (victim_id) REFERENCES players (id)
                    )
                ''')
                
                # Table des constructions
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS builds (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        progress INTEGER,
                        is_completed BOOLEAN
                    )
                ''')
                
                # Table des clans
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS clans (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE,
                        total_kills INTEGER DEFAULT 0,
                        total_deaths INTEGER DEFAULT 0,
                        member_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_activity TIMESTAMP
                    )
                ''')
                
                await db.commit()
                logger.info("Base de données initialisée avec succès")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
            
    async def get_player_stats(self, player_name):
        """Récupère les statistiques d'un joueur"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute(
                    "SELECT * FROM players WHERE char_name = ?",
                    (player_name,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats du joueur {player_name}: {e}")
            return None
            
    async def update_player_status(self, player_data):
        """Met à jour le statut d'un joueur"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO players (
                        id, char_name, level, guild, isAlive,
                        killerName, lastTimeOnline, killerId,
                        lastServerTimeOnline
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    player_data['id'],
                    player_data['char_name'],
                    player_data['level'],
                    player_data.get('guild'),
                    player_data['isAlive'],
                    player_data.get('killerName'),
                    player_data['lastTimeOnline'],
                    player_data.get('killerId'),
                    player_data['lastServerTimeOnline']
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut du joueur: {e}")
            raise
            
    async def get_online_players(self):
        """Récupère la liste des joueurs connectés"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute(
                    "SELECT * FROM players WHERE isAlive = 1"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs connectés: {e}")
            return []
            
    async def get_all_players(self):
        """Récupère tous les joueurs"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute("SELECT * FROM players") as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de tous les joueurs: {e}")
            return []
            
    async def mark_player_inactive(self, player_id):
        """Marque un joueur comme inactif"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE players SET isAlive = 0 WHERE id = ?",
                    (player_id,)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors du marquage du joueur {player_id} comme inactif: {e}")
            raise
            
    async def get_active_builds(self):
        """Récupère les constructions actives"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute(
                    "SELECT * FROM builds WHERE is_completed = 0"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des constructions actives: {e}")
            return []
            
    async def add_build(self, name, start_time, end_time):
        """Ajoute une nouvelle construction"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO builds (name, start_time, end_time, progress, is_completed)
                    VALUES (?, ?, ?, 0, 0)
                ''', (name, start_time, end_time))
                await db.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'une construction: {e}")
            raise
            
    async def update_build_progress(self, build_id, progress):
        """Met à jour la progression d'une construction"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE builds SET progress = ? WHERE id = ?",
                    (progress, build_id)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la progression de la construction {build_id}: {e}")
            raise
            
    async def complete_build(self, build_id):
        """Marque une construction comme terminée"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE builds SET is_completed = 1, progress = 100 WHERE id = ?",
                    (build_id,)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation de la construction {build_id}: {e}")
            raise
            
    async def get_clan_stats(self):
        """Récupère les statistiques des clans"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute(
                    "SELECT * FROM clans WHERE is_active = 1"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats des clans: {e}")
            return []
            
    async def update_clan_stats(self, clan_data):
        """Met à jour les statistiques d'un clan"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO clans (
                        name, total_kills, total_deaths,
                        member_count, last_activity
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    clan_data['name'],
                    clan_data['total_kills'],
                    clan_data['total_deaths'],
                    clan_data['member_count'],
                    datetime.now()
                ))
                await db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats du clan {clan_data.get('name')}: {e}")
            raise
            
    async def get_clan_members(self, clan_name):
        """Récupère les membres d'un clan"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute(
                    "SELECT * FROM players WHERE guild = ?",
                    (clan_name,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des membres du clan {clan_name}: {e}")
            return []
            
    async def get_all_clans(self):
        """Récupère tous les clans"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute("SELECT * FROM clans") as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de tous les clans: {e}")
            return []
            
    async def mark_clan_inactive(self, clan_id):
        """Marque un clan comme inactif"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE clans SET is_active = 0 WHERE id = ?",
                    (clan_id,)
                )
                await db.commit()
                
        except Exception as e:
            logger.error(f"Erreur lors du marquage du clan {clan_id} comme inactif: {e}")
            raise
            
    async def get_clan_ranking(self):
        """Récupère le classement des clans"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                async with db.execute('''
                    SELECT * FROM clans
                    WHERE is_active = 1
                    ORDER BY total_kills DESC
                ''') as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du classement des clans: {e}")
            return [] 