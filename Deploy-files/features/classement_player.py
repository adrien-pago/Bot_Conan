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
        logger.info(f"KillTracker initialisé avec channel_id: {channel_id}")

    async def start(self):
        """Démarre le tracker de kills"""
        try:
            logger.info("Tentative de démarrage de update_kills_task...")
            # Vérifier si le canal existe
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Impossible de trouver le canal avec ID {self.channel_id}")
                return
                
            logger.info(f"Canal trouvé: {channel.name} (ID: {channel.id})")
            
            # Vérifier les permissions
            permissions = channel.permissions_for(channel.guild.me)
            if not permissions.send_messages:
                logger.error(f"Pas d'autorisation d'envoi de messages dans le canal {channel.name}")
            if not permissions.manage_messages:
                logger.error(f"Pas d'autorisation de gestion des messages dans le canal {channel.name}")
                
            # Démarrer la tâche
            self.update_kills_task.start()
            logger.info("KillTracker démarré avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du KillTracker: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def stop(self):
        """Arrête le tracker de kills"""
        try:
            if self.update_kills_task.is_running():
                self.update_kills_task.stop()
                logger.info("KillTracker arrêté")
            else:
                logger.warning("KillTracker n'était pas en cours d'exécution")
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt du KillTracker: {e}")

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
            logger.info("Exécution de update_kills_task...")
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Canal {self.channel_id} introuvable")
                return
                
            logger.info(f"Récupération des stats pour le canal {channel.name}")
            stats = self.get_kill_stats()
            if not stats:
                logger.info("Aucune statistique disponible")
                return

            message = self.format_kill_stats(stats)
            
            try:
                # Supprimer les anciens messages
                await channel.purge(limit=1)
                # Envoyer le nouveau message
                await channel.send(message)
                logger.info("Classement des kills mis à jour")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du message: {e}")
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du classement: {e}")
            import traceback
            logger.error(traceback.format_exc())

    @update_kills_task.before_loop
    async def before_update_kills_task(self):
        """Attendre que le bot soit prêt avant de démarrer la tâche"""
        logger.info("Attente que le bot soit prêt...")
        await self.bot.wait_until_ready()
        logger.info("Bot prêt, tâche de mise à jour des kills peut démarrer")

    async def display_kills(self, ctx):
        """Affiche le classement des kills"""
        try:
            stats = self.get_kill_stats()
            message = self.format_kill_stats(stats)
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'affichage du classement: {e}")
