import logging
import asyncio
from datetime import datetime, timedelta
from config.logging_config import setup_logging
from database.database_manager import DatabaseManager

logger = setup_logging()

class BuildTracker:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.active_builds = {}
        self.is_running = False
        
    async def start(self):
        """Démarre le suivi des constructions"""
        self.is_running = True
        logger.info("BuildTracker démarré")
        
    async def stop(self):
        """Arrête le suivi des constructions"""
        self.is_running = False
        logger.info("BuildTracker arrêté")
        
    async def check_builds(self):
        """Vérifie l'état des constructions en cours"""
        try:
            # Récupérer les constructions actives depuis la base de données
            builds = await self.db.get_active_builds()
            
            for build in builds:
                build_id = build['id']
                current_time = datetime.now()
                
                # Vérifier si la construction est terminée
                if current_time >= build['end_time']:
                    await self._complete_build(build)
                else:
                    # Mettre à jour la progression
                    progress = self._calculate_progress(build)
                    await self._update_build_progress(build_id, progress)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des constructions: {e}")
            
    async def _complete_build(self, build):
        """Marque une construction comme terminée"""
        try:
            await self.db.complete_build(build['id'])
            
            # Notifier le canal Discord
            channel = self.bot.get_channel(BUILD_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🏗️ Construction terminée",
                    description=f"La construction de {build['name']} est terminée !",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation de la construction {build['id']}: {e}")
            
    def _calculate_progress(self, build):
        """Calcule la progression d'une construction"""
        total_duration = (build['end_time'] - build['start_time']).total_seconds()
        elapsed = (datetime.now() - build['start_time']).total_seconds()
        return min(100, int((elapsed / total_duration) * 100))
        
    async def _update_build_progress(self, build_id, progress):
        """Met à jour la progression d'une construction"""
        try:
            await self.db.update_build_progress(build_id, progress)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la progression de la construction {build_id}: {e}")
            
    async def get_active_builds(self):
        """Récupère la liste des constructions actives"""
        try:
            builds = await self.db.get_active_builds()
            return [{
                'name': build['name'],
                'progress': build['progress'],
                'time_left': str(build['end_time'] - datetime.now()).split('.')[0]
            } for build in builds]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des constructions actives: {e}")
            return []
            
    async def add_build(self, name, duration_hours):
        """Ajoute une nouvelle construction"""
        try:
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=duration_hours)
            
            build_id = await self.db.add_build(name, start_time, end_time)
            
            # Notifier le canal Discord
            channel = self.bot.get_channel(BUILD_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🏗️ Nouvelle construction",
                    description=f"La construction de {name} a commencé !",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Durée estimée", value=f"{duration_hours} heures")
                await channel.send(embed=embed)
                
            return build_id
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'une construction: {e}")
            return None 