import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Discord
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN or DISCORD_TOKEN.count('.') != 2:
    raise RuntimeError("Le token Discord est manquant ou invalide dans votre .env")

# IDs des canaux Discord
TEST_CHANNEL_ID = int(os.getenv('TEST_CHANNEL_ID', '1375046216097988629'))
KILLS_CHANNEL_ID = int(os.getenv('KILLS_CHANNEL_ID', '1375046216097988629'))
BUILD_CHANNEL_ID = int(os.getenv('BUILD_CHANNEL_ID', '1375234869071708260'))
PLAYER_COUNT_CHANNEL_ID = int(os.getenv('PLAYER_COUNT_CHANNEL_ID', '1375223092892401737'))

# Configuration FTP
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')
FTP_DB_PATH = os.getenv('FTP_DB_PATH')

# Configuration RCON
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT', '25575'))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

# Constantes du jeu
LIMITE_CONSTRUCTION = 12000
MAX_PLAYERS = 40

# Configuration des tâches planifiées
UPDATE_CHANNEL_INTERVAL = 8  # minutes
BUILD_CHECK_INTERVAL = 5     # minutes
KILLS_UPDATE_INTERVAL = 1    # minute

# Configuration des raids
RAID_DAYS = [5, 6]  # Samedi, Dimanche
RAID_START_HOUR = 20
RAID_END_HOUR = 23