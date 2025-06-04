import random
import string
import re
import sqlite3
from datetime import datetime, timedelta
from discord.ext import tasks
from config.logging_config import setup_logging
from database.database_sync import DatabaseSync
from database.database_classement import DatabaseClassement
from utils.ftp_handler import FTPHandler

class PlayerSync:
    def __init__(self, bot, log_file_path, ftp_handler=None):
        """Initialise le système de synchronisation des joueurs"""
        self.bot = bot
        self.log_file_path = log_file_path
        self.ftp = ftp_handler or FTPHandler()
        self.db = DatabaseSync()
        self.classement_db = DatabaseClassement()
        self.game_db_path = 'game.db'
        self.verification_codes = {}
        self.verification_timeouts = {}

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
        except Exception as e:
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
            pass
        return None, None, None, None

    def parse_kill_line(self, line):
        """Parse une ligne de log pour détecter un kill"""
        try:
            # Format attendu : [2025.06.01-17.57.38:972][555]LogKill: Killer: pago-fraise (uid 12364) killed Victim: victime-name (uid 56789)
            match = re.search(r'LogKill: Killer: ([^()]+) \(uid (\d+)\) killed Victim: ([^()]+) \(uid (\d+)\)', line)
            if match:
                killer_name = match.group(1).strip()
                killer_uid = match.group(2)
                victim_name = match.group(3).strip()
                victim_uid = match.group(4)
                return killer_name, killer_uid, victim_name, victim_uid
        except Exception as e:
            pass
        return None, None, None, None

    @tasks.loop(seconds=5)
    async def check_logs(self):
        """Vérifie les logs pour les codes de vérification et les kills"""
        try:
            # Lire les logs
            log_content = self.ftp.read_database(self.log_file_path)
            if not log_content:
                return

            # Convertir en texte et filtrer les lignes
            log_text = log_content.decode('utf-8', errors='ignore')
            chat_lines = [line for line in log_text.splitlines() if 'ChatWindow' in line]
            kill_lines = [line for line in log_text.splitlines() if 'LogKill' in line]
            
            # Traiter les kills
            for line in kill_lines:
                killer_name, killer_uid, victim_name, victim_uid = self.parse_kill_line(line)
                if killer_name and killer_uid and victim_name and victim_uid:
                    # Vérifier si les joueurs sont valides
                    if self.classement_db.is_valid_player(killer_name) and self.classement_db.is_valid_player(victim_name):
                        # Mettre à jour les statistiques
                        self.classement_db.update_kill_stats(killer_uid, killer_name, victim_uid, victim_name)

            # Traiter les codes de vérification
            pending_verifications = self.db.get_pending_verifications()

            for discord_id, code in pending_verifications:
                # Chercher le code dans les lignes de chat
                for line in chat_lines:
                    if code in line:
                        # Extraire les informations du joueur
                        char_name, uid, steam_id, message = self.parse_log_line(line)
                        if char_name and uid and message:
                            # Vérifier que le message correspond exactement au code
                            if message == code:
                                # Vérifier le joueur
                                if self.db.verify_player(discord_id, char_name, uid, steam_id):
                                    # Envoyer un message de confirmation
                                    user = self.bot.get_user(int(discord_id))
                                    if user:
                                        await user.send(f"✅ Votre compte a été vérifié avec succès!\n")
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass

        except Exception as e:
            pass

    async def start(self):
        """Démarre le système de synchronisation"""
        self.check_logs.start()

    async def stop(self):
        """Arrête le système de synchronisation"""
        self.check_logs.stop()

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
            await ctx.send("❌ Une erreur est survenue lors de la récupération des informations.")

    # La fonction update_player_name a été supprimée car les joueurs ne peuvent pas changer leur nom in-game 