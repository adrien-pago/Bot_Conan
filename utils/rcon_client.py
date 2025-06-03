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
            
            # Essayer la commande GetPlayerList spécifique à Conan Exiles
            resp_player_list = self.execute("GetPlayerList")
            logger.info(f"Réponse de GetPlayerList: {resp_player_list}")
            
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
            
            # Si GetPlayerList n'a pas fonctionné, essayer avec ListPlayers
            resp = self.execute("ListPlayers")
            logger.info(f"Réponse brute de ListPlayers: {resp}")
            
            # Si aucun joueur n'est connecté
            if "No players" in resp or not resp.strip():
                logger.info("Aucun joueur connecté")
                return []
            
            players = []
            
            # Analyser la réponse ligne par ligne
            lines = resp.splitlines()
            
            # Ignorer la ligne d'en-tête si elle existe
            if lines and ("Idx" in lines[0] or "Char name" in lines[0] or "Player name" in lines[0]):
                lines = lines[1:]
                
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    logger.info(f"Ligne ListPlayers: {line}")
                    
                    # Format attendu: Idx | Char name | Player name | User ID | Platform ID | Platform Name
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 2:  # Au moins l'index et le nom du personnage
                            char_name = parts[1].strip()
                            if char_name and char_name != "Char name":
                                players.append(char_name)
                                logger.info(f"Joueur trouvé: {char_name}")
                    else:
                        # Format alternatif sans pipes
                        parts = line.strip().split()
                        if len(parts) >= 3:  # Au moins l'index, le nom et quelque chose d'autre
                            # Essayer de récupérer le nom du personnage (souvent la deuxième colonne)
                            char_name = parts[1]
                            if char_name and char_name != "Steam" and not char_name.isdigit():
                                players.append(char_name)
                                logger.info(f"Joueur trouvé (format alternatif): {char_name}")
                except Exception as e:
                    logger.warning(f"Erreur lors du parsing d'une ligne de ListPlayers: {line} - {str(e)}")
            
            # Si on a trouvé des joueurs, on retourne la liste
            if players:
                logger.info(f"Joueurs connectés avec noms de personnage: {players}")
                return players
            
            # Dernier recours: si la commande ListPlayerIDs est disponible
            try:
                resp2 = self.execute("ListPlayerIDs")
                logger.info(f"Réponse de ListPlayerIDs: {resp2}")
                
                # Ne pas traiter si la commande n'existe pas
                if "Couldn't find the command" in resp2:
                    logger.warning("La commande ListPlayerIDs n'est pas disponible")
                else:
                    # Extraire les noms des joueurs
                    lines2 = resp2.splitlines()
                    for line in lines2:
                        if not line.strip():
                            continue
                            
                        try:
                            parts = line.strip().split()
                            if len(parts) >= 3:
                                # Format possible: PlayerID CharID Name
                                char_name = ' '.join(parts[2:])  # Le nom peut contenir des espaces
                                if char_name and not char_name.isdigit():
                                    players.append(char_name)
                        except Exception as e:
                            logger.warning(f"Erreur lors du parsing de ListPlayerIDs: {line} - {str(e)}")
            except Exception as e:
                logger.warning(f"Erreur lors de l'exécution de ListPlayerIDs: {e}")
            
            # Retourner la liste finale des joueurs
            logger.info(f"Joueurs connectés (final): {players}")
            return players
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des joueurs en ligne: {str(e)}")
            return []

    def close(self):
        self.sock.close()
