import logging
import asyncio
import discord
import sys
import os

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
        self.check_interval = 60
        self.channel = None

    async def start(self):
        if not self.bot.is_ready():
            await asyncio.sleep(5)
            if not self.bot.is_ready():
                return False

        logger.info(f"Récupération du canal {self.channel_id}")
        self.channel = self.bot.get_channel(self.channel_id)
        if not self.channel:
            logger.error(f"Canal {self.channel_id} non trouvé")
            return False

        logger.info(f"Canal trouvé : {self.channel.name}")
        self.is_running = True
        
        while self.is_running:
            try:
                await self.check_players()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Erreur: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        self.is_running = False

    async def check_players(self):
        try:
            # Récupérer la liste des joueurs
            players = await self.rcon_client.get_player_list()
            print(f"DEBUG - Type renvoyé par get_player_list() : {type(players)}")
            print(f"DEBUG - Liste des joueurs reçue : {players}")

            # Calculer le nombre de joueurs
            player_count = len(players)
            print(f"DEBUG - Nombre de joueurs calculé : {player_count}")

            # Mettre à jour le nom du canal
            if self.channel:
                new_name = f"🟢【{player_count}︱40】raid-on"
                print(f"DEBUG - Nouveau nom du canal : {new_name}")
                await self.channel.edit(name=new_name)
                
        except Exception as e:
            print(f"DEBUG - Erreur dans check_players() : {e}")

if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test simple de la classe
    async def test_tracker():
        try:
            # Créer une instance de RCONClient avec des valeurs de test
            rcon_client = RCONClient(
                host="localhost",
                port=28316,
                password="test_password"
            )
            
            # Créer une instance de test du tracker
            tracker = PlayerTracker(None, 123456789, rcon_client)
            logger.info("Test du tracker de joueurs")
            
            # Tester les méthodes de base
            await tracker.start()
            await asyncio.sleep(5)  # Attendre 5 secondes
            await tracker.stop()
            
        except Exception as e:
            logger.error(f"Erreur lors du test: {e}")
    
    # Exécuter le test
    asyncio.run(test_tracker()) 