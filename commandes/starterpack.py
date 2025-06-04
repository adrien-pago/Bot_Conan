from discord.ext import commands
import discord
import sqlite3
import datetime
import logging
import traceback

class StarterPack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="starterpack")
    async def starterpack_command(self, ctx):
        """Donne un pack de départ au joueur"""
        # Vérifier si la commande est utilisée en MP
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ Cette commande doit être utilisée en message privé avec le bot.")
            return

        try:
            logger = logging.getLogger('bot')
            player_info = self.bot.player_sync.db.get_player_info(str(ctx.author.id))
            if not player_info or not player_info[1]:
                await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande `!register` pour vous inscrire.")
                return
            discord_name, player_name, player_id, wallet, rp, date_end_rp, steam_id = player_info
            logger.info(f"Traitement starterpack pour {ctx.author.name} (Discord ID: {ctx.author.id})")
            logger.info(f"Informations joueur : Nom={player_name}, ID={player_id}, Steam ID={steam_id}")
            if not steam_id:
                await ctx.send("❌ Votre compte n'a pas de Steam ID associé. Veuillez contacter un administrateur.")
                logger.error(f"Pas de Steam ID pour le joueur {player_name} (Discord ID: {ctx.author.id})")
                return
            if self.bot.player_sync.db.has_received_starterpack(str(ctx.author.id)):
                await ctx.send("❌ Vous avez déjà reçu votre pack de départ. Cette commande ne peut être utilisée qu'une seule fois par joueur.")
                return
            # Vérifier la présence en ligne avec la méthode unifiée
            if not self.bot.item_manager.is_player_online(steam_id):
                await ctx.send(f"❌ Vous devez être connecté au serveur avec votre personnage '{player_name}' pour recevoir votre pack de départ.")
                return
            # Message d'attente
            wait_msg = await ctx.send("⏳ Préparation de votre pack de départ, veuillez patienter...")
            logger.info(f"Tentative d'envoi du starter pack pour le joueur avec Steam ID {steam_id}")
            if await self.bot.item_manager.give_starter_pack_by_steam_id(steam_id):
                self.bot.player_sync.db.set_starterpack_received(str(ctx.author.id))
                try:
                    await wait_msg.edit(content=f"✅ Votre pack de départ a été ajouté à votre inventaire!\n"
                                  f"Personnage : {player_name}\n"
                                  f"Contenu : Piolet stellaire, couteau stellaire, grande hache stellaire, coffre en fer, cheval, selle légère et extrait d'aoles.")
                    logger.info("Message de réussite starterpack édité avec succès.")
                except Exception as e:
                    logger.error(f"Erreur lors de l'édition du message de réussite starterpack: {e}")
                    await ctx.send(f"✅ Votre pack de départ a été ajouté à votre inventaire!\nPersonnage : {player_name}\nContenu : Piolet stellaire, couteau stellaire, grande hache stellaire, coffre en fer, cheval, selle légère et extrait d'aoles.")
                conn = sqlite3.connect('discord.db')
                c = conn.cursor()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    c.execute("INSERT INTO item_transactions (discord_id, player_name, item_id, count, price, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (str(ctx.author.id), player_name, 0, 1, 0, "StarterPack Distribué", timestamp))
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
                finally:
                    conn.close()
            else:
                await wait_msg.edit(content="❌ Une erreur est survenue lors de l'ajout du pack de départ. Vérifiez que vous êtes bien connecté au serveur.")
        except Exception as e:
            logger = logging.getLogger('bot')
            logger.error(f"Erreur dans starterpack_command: {e}")
            logger.error(traceback.format_exc())
            await ctx.send("❌ Une erreur est survenue lors de l'ajout du pack de départ. Veuillez contacter un administrateur.")

async def setup(bot):
    await bot.add_cog(StarterPack(bot)) 