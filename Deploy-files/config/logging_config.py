import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure le système de logging pour l'application"""
    # Créer le dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configuration du format de base
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configuration du handler pour les fichiers
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Configuration du handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configuration des loggers spécifiques
    loggers = {
        'bot': logging.INFO,
        'rcon': logging.INFO,
        'ftp': logging.INFO,
        'discord': logging.WARNING
    }

    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    return root_logger 