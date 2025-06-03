# rcon.py

import socket, struct, os, threading
from dotenv import load_dotenv
import logging
import asyncio
import time

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

load_dotenv()

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

load_dotenv()

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

class RCONClient:
    DEFAULT_TIMEOUT = 10.0  # Timeout par défaut en secondes
    
    def __init__(self, timeout: float = None, max_retries: int = 3):
        self.host = os.getenv('GAME_SERVER_HOST')
        self.port = int(os.getenv('RCON_PORT'))
        self.password = os.getenv('RCON_PASSWORD')
        self.max_retries = max_retries
        self.retries = 0
        self.sock = None
        self.event_callbacks = []  # Liste des callbacks pour les événements
        self.connected = False
        
        # Vérifier que les variables d'environnement sont définies
        if not self.host:
            raise ValueError("GAME_SERVER_HOST n'est pas défini dans .env")
        if not self.port:
            raise ValueError("RCON_PORT n'est pas défini dans .env")
        if not self.password:
            raise ValueError("RCON_PASSWORD n'est pas défini dans .env")
        
        # Utiliser le timeout par défaut si aucun n'est fourni
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Initialiser la connexion
        self._connect()

    def _connect(self):
        """Tente de se connecter au serveur RCON avec gestion des reconnexions"""
        try:
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None
            
            # Vérifier la connexion avant de continuer
            if not self.sock:
                self.sock = socket.create_connection((self.host, self.port), self.timeout)
            
            # Authentification
            if not self._auth():
                raise RuntimeError("Authentification RCON échouée")
            
            self.retries = 0
            self.connected = True
            logger.info(f"Connexion RCON réussie après {self.retries} tentatives")
            
        except (socket.timeout, ConnectionRefusedError, ConnectionResetError, BrokenPipeError) as e:
            self.connected = False
            if self.retries < self.max_retries:
                self.retries += 1
                logger.warning(f"Échec de la connexion RCON (tentative {self.retries}/{self.max_retries}): {str(e)}")
                time.sleep(5)
                self._connect()
            else:
                raise RuntimeError(f"Impossible de se connecter après {self.max_retries} tentatives: {str(e)}")
        except Exception as e:
            self.connected = False
            logger.error(f"Erreur inattendue lors de la connexion RCON: {str(e)}")
            raise RuntimeError(f"Erreur lors de la connexion RCON: {str(e)}")

    def _ensure_connection(self):
        """Assure que la connexion est active avant d'envoyer une commande"""
        if not self.connected or not self.sock:
            self._connect()
            if not self.connected:
                raise RuntimeError("Impossible de se connecter au serveur RCON")

    def _send_packet(self, req_id: int, type_id: int, payload: str):
        data   = payload.encode('utf8')
        length = 4 + 4 + len(data) + 2
        # length, requestId, typeId, payload, two null bytes
        pkt = struct.pack('<iii', length, req_id, type_id) + data + b'\x00\x00'
        self.sock.sendall(pkt)

    def _recv_packet(self):
        # lire length
        raw = self.sock.recv(4)
        if len(raw) < 4:
            raise ConnectionError("Réponse RCON incomplète")
        length = struct.unpack('<i', raw)[0]
        # lire le reste
        data = b''
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        req_id, type_id = struct.unpack('<ii', data[:8])
        payload = data[8:-2].decode('utf8', errors='ignore')
        return req_id, type_id, payload

    def _auth(self) -> bool:
        # Utiliser un petit ID (1) pour l'authentification (type=3)
        self._send_packet(1, 3, self.password)
        req_id, type_id, _ = self._recv_packet()
        return req_id != -1  # -1 = échec

    def execute(self, command: str) -> str:
        # Utiliser un autre ID (2) pour l'exécution de commande (type=2)
        self._send_packet(2, 2, command)
        _, _, payload = self._recv_packet()
        return payload

    def get_online_players(self) -> list[str]:
        """Récupère la liste des joueurs connectés"""
        try:
            self._ensure_connection()
            resp = self.execute("ListPlayers")
            players = []
            
            # Gérer le cas où il n'y a pas de joueurs
            if "No players" in resp or not resp.strip():
                logger.info("Aucun joueur connecté")
                return []
                
            # Ignorer la première ligne si c'est un en-tête
            lines = resp.splitlines()
            if lines and ("Name" in lines[0] or "ID" in lines[0] or "Player" in lines[0]):
                lines = lines[1:]
                
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    # Format attendu: "ID Name ... PlayerName"
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        # Le nom du joueur est généralement le dernier élément
                        name = parts[-1]
                        if name and name != "Name" and not name.isdigit():
                            players.append(name)
                except Exception as e:
                    logger.warning(f"Erreur lors du parsing d'une ligne de ListPlayers: {line} - {str(e)}")
                    
            logger.info(f"Joueurs connectés: {players}")
            return players
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs en ligne: {str(e)}")
            return []

    def close(self):
        self.sock.close()
