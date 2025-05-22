# rcon.py

import socket, struct, os
from dotenv import load_dotenv

load_dotenv()

class RconClient:
    def __init__(self, timeout: float = 10.0):
        self.host     = os.getenv('GAME_SERVER_HOST')
        self.port     = int(os.getenv('RCON_PORT'))
        self.password = os.getenv('RCON_PASSWORD')

        if not (self.host and self.password):
            raise RuntimeError("❌ Host ou mot de passe RCON manquant dans .env")

        # 1) Ouvrir le socket
        self.sock = socket.create_connection((self.host, self.port), timeout)

        # 2) Authentifier
        if not self._auth():
            raise RuntimeError("❌ Authentification RCON échouée")

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
