import logging
from discord.ext import tasks
from config.logging_config import setup_logging
from database.database_classement import DatabaseClassement

logger = setup_logging()

class KillTracker:
    def __init__(self, bot, channel_id):
        """Initialise le tracker de kills"""
        self.bot = bot
        self.channel_id = channel_id
        self.db = DatabaseClassement()
        logger.info("KillTracker initialisé")

    async def start(self):
        """Démarre le tracker de kills"""
        self.update_kills_task.start()
        logger.info("KillTracker démarré")

    async def stop(self):
        """Arrête le tracker de kills"""
        self.update_kills_task.stop()
        logger.info("KillTracker arrêté")

    def update_kill_stats(self, killer_id: str, killer_name: str, victim_id: str, victim_name: str, is_kill: bool = True):
        """Met à jour les statistiques de kills"""
        try:
            self.db.update_kill_stats(killer_id, killer_name, victim_id, victim_name, is_kill)
            logger.info(f"Statistiques mises à jour pour {killer_name} et {victim_name}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des stats: {e}")
            raise

    def get_kill_stats(self):
        """Récupère les statistiques de kills triées par nombre de kills"""
        try:
            stats = self.db.get_kill_stats()
            return [{'player_name': row[0], 'kills': row[1]} for row in stats]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return []

    def format_kill_stats(self, stats):
        """Formate les statistiques de kills pour l'affichage"""
        if not stats:
            return "```\nAucune statistique disponible\n```"

        message = "```\nClassement du nombre de kills par joueur \n\n"
        message += "Joueur         | Kills\n"
        message += "----------------------\n"

        for i, stat in enumerate(stats, 1):
            player_name = stat['player_name'][:10].ljust(10)
            kills = str(stat['kills']).rjust(5)
            message += f"{i:2d}. {player_name} | {kills}\n"

        message += "```"
        return message

    @tasks.loop(minutes=1)
    async def update_kills_task(self):
        """Met à jour le classement des kills toutes les minutes"""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                stats = self.get_kill_stats()
                if not stats:
                    return

                message = self.format_kill_stats(stats)
                
                # Supprimer les anciens messages
                await channel.purge(limit=1)
                # Envoyer le nouveau message
                await channel.send(message)
                logger.info("Classement des kills mis à jour")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du classement: {e}")

    async def display_kills(self, ctx):
        """Affiche le classement des kills"""
        try:
            stats = self.get_kill_stats()
            message = self.format_kill_stats(stats)
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'affichage du classement: {e}")
