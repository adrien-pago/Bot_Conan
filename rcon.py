import socket
import struct
import os
from dotenv import load_dotenv

load_dotenv()

class ServerQuery:
    def __init__(self):
        """Initialisation du client de requête serveur"""
        self.host = os.getenv('FTP_HOST')
        self.port = int(os.getenv('RCON_PORT', 27015))  # Par défaut, c'est le port jeu + 1

    def _send_request(self, request_type, challenge=0):
        """Envoie une requête au serveur"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(2)  # Délai normal pour une requête UDP
                sock.connect((self.host, self.port))
                
                # Créer le paquet
                if request_type == 'info':
                    packet = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
                elif request_type == 'players':
                    packet = struct.pack('cBBB', b'\xFF', 0x55, challenge & 0xFF, challenge >> 8)
                
                sock.send(packet)
                response = sock.recv(4096)
                return response
        except Exception as e:
            print(f"Erreur lors de la requête : {str(e)}")
            return None

    def get_online_players(self):
        """Obtenir la liste des joueurs connectés"""
        try:
            # D'abord obtenir un challenge
            response = self._send_request('info')
            if not response:
                return []
                
            # Extraire le challenge
            challenge = struct.unpack('i', response[5:9])[0]
            
            # Obtenir la liste des joueurs
            response = self._send_request('players', challenge)
            if not response:
                return []
                
            # Analyser la réponse
            players = []
            offset = 11  # Skip header
            while offset < len(response):
                player = {}
                player['name'] = response[offset:].split(b'\x00')[0].decode()
                offset += len(player['name']) + 1
                players.append(player)
            
            return [player['name'] for player in players if player['name']]
        except Exception as e:
            print(f"Erreur lors de la récupération des joueurs : {str(e)}")
            return []

    def get_server_info(self):
        """Obtenir les informations du serveur"""
        try:
            response = self._send_request('info')
            if not response:
                return None
                
            # Analyser la réponse
            info = {}
            info['name'] = response[11:].split(b'\x00')[0].decode()
            info['map'] = response[11:].split(b'\x00')[1].decode()
            info['players'] = struct.unpack('B', response[28:29])[0]
            info['max_players'] = struct.unpack('B', response[29:30])[0]
            
            return info
        except Exception as e:
            print(f"Erreur lors de la récupération des informations serveur : {str(e)}")
            return None
