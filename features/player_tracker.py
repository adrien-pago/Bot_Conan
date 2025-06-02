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

    async def start(self):
        """Démarre le suivi des joueurs"""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_task = self.bot.loop.create_task(self._update_loop())

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

    async def _update_loop(self):
        """Boucle de mise à jour du nom du salon"""
        while self.is_running:
            try:
                await self._update_channel_name()
                await asyncio.sleep(60)  # Mise à jour toutes les minutes
            except Exception as e:
                print(f"Erreur dans la boucle de mise à jour : {e}")
                await asyncio.sleep(60)  # Attendre avant de réessayer

    async def _update_channel_name(self):
        """Met à jour le nom du salon avec le nombre de joueurs"""
        try:
            # Récupérer la liste des joueurs en ligne via RCON
            online = self.rcon_client.get_online_players()
            count = len(online)
            
            # Vérifier si c'est le raid time
            now = datetime.datetime.now()
            is_raid_time = (
                now.weekday() in [2, 5, 6] and  # Mercredi (2), Samedi (5), Dimanche (6)
                19 <= now.hour < 22  # Entre 19h et 22h
            )
            
            # Renommer le salon
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                if is_raid_time:
                    await channel.edit(name=f"🟢【{count}︱40】Raid On")
                else:
                    await channel.edit(name=f"🟢【{count}︱40】Raid Off")
        except discord.errors.HTTPException as e:
            if e.status == 429:  # Rate limit
                retry_after = e.retry_after
                print(f"Rate limit atteint. Nouvelle tentative dans {retry_after} secondes")
                await asyncio.sleep(retry_after)
                await self._update_channel_name()
            else:
                print(f"Erreur Discord : {e}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du nom du salon : {e}")

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    