import asyncio
import logging
import os
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

class RconClient:
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.connected = False
        self.server_address = os.getenv('RCON_HOST', 'localhost')
        self.server_port = int(os.getenv('RCON_PORT', '25575'))
        self.password = os.getenv('RCON_PASSWORD', '')
        self.packet_id = 0
        self.event_callbacks: Dict[str, Callable] = {}

    async def initialize(self):
        """Initialise la connexion RCON"""
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.server_address, self.server_port
            )
            await self._authenticate()
            self.connected = True
            logger.info("Connexion RCON établie avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation RCON: {str(e)}")
            raise

    async def _authenticate(self):
        """Authentifie la connexion RCON"""
        try:
            # Envoyer le paquet d'authentification
            await self._send_packet(3, self.password)
            
            # Lire la réponse
            response = await self._read_packet()
            if response['type'] != 2:  # 2 = SERVERDATA_AUTH_RESPONSE
                raise Exception("Échec de l'authentification RCON")
                
            logger.info("Authentification RCON réussie")
        except Exception as e:
            logger.error(f"Erreur lors de l'authentification RCON: {str(e)}")
            raise

    async def execute(self, command: str) -> str:
        """Exécute une commande RCON et retourne la réponse"""
        if not self.connected:
            await self.initialize()
            
        try:
            # Envoyer la commande
            await self._send_packet(2, command)  # 2 = SERVERDATA_EXECCOMMAND
            
            # Lire la réponse
            response = await self._read_packet()
            return response['payload'].decode('utf-8').strip()
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande RCON: {str(e)}")
            raise

    async def _send_packet(self, packet_type: int, payload: str):
        """Envoie un paquet RCON"""
        if not self.writer:
            raise Exception("Pas de connexion RCON active")
            
        # Construire le paquet
        self.packet_id += 1
        payload_bytes = payload.encode('utf-8')
        packet = (
            len(payload_bytes) + 10  # Taille totale
            + self.packet_id.to_bytes(4, 'little')  # ID du paquet
            + packet_type.to_bytes(4, 'little')  # Type du paquet
            + payload_bytes  # Payload
            + b'\x00\x00'  # Terminateurs
        )
        
        # Envoyer le paquet
        self.writer.write(packet)
        await self.writer.drain()

    async def _read_packet(self) -> Dict[str, Any]:
        """Lit un paquet RCON"""
        if not self.reader:
            raise Exception("Pas de connexion RCON active")
            
        # Lire la taille du paquet
        size_bytes = await self.reader.read(4)
        if not size_bytes:
            raise Exception("Connexion RCON fermée")
            
        size = int.from_bytes(size_bytes, 'little')
        
        # Lire le reste du paquet
        packet = await self.reader.read(size)
        if not packet:
            raise Exception("Connexion RCON fermée")
            
        # Décoder le paquet
        packet_id = int.from_bytes(packet[0:4], 'little')
        packet_type = int.from_bytes(packet[4:8], 'little')
        payload = packet[8:-2]  # Exclure les terminateurs
        
        return {
            'id': packet_id,
            'type': packet_type,
            'payload': payload
        }

    def close(self):
        """Ferme la connexion RCON"""
        if self.writer:
            self.writer.close()
            self.writer = None
        self.connected = False
        logger.info("Connexion RCON fermée") 