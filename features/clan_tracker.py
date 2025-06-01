import logging
import asyncio
from datetime import datetime
from config.logging_config import setup_logging
from database.database_manager import DatabaseManager

logger = setup_logging()

class ClanTracker:
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager()
        self.is_running = False
        
    async def start(self):
        """Démarre le suivi des clans"""
        self.is_running = True
        logger.info("ClanTracker démarré")
        
    async def stop(self):
        """Arrête le suivi des clans"""
        self.is_running = False
        logger.info("ClanTracker arrêté")
        
    async def get_clan_stats(self):
        """Récupère les statistiques des clans"""
        try:
            clans = await self.db.get_clan_stats()
            return [{
                'name': clan['name'],
                'kills': clan['total_kills'],
                'deaths': clan['total_deaths'],
                'members': clan['member_count']
            } for clan in clans]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats des clans: {e}")
            return []
            
    async def update_clan_stats(self, clan_data):
        """Met à jour les statistiques d'un clan"""
        try:
            await self.db.update_clan_stats(clan_data)
            
            # Vérifier si le clan a atteint un nouveau record
            if clan_data.get('new_record'):
                channel = self.bot.get_channel(CLAN_CHANNEL_ID)
                if channel:
                    embed = discord.Embed(
                        title="🏆 Nouveau record de clan",
                        description=f"Le clan {clan_data['name']} a atteint un nouveau record !",
                        color=discord.Color.gold()
                    )
                    embed.add_field(name="Kills", value=str(clan_data['total_kills']))
                    embed.add_field(name="Membres", value=str(clan_data['member_count']))
                    await channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats du clan {clan_data.get('name')}: {e}")
            
    async def get_clan_members(self, clan_name):
        """Récupère la liste des membres d'un clan"""
        try:
            members = await self.db.get_clan_members(clan_name)
            return [{
                'name': member['char_name'],
                'level': member['level'],
                'last_seen': member['lastTimeOnline']
            } for member in members]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des membres du clan {clan_name}: {e}")
            return []
            
    async def check_clan_activity(self):
        """Vérifie l'activité des clans"""
        try:
            clans = await self.db.get_all_clans()
            current_time = datetime.now()
            
            for clan in clans:
                # Vérifier si le clan est inactif
                if not await self._is_clan_active(clan['name']):
                    await self._handle_inactive_clan(clan)
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'activité des clans: {e}")
            
    async def _is_clan_active(self, clan_name):
        """Vérifie si un clan est actif"""
        try:
            members = await self.db.get_clan_members(clan_name)
            current_time = datetime.now()
            
            for member in members:
                last_seen = member['lastTimeOnline']
                if last_seen:
                    time_diff = current_time - last_seen
                    # Si au moins un membre a été actif dans les dernières 24h
                    if time_diff.days < 1:
                        return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'activité du clan {clan_name}: {e}")
            return False
            
    async def _handle_inactive_clan(self, clan):
        """Gère un clan inactif"""
        try:
            # Marquer le clan comme inactif dans la base de données
            await self.db.mark_clan_inactive(clan['id'])
            
            # Notifier le canal Discord
            channel = self.bot.get_channel(CLAN_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="⏰ Clan inactif",
                    description=f"Le clan {clan['name']} n'a pas eu d'activité depuis plus de 24h",
                    color=discord.Color.orange()
                )
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du clan inactif {clan['name']}: {e}")
            
    async def get_clan_ranking(self):
        """Récupère le classement des clans"""
        try:
            clans = await self.db.get_clan_ranking()
            return [{
                'rank': idx + 1,
                'name': clan['name'],
                'kills': clan['total_kills'],
                'members': clan['member_count']
            } for idx, clan in enumerate(clans)]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du classement des clans: {e}")
            return [] 