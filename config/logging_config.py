import logging
import logging.handlers
import os

def setup_logging():
    """Configure le système de logging"""
    # Créer le dossier logs s'il n'existe pas
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configuration du format de base
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configuration du handler de fichier
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/bot.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Configuration du handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Configuration des loggers spécifiques
    loggers = {
        'bot': logging.DEBUG,
        'rcon': logging.DEBUG,
        'killtracker': logging.DEBUG,
        'buildtracker': logging.DEBUG,
        'playertracker': logging.DEBUG,
        'clantracker': logging.DEBUG,
        'database': logging.DEBUG,
        'ftp': logging.DEBUG
    }

    # Configurer chaque logger
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    # Configurer le logger Discord
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    discord_logger.propagate = False
    discord_logger.addHandler(file_handler)
    discord_logger.addHandler(console_handler)

    return logging.getLogger('bot') 