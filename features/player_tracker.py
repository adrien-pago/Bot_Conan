import logging
import asyncio
from datetime import datetime
from config.logging_config import setup_logging
from database.database_manager import DatabaseManager
import discord

logger = setup_logging()

class PlayerTracker:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.is_running = False
        self.last_player_count = 0
        
    async def start(self):
        """Démarre le suivi des joueurs"""
        self.is_running = True
        logger.info("PlayerTracker démarré")
        
    async def stop(self):
        """Arrête le suivi des joueurs"""
        self.is_running = False
        logger.info("PlayerTracker arrêté")
        
    async def update_channel_name(self):
        """Met à jour le nom du salon avec le nombre de joueurs"""
        try:
            # Récupérer le nombre de joueurs connectés
            online_players = await self.db.get_online_players()
            player_count = len(online_players)
            
            # Mettre à jour le nom du salon si le nombre a changé
            if player_count != self.last_player_count:
                channel = self.bot.get_channel(PLAYER_CHANNEL_ID)
                if channel:
                    await channel.edit(name=f"👥 Joueurs: {player_count}")
                    self.last_player_count = player_count
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du nom du salon: {e}")
            
    async def get_online_players(self):
        """Récupère la liste des joueurs connectés"""
        try:
            players = await self.db.get_online_players()
            return [{
                'name': player['char_name'],
                'level': player['level'],
                'clan': player['guild'] or "Sans clan"
            } for player in players]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs connectés: {e}")
            return []
            
    async def get_player_stats(self, player_name):
        """Récupère les statistiques d'un joueur"""
        try:
            stats = await self.db.get_player_stats(player_name)
            if stats:
                return {
                    'name': stats['char_name'],
                    'level': stats['level'],
                    'clan': stats['guild'] or "Sans clan",
                    'last_seen': stats['lastTimeOnline'],
                    'is_alive': stats['isAlive']
                }
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats du joueur {player_name}: {e}")
            return None
            
    async def update_player_status(self, player_data):
        """Met à jour le statut d'un joueur"""
        try:
            await self.db.update_player_status(player_data)
            
            # Vérifier si le joueur vient de se connecter
            if player_data.get('isOnline') and not player_data.get('wasOnline'):
                channel = self.bot.get_channel(PLAYER_CHANNEL_ID)
                if channel:
                    embed = discord.Embed(
                        title="👋 Nouveau joueur connecté",
                        description=f"{player_data['char_name']} vient de se connecter !",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Niveau", value=str(player_data['level']))
                    if player_data.get('guild'):
                        embed.add_field(name="Clan", value=player_data['guild'])
                    await channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut du joueur {player_data.get('char_name')}: {e}")
            
    async def check_player_activity(self):
        """Vérifie l'activité des joueurs"""
        try:
            players = await self.db.get_all_players()
            current_time = datetime.now()
            
            for player in players:
                last_seen = player['lastTimeOnline']
                if last_seen:
                    time_diff = current_time - last_seen
                    
                    # Si le joueur est inactif depuis plus de 24h
                    if time_diff.days >= 1:
                        await self._handle_inactive_player(player)
                        
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'activité des joueurs: {e}")
            
    async def _handle_inactive_player(self, player):
        """Gère un joueur inactif"""
        try:
            # Marquer le joueur comme inactif dans la base de données
            await self.db.mark_player_inactive(player['id'])
            
            # Notifier le canal Discord
            channel = self.bot.get_channel(PLAYER_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="⏰ Joueur inactif",
                    description=f"{player['char_name']} n'a pas été vu depuis plus de 24h",
                    color=discord.Color.orange()
                )
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du joueur inactif {player['char_name']}: {e}") 