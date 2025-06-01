import logging
import asyncio
import aiohttp
import json
from config.logging_config import setup_logging
from config.settings import *

logger = setup_logging()

class RCONClient:
    def __init__(self):
        self.host = RCON_HOST
        self.port = RCON_PORT
        self.password = RCON_PASSWORD
        self.session = None
        self.is_connected = False
        
    async def connect(self):
        """Établit une connexion RCON"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            # Tester la connexion avec une commande simple
            response = await self.send_command("version")
            if response:
                self.is_connected = True
                logger.info("Connexion RCON établie avec succès")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion RCON: {e}")
            return False
            
    async def disconnect(self):
        """Ferme la connexion RCON"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            self.is_connected = False
            logger.info("Connexion RCON fermée")
            
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la connexion RCON: {e}")
            
    async def send_command(self, command):
        """Envoie une commande RCON"""
        try:
            if not self.is_connected:
                if not await self.connect():
                    return None
                    
            url = f"http://{self.host}:{self.port}/rcon"
            data = {
                "command": command,
                "password": self.password
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.text()
                    return result
                else:
                    logger.error(f"Erreur RCON (status {response.status}): {await response.text()}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la commande RCON: {e}")
            return None
            
    async def get_player_list(self):
        """Récupère la liste des joueurs connectés"""
        try:
            response = await self.send_command("listplayers")
            if response:
                # Parser la réponse pour extraire la liste des joueurs
                players = []
                for line in response.split('\n'):
                    if line.strip():
                        # Format: "ID: X, Name: Y, SteamID: Z"
                        parts = line.split(',')
                        player = {}
                        for part in parts:
                            key, value = part.split(':')
                            player[key.strip()] = value.strip()
                        players.append(player)
                return players
            return []
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des joueurs: {e}")
            return []
            
    async def get_server_info(self):
        """Récupère les informations du serveur"""
        try:
            response = await self.send_command("serverinfo")
            if response:
                # Parser la réponse pour extraire les informations
                info = {}
                for line in response.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                return info
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des informations du serveur: {e}")
            return None
            
    async def broadcast_message(self, message):
        """Envoie un message à tous les joueurs"""
        try:
            command = f'broadcast "{message}"'
            response = await self.send_command(command)
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message broadcast: {e}")
            return False
            
    async def kick_player(self, player_id, reason=""):
        """Expulse un joueur du serveur"""
        try:
            command = f'kick {player_id}'
            if reason:
                command += f' "{reason}"'
            response = await self.send_command(command)
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'expulsion du joueur {player_id}: {e}")
            return False
            
    async def ban_player(self, player_id, duration=0, reason=""):
        """Bannit un joueur du serveur"""
        try:
            command = f'ban {player_id}'
            if duration > 0:
                command += f' {duration}'
            if reason:
                command += f' "{reason}"'
            response = await self.send_command(command)
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors du bannissement du joueur {player_id}: {e}")
            return False
            
    async def teleport_player(self, player_id, x, y, z):
        """Téléporte un joueur à des coordonnées spécifiques"""
        try:
            command = f'teleport {player_id} {x} {y} {z}'
            response = await self.send_command(command)
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors de la téléportation du joueur {player_id}: {e}")
            return False
            
    async def give_item(self, player_id, item_name, amount=1):
        """Donne un objet à un joueur"""
        try:
            command = f'give {player_id} {item_name} {amount}'
            response = await self.send_command(command)
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'attribution d'objet au joueur {player_id}: {e}")
            return False
            
    async def save_world(self):
        """Sauvegarde le monde"""
        try:
            response = await self.send_command("saveworld")
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du monde: {e}")
            return False
            
    async def shutdown_server(self, message="", delay=0):
        """Arrête le serveur"""
        try:
            command = "shutdown"
            if delay > 0:
                command += f" {delay}"
            if message:
                command += f' "{message}"'
            response = await self.send_command(command)
            return response is not None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du serveur: {e}")
            return False 