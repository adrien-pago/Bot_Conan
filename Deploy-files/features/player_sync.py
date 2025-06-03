import logging
import random
import string
import re
import sqlite3
from datetime import datetime, timedelta
from discord.ext import tasks
from config.logging_config import setup_logging
from database.database_sync import DatabaseSync
from utils.ftp_handler import FTPHandler

logger = setup_logging()

class PlayerSync:
    def __init__(self, bot, log_file_path, ftp_handler=None):
        """Initialise le système de synchronisation des joueurs"""
        self.bot = bot
        self.log_file_path = log_file_path
        self.ftp = ftp_handler or FTPHandler()
        self.db = DatabaseSync()
        self.game_db_path = 'game.db'
        self.verification_codes = {}
        self.verification_timeouts = {}
        logger.info("PlayerSync initialisé")

    def generate_verification_code(self, length=8):
        """Génère un code de vérification aléatoire"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    async def start_verification(self, ctx):
        """Démarre le processus de vérification pour un utilisateur"""
        try:
            verification_code = self.generate_verification_code()
            self.db.create_verification(
                str(ctx.author.id),
                ctx.author.name,
                verification_code
            )
            
            await ctx.send(f"Pour lier votre compte Discord à votre compte de jeu, écrivez ce code dans le chat du jeu :\n```{verification_code}```\nVous avez 5 minutes pour le faire.")
            logger.info(f"Code de vérification généré pour {ctx.author.name}")
        except Exception as e:
            logger.error(f"Erreur lors de la génération du code de vérification: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la génération du code de vérification.")

    def parse_log_line(self, line):
        """Parse une ligne de log pour extraire les informations du joueur"""
        try:
            # Format attendu : [2025.06.01-17.57.38:972][555]ChatWindow: Character pago-fraise (uid 12364, player 76561198276177053) said: message
            match = re.search(r'Character ([^()]+) \(uid (\d+), player (\d+)\) said: (.+)', line)
            if match:
                char_name = match.group(1).strip()
                uid = match.group(2)
                steam_id = match.group(3)
                message = match.group(4).strip()
                return char_name, uid, steam_id, message
        except Exception as e:
            logger.error(f"Erreur lors du parsing de la ligne de log: {e}")
        return None, None, None, None

    @tasks.loop(seconds=5)
    async def check_logs(self):
        """Vérifie les logs pour les codes de vérification"""
        try:
            # Lire les logs
            log_content = self.ftp.read_database(self.log_file_path)
            if not log_content:
                logger.error("Impossible de lire les logs")
                return

            # Convertir en texte et filtrer les lignes de chat
            log_text = log_content.decode('utf-8', errors='ignore')
            chat_lines = [line for line in log_text.splitlines() if 'ChatWindow' in line]
            logger.info(f"Nombre de lignes de chat trouvées: {len(chat_lines)}")

            # Récupérer tous les codes de vérification en attente
            pending_verifications = self.db.get_pending_verifications()
            logger.info(f"Vérifications en attente: {len(pending_verifications)}")

            for discord_id, code in pending_verifications:
                logger.info(f"Recherche du code {code} pour l'utilisateur {discord_id}")
                
                # Chercher le code dans les lignes de chat
                for line in chat_lines:
                    if code in line:
                        logger.info(f"Code trouvé dans la ligne: {line}")
                        
                        # Extraire les informations du joueur
                        char_name, uid, steam_id, message = self.parse_log_line(line)
                        if char_name and uid and message:
                            logger.info(f"Informations extraites - Nom: {char_name}, UID: {uid}, Steam ID: {steam_id}, Message: {message}")
                            
                            # Vérifier que le message correspond exactement au code
                            if message == code:
                                # Vérifier le joueur
                                if self.db.verify_player(discord_id, char_name, uid, steam_id):
                                    logger.info(f"Joueur vérifié avec succès: {char_name} (UID: {uid}, Steam ID: {steam_id})")
                                    # Envoyer un message de confirmation
                                    user = self.bot.get_user(int(discord_id))
                                    if user:
                                        await user.send(f"✅ Votre compte a été vérifié avec succès!\n")
                                else:
                                    logger.error(f"Échec de la vérification pour {char_name} (UID: {uid})")
                            else:
                                logger.info(f"Message ne correspond pas au code attendu: {message} != {code}")
                        else:
                            logger.error(f"Impossible d'extraire les informations de la ligne: {line}")

        except Exception as e:
            logger.error(f"Erreur lors de la vérification des logs: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def start(self):
        """Démarre le système de synchronisation"""
        self.check_logs.start()
        logger.info("Système de synchronisation démarré")

    async def stop(self):
        """Arrête le système de synchronisation"""
        self.check_logs.stop()
        logger.info("Système de synchronisation arrêté")

    async def get_player_info(self, ctx):
        """Affiche les informations d'un joueur"""
        try:
            info = self.db.get_player_info(str(ctx.author.id))
            if info:
                discord_name, player_name, player_id, wallet, rp, date_end_rp, steam_id = info
                message = f"```\nInformations du joueur :\n"
                message += f"Discord : {discord_name}\n"
                if player_name:
                    message += f"Personnage : {player_name}\n"
                    message += f"ID Joueur : {player_id}\n"
                    if steam_id:
                        message += f"Steam ID : {steam_id}\n"
                    message += f"Wallet : {wallet}\n"
                    message += f"RP : {rp}\n"
                    if date_end_rp:
                        message += f"Fin RP : {date_end_rp}\n"
                else:
                    message += "Personnage non lié\n"
                message += "```"
            else:
                message = "❌ Aucune information trouvée pour votre compte."
            await ctx.send(message)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos du joueur: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des informations.")

    # La fonction update_player_name a été supprimée car les joueurs ne peuvent pas changer leur nom in-game 