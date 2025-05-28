import sqlite3
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialise la base de données discord.db avec la table classement"""
    try:
        # Connexion à la base de données (créera le fichier s'il n'existe pas)
        conn = sqlite3.connect('discord.db')
        cursor = conn.cursor()
        
        # Création de la table classement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classement (
                player_id TEXT PRIMARY KEY,
                player_name TEXT,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                last_kill TIMESTAMP,
                last_death TIMESTAMP
            )
        ''')
        
        # Commit des changements
        conn.commit()
        logger.info("Base de données 'discord.db' créée avec succès")
        logger.info("Table 'classement' créée avec succès")
        
        # Vérification de la création
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='classement'")
        if cursor.fetchone():
            logger.info("Vérification : La table 'classement' existe bien")
        else:
            logger.error("Erreur : La table 'classement' n'a pas été créée")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la base de données : {str(e)}")
        raise

if __name__ == "__main__":
    init_database() 