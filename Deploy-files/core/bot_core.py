import discord
from discord.ext import commands, tasks
import asyncio
import logging
from config.settings import *
from config.logging_config import setup_logging

logger = setup_logging()

class ConanBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialiser les trackers
        self.kill_tracker = None
        self.build_tracker = None
        self.player_tracker = None
        self.clan_tracker = None
        
        # État du bot
        self.is_ready = False
        
    async def setup_hook(self):
        """Initialise les trackers et les tâches planifiées"""
        from features.kill_tracker import KillTracker
        from features.build_tracker import BuildTracker
        from features.player_tracker import PlayerTracker
        from features.clan_tracker import ClanTracker
        
        # Initialiser les trackers
        self.kill_tracker = KillTracker(self)
        self.build_tracker = BuildTracker(self)
        self.player_tracker = PlayerTracker(self)
        self.clan_tracker = ClanTracker(self)
        
        # Démarrer les tâches planifiées
        self.update_channel_name.start()
        self.check_builds.start()
        
    async def on_ready(self):
        """Événement déclenché quand le bot est prêt"""
        try:
            logger.info(f"Bot connecté en tant que {self.user.name}")
            logger.info(f"ID du bot: {self.user.id}")
            logger.info(f"Nombre de guildes: {len(self.guilds)}")
            
            # Démarrer les trackers
            await self.kill_tracker.start()
            await self.build_tracker.start()
            await self.player_tracker.start()
            await self.clan_tracker.start()
            
            self.is_ready = True
            logger.info("Bot prêt et toutes les tâches démarrées")
            
        except Exception as e:
            logger.error(f"Erreur dans l'événement on_ready: {e}")
            raise
            
    @tasks.loop(minutes=UPDATE_CHANNEL_INTERVAL)
    async def update_channel_name(self):
        """Met à jour le nom du salon avec le nombre de joueurs"""
        try:
            await self.player_tracker.update_channel_name()
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du nom du salon: {e}")
            
    @tasks.loop(minutes=BUILD_CHECK_INTERVAL)
    async def check_builds(self):
        """Vérifie les constructions"""
        try:
            await self.build_tracker.check_builds()
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des constructions: {e}")
            
    async def on_error(self, event, *args, **kwargs):
        """Gestion des erreurs"""
        logger.error(f"Erreur dans l'événement {event}: {str(args)}")
        
    async def on_disconnect(self):
        """Gestion de la déconnexion"""
        logger.warning("Bot déconnecté de Discord")
        
    async def on_connect(self):
        """Gestion de la connexion"""
        logger.info("Bot connecté à Discord")
        
    async def close(self):
        """Arrêt propre du bot"""
        try:
            # Arrêter les trackers
            if self.kill_tracker:
                await self.kill_tracker.stop()
            if self.build_tracker:
                await self.build_tracker.stop()
            if self.player_tracker:
                await self.player_tracker.stop()
            if self.clan_tracker:
                await self.clan_tracker.stop()
                
            # Arrêter les tâches planifiées
            self.update_channel_name.cancel()
            self.check_builds.cancel()
            
            await super().close()
            logger.info("Bot arrêté proprement")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du bot: {e}")
            raise 