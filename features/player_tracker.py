import logging
import asyncio
import discord
import sys
import os
import datetime

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.rcon_client import RCONClient

logger = logging.getLogger(__name__)

class PlayerTracker:
    def __init__(self, bot, channel_id, rcon_client):
        self.bot = bot
        self.channel_id = channel_id
        self.rcon_client = rcon_client
        self.is_running = False
        self.update_task = None
        self.last_player_count = 0  # Garder en mémoire le dernier nombre de joueurs

    async def start(self):
        """Démarre le suivi des joueurs"""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_task = self.bot.loop.create_task(self._update_loop())
        logger.info("PlayerTracker démarré")

    async def stop(self):
        """Arrête le suivi des joueurs"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        logger.info("PlayerTracker arrêté")

    async def _update_loop(self):
        """Boucle de mise à jour du nom du salon"""
        while self.is_running:
            try:
                await self._update_channel_name()
                # Mise à jour toutes les 8 minutes au lieu de 1 minute pour éviter le spam RCON
                await asyncio.sleep(480)  # 8 minutes = 480 secondes
            except Exception as e:
                logger.error(f"Erreur dans la boucle de mise à jour : {e}")
                # En cas d'erreur, attendre 2 minutes avant de réessayer
                await asyncio.sleep(120)

    async def _update_channel_name(self):
        """Met à jour le nom du salon avec le nombre de joueurs"""
        try:
            # Récupérer la liste des joueurs en ligne via RCON
            online = self.rcon_client.get_online_players()
            count = len(online)
            
            # Ne mettre à jour que si le nombre de joueurs a changé
            if count != self.last_player_count:
                self.last_player_count = count
                
                # Vérifier si c'est le raid time
                now = datetime.datetime.now()
                is_raid_time = (
                    now.weekday() in [2, 5, 6] and  # Mercredi (2), Samedi (5), Dimanche (6)
                    19 <= now.hour < 22  # Entre 19h et 22h
                )
                
                # Renommer le salon
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    try:
                        if is_raid_time:
                            await channel.edit(name=f"🟢【{count}︱40】Raid On")
                        else:
                            await channel.edit(name=f"🟢【{count}︱40】Raid Off")
                        logger.info(f"Nom du salon mis à jour: {count} joueurs connectés")
                    except discord.errors.HTTPException as e:
                        if e.status == 429:  # Rate limit Discord
                            retry_after = e.retry_after
                            logger.warning(f"Rate limit Discord atteint. Nouvelle tentative dans {retry_after} secondes")
                            await asyncio.sleep(retry_after)
                            await self._update_channel_name()
                        else:
                            logger.error(f"Erreur Discord lors de la mise à jour du nom: {e}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la mise à jour du nom du salon: {e}")
            else:
                logger.debug(f"Nombre de joueurs inchangé ({count}), pas de mise à jour du salon")
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du nom du salon : {e}")

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    