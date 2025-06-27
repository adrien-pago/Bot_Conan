# rcon.py

import socket, struct, os, threading
from dotenv import load_dotenv
import logging
import asyncio
import time
import json

# Utiliser le logger configuré dans bot.py
logger = logging.getLogger(__name__)

load_dotenv()

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
        self.last_command_time = 0  # Timestamp de la dernière commande
        self.min_command_interval = 2.0  # Intervalle minimum entre les commandes (en secondes)
        
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

    def _rate_limit_check(self):
        """Vérifie et respecte le rate limiting des commandes RCON"""
        current_time = time.time()
        time_since_last = current_time - self.last_command_time
        
        if time_since_last < self.min_command_interval:
            sleep_time = self.min_command_interval - time_since_last
            logger.debug(f"Rate limiting: attente de {sleep_time:.2f} secondes")
            time.sleep(sleep_time)
        
        self.last_command_time = time.time()

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

    def execute(self, command: str, auto_retry: bool = True) -> str:
        """Exécute une commande RCON avec gestion du rate limiting et reconnexion automatique"""
        self._rate_limit_check()
        
        try:
            self._ensure_connection()
            
            # Utiliser un autre ID (2) pour l'exécution de commande (type=2)
            self._send_packet(2, 2, command)
            _, _, payload = self._recv_packet()
            
            # Vérifier si la réponse indique "Too many commands"
            if "Too many commands" in payload:
                logger.warning(f"Rate limit RCON atteint pour la commande '{command}'. Attente de 5 secondes...")
                time.sleep(5)  # Attendre 5 secondes avant de réessayer
                raise RuntimeError("Too many commands, try again later")
            
            return payload
            
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
            # Gestion spécifique des erreurs de connexion
            logger.warning(f"Connexion RCON perdue lors de l'exécution de '{command}': {e}")
            self.connected = False
            
            if auto_retry:
                logger.info("Tentative de reconnexion automatique...")
                try:
                    self._connect()
                    # Réessayer la commande une seule fois après reconnexion
                    return self.execute(command, auto_retry=False)
                except Exception as reconnect_error:
                    logger.error(f"Échec de la reconnexion automatique: {reconnect_error}")
                    raise RuntimeError(f"Connexion RCON perdue et reconnexion échouée: {e}")
            else:
                raise RuntimeError(f"Erreur RCON: {e}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la commande RCON '{command}': {e}")
            raise

    def get_online_players(self) -> list[str]:
        """Récupère la liste des joueurs connectés avec reconnexion automatique"""
        max_attempts = 2  # Maximum 2 tentatives
        
        for attempt in range(max_attempts):
            try:
                self._ensure_connection()
                
                # Essayer la commande GetPlayerList spécifique à Conan Exiles
                try:
                    resp_player_list = self.execute("GetPlayerList", auto_retry=(attempt == 0))
                    logger.debug(f"Réponse de GetPlayerList: {resp_player_list}")
                    
                    # Si la commande a fonctionné et retourne des données JSON valides
                    if resp_player_list and resp_player_list.strip() and "{" in resp_player_list:
                        try:
                            # Nettoyer la réponse si nécessaire pour obtenir un JSON valide
                            json_str = resp_player_list.strip()
                            if json_str.startswith("Command 'GetPlayerList' succeeded!"):
                                json_str = json_str.replace("Command 'GetPlayerList' succeeded!", "").strip()
                            
                            # Analyser le JSON
                            player_data = json.loads(json_str)
                            players = []
                            
                            # Format attendu: {"players": [{"playerId": 12345, "name": "PlayerName", "charName": "CharacterName"}, ...]}
                            if "players" in player_data and isinstance(player_data["players"], list):
                                for player in player_data["players"]:
                                    # Utiliser le nom du personnage s'il existe, sinon le nom du joueur
                                    if "charName" in player and player["charName"]:
                                        players.append(player["charName"])
                                    elif "name" in player and player["name"]:
                                        players.append(player["name"])
                            
                                if players:
                                    logger.info(f"Joueurs connectés via GetPlayerList: {players}")
                                    return players
                        except Exception as e:
                            logger.warning(f"Erreur lors du parsing du JSON de GetPlayerList: {e}")
                except RuntimeError as e:
                    if "Too many commands" in str(e):
                        logger.warning("GetPlayerList: Too many commands, passage à ListPlayers")
                    elif "Connexion RCON perdue" in str(e) and attempt == 0:
                        logger.warning("GetPlayerList: Connexion perdue, nouvelle tentative...")
                        continue  # Réessayer avec ListPlayers
                    else:
                        raise
                
                # Si GetPlayerList n'a pas fonctionné, essayer avec ListPlayers
                try:
                    resp = self.execute("ListPlayers", auto_retry=(attempt == 0))
                    logger.debug(f"Réponse brute de ListPlayers: {resp}")
                    
                    # Si aucun joueur n'est connecté
                    if "No players" in resp or not resp.strip():
                        logger.info("Aucun joueur connecté")
                        return []
                    
                    # Vérifier si la réponse contient une erreur
                    if "Too many commands" in resp:
                        logger.warning("ListPlayers: Too many commands, retour liste vide")
                        return []
                    
                    # Analyser la liste des joueurs
                    players = []
                    lines = resp.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('Command') and not line.startswith('Player'):
                            # Format typique: "PlayerName (Steam ID: 76561198123456789)"
                            if '(' in line:
                                player_name = line.split('(')[0].strip()
                                if player_name:
                                    players.append(player_name)
                            elif line:  # Si pas de parenthèses, prendre la ligne entière
                                players.append(line)
                    
                    logger.info(f"Joueurs connectés via ListPlayers: {players}")
                    return players
                    
                except RuntimeError as e:
                    if "Connexion RCON perdue" in str(e) and attempt == 0:
                        logger.warning("ListPlayers: Connexion perdue, nouvelle tentative...")
                        continue  # Réessayer
                    else:
                        raise
                        
                # Si on arrive ici, les deux commandes ont échoué mais sans erreur de connexion
                logger.warning("Aucune commande RCON n'a fonctionné, retour liste vide")
                return []
                
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError) as e:
                logger.error(f"Erreur de connexion RCON (tentative {attempt + 1}/{max_attempts}): {e}")
                self.connected = False
                
                if attempt < max_attempts - 1:
                    logger.info("Tentative de reconnexion...")
                    try:
                        time.sleep(2)  # Attendre 2 secondes avant de réessayer
                        self._connect()
                    except Exception as reconnect_error:
                        logger.error(f"Échec de la reconnexion: {reconnect_error}")
                        continue
                else:
                    logger.error("Toutes les tentatives de reconnexion ont échoué")
                    raise RuntimeError(f"Erreur lors de la récupération des joueurs en ligne: {e}")
                    
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la récupération des joueurs en ligne: {e}")
                if attempt == max_attempts - 1:
                    raise RuntimeError(f"Erreur lors de la récupération des joueurs en ligne: {e}")
        
        # Si on arrive ici, toutes les tentatives ont échoué
        logger.error("Impossible de récupérer la liste des joueurs après toutes les tentatives")
        return []

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.connected = False
