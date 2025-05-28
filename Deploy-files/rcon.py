# rcon.py

import socket, struct, os, time
from dotenv import load_dotenv
import logging
import asyncio

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('rcon')

load_dotenv()

class RconClient:
    def __init__(self):
        """Initialise le client RCON"""
        self.host = os.getenv('GAME_SERVER_HOST', '176.57.178.12')
        self.port = int(os.getenv('RCON_PORT', '28316'))
        self.password = os.getenv('RCON_PASSWORD', '102633')
        self.timeout = 10.0
        self.sock = None
        self.connected = False
        self.event_callbacks = []
        self.max_retries = 3
        self.retry_delay = 5

    async def initialize(self):
        """Initialise la connexion RCON"""
        await self._connect()
        return self

    def _create_packet(self, packet_type, payload):
        """Crée un paquet RCON selon le protocole Unreal Engine"""
        try:
            if isinstance(payload, str):
                payload = payload.encode('utf-8')
            
            # Format Unreal Engine RCON: [packet_size(4)][request_id(4)][type(4)][payload][null_terminator(2)]
            packet = struct.pack('<ii', 1, packet_type) + payload + b'\x00\x00'
            size = len(packet)
            packet = struct.pack('<i', size) + packet
            
            return packet
        except Exception as e:
            logger.error(f"Erreur lors de la création du paquet RCON: {e}")
            raise

    async def _send_packet(self, packet):
        """Envoie un paquet RCON"""
        try:
            if not self.sock:
                raise RuntimeError("Socket non initialisé")
            
            await asyncio.sleep(0.5)  # Réduit le délai entre les paquets
            self.sock.sendall(packet)
            logger.debug("Paquet RCON envoyé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du paquet RCON: {e}")
            self.connected = False
            raise

    async def _receive_packet(self):
        """Reçoit un paquet RCON"""
        try:
            if not self.sock:
                raise RuntimeError("Socket non initialisé")

            # Lire la taille du paquet
            size_data = self.sock.recv(4)
            if not size_data:
                raise ConnectionError("Connexion fermée par le serveur")
            
            size = struct.unpack('<i', size_data)[0]
            
            # Lire le reste du paquet
            data = b''
            remaining = size
            while remaining > 0:
                chunk = self.sock.recv(min(remaining, 4096))
                if not chunk:
                    raise ConnectionError("Connexion fermée par le serveur")
                data += chunk
                remaining -= len(chunk)
            
            # Décoder le paquet
            packet_id = struct.unpack('<i', data[0:4])[0]
            packet_type = struct.unpack('<i', data[4:8])[0]
            payload = data[8:-2].decode('utf-8', errors='ignore')
            
            return {
                'id': packet_id,
                'type': packet_type,
                'payload': payload
            }
        except Exception as e:
            logger.error(f"Erreur lors de la réception du paquet RCON: {e}")
            self.connected = False
            raise

    async def _connect(self):
        """Établit la connexion RCON avec retry"""
        retries = 0
        while retries < self.max_retries:
            try:
                logger.debug(f"Tentative de connexion RCON à {self.host}:{self.port} (tentative {retries + 1}/{self.max_retries})")
                
                # Fermer l'ancienne connexion si elle existe
                if self.sock:
                    try:
                        self.sock.close()
                    except:
                        pass
                    self.sock = None
                
                # Créer un nouveau socket
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.timeout)
                
                # Se connecter au serveur
                self.sock.connect((self.host, self.port))
                logger.debug("Connexion RCON établie")
                
                # Attendre un peu avant l'authentification
                await asyncio.sleep(1)
                
                # Envoyer le paquet d'authentification
                auth_packet = self._create_packet(3, self.password)
                await self._send_packet(auth_packet)
                
                # Attendre un peu avant de recevoir la réponse
                await asyncio.sleep(1)
                
                # Recevoir la réponse
                response = await self._receive_packet()
                
                if response['id'] == -1:
                    raise RuntimeError("Authentification RCON échouée")
                
                logger.debug("Authentification RCON réussie")
                self.connected = True
                return
                
            except Exception as e:
                logger.error(f"Erreur lors de la connexion RCON (tentative {retries + 1}): {e}")
                retries += 1
                if retries < self.max_retries:
                    logger.info(f"Tentative de reconnexion dans {self.retry_delay} secondes...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise RuntimeError(f"Impossible de se connecter au serveur RCON après {self.max_retries} tentatives")

    async def execute(self, command):
        """Exécute une commande RCON avec retry"""
        retries = 0
        while retries < self.max_retries:
            try:
                if not self.connected:
                    await self._connect()
                
                # Créer et envoyer le paquet de commande
                packet = self._create_packet(2, command)
                await self._send_packet(packet)
                
                # Attendre un peu avant de recevoir la réponse
                await asyncio.sleep(0.5)
                
                # Recevoir la réponse
                response = await self._receive_packet()
                return response['payload']
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de la commande RCON (tentative {retries + 1}): {e}")
                retries += 1
                if retries < self.max_retries:
                    logger.info(f"Tentative de reconnexion dans {self.retry_delay} secondes...")
                    await asyncio.sleep(self.retry_delay)
                    await self._connect()
                else:
                    raise RuntimeError(f"Impossible d'exécuter la commande RCON après {self.max_retries} tentatives")

    async def get_online_players(self):
        """Récupère la liste des joueurs en ligne"""
        try:
            resp = await self.execute("ListPlayers")
            if not resp:
                return []
            
            # Parser la réponse
            players = []
            for line in resp.split('\n'):
                if line.strip():
                    # Extraire le nom du joueur (dernier élément de la ligne)
                    parts = line.strip().split()
                    if parts:
                        players.append(parts[-1])
            
            return players
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs: {e}")
            return []

    def close(self):
        """Ferme la connexion RCON"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.connected = False

    def is_connected(self):
        """Vérifie si la connexion est active"""
        if not self.sock:
            return False
        try:
            # Envoyer un paquet de test
            test_packet = self._create_packet(2, "version")
            self._send_packet(test_packet)
            return True
        except:
            self.connected = False
            return False

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
                    logs = await self.execute("getlastlog")
                    
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

    def _ensure_connection(self):
        """S'assure que la connexion est établie"""
        if not self.is_connected():
            try:
                self._connect()
            except Exception as e:
                logger.error(f"Erreur lors de la connexion RCON: {str(e)}")
                raise RuntimeError("Impossible de se connecter au serveur RCON")

    def _auth(self) -> bool:
        # Utiliser un petit ID (1) pour l'authentification (type=3)
        self._send_packet(self._create_packet(3, self.password))
        req_id, type_id, _ = self._receive_packet()
        return req_id != -1  # -1 = échec
