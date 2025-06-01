import logging
import asyncio
from datetime import datetime
from config.logging_config import setup_logging
from database.database_manager import DatabaseManager
import discord

logger = setup_logging()

class KillTracker:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.is_running = False
        
    async def start(self):
        """Démarre le suivi des kills"""
        self.is_running = True
        logger.info("KillTracker démarré")
        
    async def stop(self):
        """Arrête le suivi des kills"""
        self.is_running = False
        logger.info("KillTracker arrêté")
        
    async def get_stats(self):
        """Récupère les statistiques de kills"""
        try:
            stats = await self.db.get_kill_stats()
            return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats de kills: {e}")
            return {}
            
    async def update_kill_stats(self, killer_name, victim_name):
        """Met à jour les statistiques de kills"""
        try:
            # Vérifier si le tueur existe dans la liste des joueurs
            all_players = await self.db.get_all_players()
            killer_exists = any(p['char_name'] == killer_name for p in all_players)
            
            if not killer_exists:
                logger.info(f"Le kill de {killer_name} sur {victim_name} n'est pas comptabilisé car {killer_name} n'est pas un joueur valide")
                return
                
            # Mettre à jour les stats
            await self.db.update_kill_stats(killer_name, victim_name)
            
            # Notifier le canal Discord
            channel = self.bot.get_channel(KILLS_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="💀 Nouveau Kill",
                    description=f"{killer_name} a tué {victim_name} !",
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats de kills: {e}")
            
    async def check_kills(self):
        """Vérifie les nouveaux kills"""
        try:
            # Récupérer les joueurs morts depuis la dernière vérification
            dead_players = await self.db.get_recent_deaths()
            
            for player in dead_players:
                if player.get('killerName'):
                    await self.update_kill_stats(
                        player['killerName'],
                        player['char_name']
                    )
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des kills: {e}")
            
    async def get_player_kills(self, player_name):
        """Récupère les kills d'un joueur"""
        try:
            kills = await self.db.get_player_kills(player_name)
            return kills
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des kills du joueur {player_name}: {e}")
            return []
            
    async def get_player_deaths(self, player_name):
        """Récupère les morts d'un joueur"""
        try:
            deaths = await self.db.get_player_deaths(player_name)
            return deaths
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des morts du joueur {player_name}: {e}")
            return [] 