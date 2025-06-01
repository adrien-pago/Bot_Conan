import logging
import asyncio
import socket
import struct
import json
from config.logging_config import setup_logging
from config.settings import *
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RCONClient:
    def __init__(self, host: str, port: int, password: str):
        """Initialise le client RCON"""
        self.host = host
        self.port = port
        self.password = password
        self.connected = False
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 5  # secondes
        self.reader = None
        self.writer = None
        logger.info(f"Client RCON initialisé pour {host}:{port}")
        
    async def connect(self):
        """Établit la connexion RCON"""
        try:
            if self.connected:
                logger.info("Déjà connecté au serveur RCON")
                return True

            logger.info(f"Tentative de connexion à {self.host}:{self.port}")
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            logger.info("Connexion TCP établie")
            
            # Envoyer le paquet d'authentification
            logger.info("Envoi du paquet d'authentification...")
            await self._send_packet(3, self.password)
            logger.info("Paquet d'authentification envoyé")
            
            # Lire la réponse
            logger.info("Attente de la réponse d'authentification...")
            response = await self._read_packet()
            if response:
                logger.info(f"Réponse reçue: ID={response['id']}, Type={response['type']}, Payload={response['payload']}")
                if response['payload'] == "Authenticated.":
                    self.connected = True
                    self.retry_count = 0
                    logger.info("Connexion RCON établie avec succès")
                    return True
                else:
                    logger.error(f"Échec de l'authentification: {response['payload']}")
            else:
                logger.error("Pas de réponse du serveur")
                
            await self.disconnect()
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion RCON: {e}")
            await self.disconnect()
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                logger.info(f"Tentative de reconnexion {self.retry_count}/{self.max_retries} dans {self.retry_delay} secondes...")
                await asyncio.sleep(self.retry_delay)
                return await self.connect()
            else:
                logger.error("Nombre maximum de tentatives de connexion atteint")
                return False
            
    async def disconnect(self):
        """Ferme la connexion RCON"""
        if self.writer:
            logger.info("Fermeture de la connexion RCON")
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None
        self.connected = False
        
    async def _send_packet(self, packet_type: int, payload: str):
        if not self.writer:
            raise ConnectionError("Non connecté au serveur RCON")

        # Construire le paquet RCON
        payload_bytes = payload.encode('utf-8')
        packet_size = len(payload_bytes) + 10  # 10 = taille de l'en-tête (4 + 4 + 2)
        
        # Format du paquet: [taille totale][ID][type][payload][\0\0]
        packet = struct.pack('<ii', packet_size, 0)  # ID de requête = 0
        packet += struct.pack('<i', packet_type)
        packet += payload_bytes
        packet += b'\x00\x00'

        # Envoyer le paquet
        logger.debug(f"Envoi du paquet: Type={packet_type}, Taille={packet_size}, Payload={payload}")
        self.writer.write(packet)
        await self.writer.drain()

    async def _read_packet(self):
        if not self.reader:
            raise ConnectionError("Non connecté au serveur RCON")

        try:
            # Lire la taille du paquet
            size_data = await self.reader.read(4)
            if not size_data:
                logger.error("Fin de la connexion lors de la lecture de la taille")
                return None
                
            size = struct.unpack('<i', size_data)[0]
            logger.debug(f"Taille du paquet reçu: {size}")

            # Lire le reste du paquet
            packet_data = await self.reader.read(size)
            if not packet_data:
                logger.error("Fin de la connexion lors de la lecture du paquet")
                return None

            # Décoder le paquet
            request_id = struct.unpack('<i', packet_data[:4])[0]
            packet_type = struct.unpack('<i', packet_data[4:8])[0]
            payload = packet_data[8:-2].decode('utf-8')  # -2 pour enlever les deux octets nuls de fin

            logger.debug(f"Paquet reçu: ID={request_id}, Type={packet_type}, Payload={payload}")
            return {
                'id': request_id,
                'type': packet_type,
                'payload': payload
            }
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du paquet RCON: {e}")
            return None

    async def send_command(self, command: str):
        """Envoie une commande RCON"""
        if not self.connected:
            logger.info("Non connecté, tentative de connexion...")
            if not await self.connect():
                return None

        try:
            logger.info(f"Envoi de la commande: {command}")
            await self._send_packet(2, command)  # Type 2 = commande
            
            # Lire toutes les réponses jusqu'à ce qu'on reçoive une réponse vide
            full_response = []
            while True:
                response = await self._read_packet()
                if not response:
                    break
                    
                logger.info(f"Réponse reçue: Type={response['type']}, Payload={response['payload']}")
                
                # Type 0 = réponse normale, Type 2 = réponse de commande
                if response['type'] in [0, 2]:
                    if response['payload']:
                        full_response.append(response['payload'])
                    if not response['payload']:  # Réponse vide = fin de la réponse
                        break
                else:
                    logger.error(f"Type de réponse inattendu: {response['type']}")
                    break
            
            if full_response:
                return '\n'.join(full_response)
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la commande RCON: {e}")
            self.connected = False
            return None
            
    async def get_player_list(self):
        """Récupère la liste des joueurs connectés"""
        try:
            response = await self.send_command("listplayers")
            if not response:
                return []

            # On récupère toutes les lignes qui contiennent "|"
            lines = [line for line in response.split('\n') if '|' in line]
            # On ignore la première ligne (en-tête)
            if len(lines) > 1:
                return lines[1:]  # Retourne la liste des joueurs
            return []
            
        except Exception as e:
            print(f"DEBUG - Erreur : {e}")  # Debug print
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