# rcon.py

import socket, struct, os
from dotenv import load_dotenv
import logging
import asyncio

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

load_dotenv()

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

load_dotenv()

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

class RconClient:
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
                self.sock.close()
            self.sock = socket.create_connection((self.host, self.port), self.timeout)
            
            # Authentification
            self._send_packet(1, 3, self.password)
            req_id, type_id, _ = self._recv_packet()
            
            if req_id == -1:
                raise RuntimeError("Authentification RCON échouée")
                
            self.retries = 0
            logger.info(f"Connexion RCON réussie après {self.retries} tentatives")
            
        except (socket.timeout, ConnectionRefusedError, ConnectionResetError) as e:
            if self.retries < self.max_retries:
                self.retries += 1
                logger.warning(f"Échec de la connexion RCON (tentative {self.retries}/{self.max_retries}): {str(e)}")
                time.sleep(5)
                self._connect()
            else:
                raise RuntimeError(f"Impossible de se connecter au serveur RCON après {self.max_retries} tentatives: {str(e)}")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la connexion RCON: {str(e)}")
            raise

    def add_event_callback(self, callback):
        """Ajoute un callback pour recevoir les événements RCON"""
        self.event_callbacks.append(callback)

    async def monitor_events(self):
        """Démarre la surveillance des événements RCON"""
        try:
            last_timestamp = None
            while True:
                try:
                    # Récupérer les derniers logs
                    logs = self.execute("getlastlog")
                    
                    # Analyser les logs pour détecter les kills
                    for line in logs.splitlines():
                        if "Killed" in line:
                            # Extraire le timestamp
                            parts = line.split()
                            current_timestamp = " ".join(parts[:2])
                            
                            # Ignorer les logs déjà traités
                            if last_timestamp and current_timestamp <= last_timestamp:
                                continue
                                
                            # Extraire les informations
                            killer = parts[1]
                            victim = parts[3]
                            
                            # Créer un événement
                            event = {
                                'type': 'kill',
                                'killer': killer,
                                'victim': victim,
                                'timestamp': current_timestamp
                            }
                            
                            # Notifier tous les callbacks
                            for callback in self.event_callbacks:
                                await callback(event)
                            
                            # Mettre à jour le timestamp
                            last_timestamp = current_timestamp
                    
                    # Attendre avant la prochaine vérification
                    await asyncio.sleep(2)  # Augmenter l'intervalle pour éviter le rate limiting
                    
                except (BrokenPipeError, ConnectionResetError) as e:
                    logger.warning(f"Connexion perdue: {str(e)}")
                    # Réinitialiser la connexion
                    self.sock = None
                    self.connected = False
                    await asyncio.sleep(5)
                    continue
                except Exception as e:
                    logger.error(f"Erreur lors du traitement des logs: {str(e)}")
                    await asyncio.sleep(5)  # Attendre plus longtemps en cas d'erreur
                    continue

        except Exception as e:
            logger.error(f"Erreur critique lors de la surveillance des événements: {str(e)}")
            raise

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
        """Envoie un paquet RCON"""
        self._ensure_connection()
        try:
            data   = payload.encode('utf8')
            length = 4 + 4 + len(data) + 2
            packet = struct.pack('<ii', length, req_id) + type_id.to_bytes(4, 'little') + data + b'\x00\x00'
            self.sock.sendall(packet)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du paquet RCON: {str(e)}")
            self.connected = False
            return False

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
        resp    = self.execute("ListPlayers")
        players = []
        for line in resp.splitlines():
            name = line.strip().split()[-1]
            players.append(name)
        return players

    def close(self):
        self.sock.close()
