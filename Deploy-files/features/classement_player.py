from discord.ext import tasks
from config.logging_config import setup_logging
from database.database_classement import DatabaseClassement
from utils.ftp_handler import FTPHandler
import os
from dotenv import load_dotenv
import time

load_dotenv()

class KillTracker:
    def __init__(self, bot, channel_id):
        """Initialise le tracker de kills"""
        self.bot = bot
        self.channel_id = channel_id
        self.db = DatabaseClassement()
        self.ftp = FTPHandler()
        self.last_message = None
        self.last_update_time = 0
        self.last_stats = None
        self.min_update_interval = 30  # Délai minimum entre les mises à jour visuelles (en secondes)

    async def start(self):
        """Démarre le tracker de kills"""
        # Vérifier si le canal existe
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        # Vérifier les permissions
        permissions = channel.permissions_for(channel.guild.me)
        # Démarrer la tâche
        self.update_kills_task.start()

    async def stop(self):
        """Arrête le tracker de kills"""
        if self.update_kills_task.is_running():
            self.update_kills_task.stop()

    def format_kill_stats(self, stats):
        """Formate les statistiques de kills pour l'affichage"""
        if not stats:
            return "```\nAucune statistique disponible\n```"

        message = "```\n🏆 Classement des Kills 🏆\n\n"
        message += "Rang | Joueur       | Kills\n"
        message += "-----|--------------|-------\n"

        for i, stat in enumerate(stats, 1):
            player_name = stat[0][:12].ljust(12)
            kills = str(stat[1]).rjust(5)
            message += f"{i:3d}  | {player_name} | {kills}\n"

        message += "```"
        return message

    @tasks.loop(seconds=5)
    async def update_kills_task(self):
        """Met à jour le classement des kills toutes les 5 secondes"""
        # Vérifier les kills dans la base de données du jeu
        self.db.check_kills(self.ftp)
        # Vérifier si on doit mettre à jour l'affichage
        current_time = time.time()
        if current_time - self.last_update_time < self.min_update_interval:
            return
        # Mettre à jour l'affichage
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        stats = self.db.get_kill_stats()
        if not stats:
            return
        message = self.format_kill_stats(stats)
        # Supprimer l'ancien message si on en a un
        if self.last_message:
            try:
                await self.last_message.delete()
            except:
                pass
        # Envoyer le nouveau message
        self.last_message = await channel.send(message)
        self.last_stats = stats
        self.last_update_time = current_time

    @update_kills_task.before_loop
    async def before_update_kills_task(self):
        """Attendre que le bot soit prêt avant de démarrer la tâche"""
        await self.bot.wait_until_ready()

    async def display_kills(self, ctx):
        """Affiche le classement des kills"""
        try:
            stats = self.db.get_kill_stats()
            message = self.format_kill_stats(stats)
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'affichage du classement: {e}")
