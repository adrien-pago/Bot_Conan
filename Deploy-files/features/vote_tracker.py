import logging
import re
from discord.ext import tasks
from config.logging_config import setup_logging
from database.database_sync import DatabaseSync
import sqlite3

logger = setup_logging()

class VoteTracker:
    def __init__(self, bot, top_server_channel_id, server_prive_channel_id, ftp_handler=None):
        """Initialise le système de suivi des votes"""
        self.bot = bot
        self.top_server_channel_id = top_server_channel_id
        self.server_prive_channel_id = server_prive_channel_id
        self.ftp = ftp_handler or FTPHandler()
        self.db = DatabaseSync()
        self.last_top_server_message = None
        self.last_server_prive_message = None
        logger.info(f"VoteTracker initialisé avec les canaux: Top-Serveurs={top_server_channel_id}, Serveur Privé={server_prive_channel_id}")

    @tasks.loop(seconds=10)
    async def check_votes(self):
        """Vérifie les nouveaux votes dans les canaux"""
        try:
            # Vérifier les votes sur Top-Serveurs
            top_server_channel = self.bot.get_channel(self.top_server_channel_id)
            if top_server_channel:
                logger.info(f"Vérification des votes dans Top-Serveurs (dernier message: {self.last_top_server_message})")
                async for message in top_server_channel.history(limit=10):
                    logger.info(f"Message trouvé - Auteur: {message.author.name} - Contenu: {message.content} (ID: {message.id})")
                    
                    # Vérifier si c'est un message de vote
                    if "vient de voter pour le serveur" in message.content:
                        if self.last_top_server_message and message.id <= self.last_top_server_message:
                            logger.info(f"Message déjà traité (ID: {message.id})")
                            break
                        
                        # Extraire le nom du joueur
                        try:
                            player_name = message.content.split(" vient de voter")[0]
                            logger.info(f"Vote Top-Serveurs détecté pour: {player_name}")
                            logger.info(f"Message complet: {message.content}")
                            
                            # Mettre à jour le wallet
                            await self.update_wallet(player_name)
                            
                            # Mettre à jour le dernier message vu
                            self.last_top_server_message = message.id
                            logger.info(f"Nouveau dernier message Top-Serveurs: {self.last_top_server_message}")
                            break
                        except Exception as e:
                            logger.error(f"Erreur lors de l'extraction du nom du joueur: {e}")
                            continue

            # Vérifier les votes sur Serveur Privé
            server_prive_channel = self.bot.get_channel(self.server_prive_channel_id)
            if server_prive_channel:
                logger.info(f"Vérification des votes dans Serveur Privé (dernier message: {self.last_server_prive_message})")
                async for message in server_prive_channel.history(limit=10):
                    logger.info(f"Message trouvé - Auteur: {message.author.name} - Contenu: {message.content} (ID: {message.id})")
                    
                    # Vérifier si c'est un message de vote
                    if "vient de voter pour le serveur" in message.content:
                        if self.last_server_prive_message and message.id <= self.last_server_prive_message:
                            logger.info(f"Message déjà traité (ID: {message.id})")
                            break
                        
                        # Extraire le nom du joueur
                        try:
                            player_name = message.content.split("Le joueur ")[1].split(" vient de voter")[0]
                            logger.info(f"Vote Serveur Privé détecté pour: {player_name}")
                            logger.info(f"Message complet: {message.content}")
                            
                            # Mettre à jour le wallet
                            await self.update_wallet(player_name)
                            
                            # Mettre à jour le dernier message vu
                            self.last_server_prive_message = message.id
                            logger.info(f"Nouveau dernier message Serveur Privé: {self.last_server_prive_message}")
                            break
                        except Exception as e:
                            logger.error(f"Erreur lors de l'extraction du nom du joueur: {e}")
                            continue

        except Exception as e:
            logger.error(f"Erreur lors de la vérification des votes: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def update_wallet(self, player_name: str):
        """Met à jour le wallet d'un joueur"""
        try:
            logger.info(f"Recherche du joueur {player_name} dans la base de données")
            # Récupérer les informations du joueur
            conn = sqlite3.connect('discord.db')
            c = conn.cursor()
            
            # Vérifier d'abord si le joueur existe
            c.execute('SELECT player_name, verified, discord_id, wallet FROM users WHERE LOWER(player_name) = LOWER(?)', (player_name,))
            result = c.fetchone()
            
            if result:
                db_player_name, verified, discord_id, wallet = result
                logger.info(f"Joueur trouvé dans la base de données: {db_player_name}")
                logger.info(f"État de vérification: {verified}")
                logger.info(f"Discord ID: {discord_id}")
                logger.info(f"Wallet actuel: {wallet}")
                
                if verified:
                    new_wallet = wallet + 50
                    # Mettre à jour le wallet
                    c.execute('''
                        UPDATE users
                        SET wallet = ?
                        WHERE discord_id = ?
                    ''', (new_wallet, discord_id))
                    conn.commit()
                    logger.info(f"Wallet mis à jour: {wallet} -> {new_wallet}")
                    
                    # Envoyer un message au joueur
                    user = self.bot.get_user(int(discord_id))
                    if user:
                        await user.send(f"✅ Merci pour votre vote !\n"
                                      f"Votre wallet a été augmenté de 50 points.\n"
                                      f"Nouveau solde: {new_wallet}")
                        logger.info(f"Message de confirmation envoyé à {user.name}")
                    else:
                        logger.warning(f"Utilisateur Discord non trouvé: {discord_id}")
                else:
                    logger.warning(f"Le joueur {player_name} n'est pas vérifié")
            else:
                logger.warning(f"Le joueur {player_name} n'existe pas dans la base de données")
                # Afficher tous les joueurs dans la base pour debug
                c.execute('SELECT player_name, verified FROM users')
                all_players = c.fetchall()
                logger.info(f"Liste des joueurs dans la base: {all_players}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du wallet: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            conn.close()

    async def start(self):
        """Démarre le système de suivi des votes"""
        self.check_votes.start()
        logger.info("Système de suivi des votes démarré")

    async def stop(self):
        """Arrête le système de suivi des votes"""
        self.check_votes.stop()
        logger.info("Système de suivi des votes arrêté") 