import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

class CustomFilter(logging.Filter):
    """Filtre personnalisé pour ne garder que les logs importants"""
    
    def filter(self, record):
        # Toujours garder les erreurs et warnings
        if record.levelno >= logging.WARNING:
            return True
        
        # Garder SEULEMENT les logs liés aux commandes buy
        message = record.getMessage().lower()
        if any(keyword in message for keyword in ['!buy', 'buy', 'achat']):
            return True
        
        # Garder les logs d'erreurs RCON importantes (même si niveau INFO)
        if any(keyword in message for keyword in ['broken pipe', 'connexion rcon', 'erreur rcon', 'rcon perdue']):
            return True
        
        # Filtrer tout le reste (RCON normal, tracker, etc.)
        return False

def setup_logging():
    """Configure le système de logging simplifié pour l'application"""
    
    # Créer les dossiers nécessaires
    os.makedirs('logs', exist_ok=True)
    os.makedirs('logs/archives', exist_ok=True)

    # Configuration du format simplifié
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configuration du logger racine
    root_logger = logging.getLogger()
    
    # Nettoyer les handlers existants
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.setLevel(logging.INFO)
    
    # Handler pour fichier avec rotation quotidienne
    file_handler = TimedRotatingFileHandler(
        'logs/bot_activity.log',
        when='midnight',
        interval=1,
        backupCount=30,  # Garder 30 jours d'archives
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    file_handler.addFilter(CustomFilter())
    
    # Fonction pour renommer les fichiers archivés
    def namer(default_name):
        """Renomme les fichiers archivés avec un format personnalisé"""
        base_filename = default_name.split('.')[0]
        # Extraire la date du nom par défaut et reformater
        parts = default_name.split('.')
        if len(parts) >= 2:
            date_str = parts[-1]  # La date est à la fin
            try:
                # Convertir la date du format par défaut vers notre format
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                new_name = f"logs/archives/bot_activity_{date_obj.strftime('%Y-%m-%d')}.log"
                return new_name
            except ValueError:
                pass
        return f"logs/archives/{os.path.basename(default_name)}"
    
    file_handler.namer = namer
    
    # Handler pour console (seulement erreurs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Seulement erreurs en console
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Ajouter les handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Désactiver les loggers externes bruyants
    logging.getLogger('discord').setLevel(logging.ERROR)
    logging.getLogger('discord.http').setLevel(logging.ERROR)
    logging.getLogger('discord.gateway').setLevel(logging.ERROR)
    logging.getLogger('discord.client').setLevel(logging.ERROR)
    
    return root_logger

def log_buy_command(user, item_name, quantity, price):
    """Log spécifique pour les commandes d'achat"""
    logger = logging.getLogger('bot.buy')
    logger.info(f"ACHAT - {user} a acheté {quantity}x {item_name} pour {price} coins")

def log_error(source, error_message):
    """Log spécifique pour les erreurs"""
    logger = logging.getLogger(f'bot.error.{source}')
    logger.error(f"ERREUR [{source}] - {error_message}") 