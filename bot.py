import asyncio
import logging
from config.logging_config import setup_logging
from config.settings import *
from core.bot_core import ConanBot
from core.commands import setup as setup_commands

logger = setup_logging()

async def main():
    """Point d'entrée principal du bot"""
    try:
        # Créer et configurer le bot
        bot = ConanBot()
        
        # Ajouter les commandes
        await setup_commands(bot)
        
        # Démarrer le bot
        logger.info("Démarrage du bot...")
        await bot.start(DISCORD_TOKEN)
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot: {e}")
        raise

if __name__ == "__main__":
    try:
        # Démarrer le bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt du bot demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        raise 