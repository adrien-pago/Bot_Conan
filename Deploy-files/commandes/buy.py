import discord
from discord.ext import commands
import sqlite3
from config.logging_config import log_buy_command, log_error

DB_PATH = 'discord.db'

class Buy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def buy(self, ctx, id_item_shop: int = None):
        """
        Permet d'acheter un item via son id_item_shop. Utilisable uniquement en DM avec le bot.
        """
        # Vérifier que la commande est en DM
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("❌ Cette commande ne peut être utilisée qu'en message privé avec le bot.")
            return

        if id_item_shop is None:
            await ctx.send("❌ Merci de préciser l'ID de l'item à acheter. Exemple : !buy 101")
            return

        # Récupérer l'item dans la base de données
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, item_id, count, price FROM items WHERE id_item_shop = ? AND enabled = 1", (id_item_shop,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                await ctx.send(f"❌ Aucun item trouvé avec l'ID boutique {id_item_shop}.")
                return
            item_name, item_id, count, price = row

            # Récupérer le wallet du joueur
            discord_id = str(ctx.author.id)
            cursor.execute("SELECT wallet FROM users WHERE discord_id = ?", (discord_id,))
            wallet_row = cursor.fetchone()
            if not wallet_row:
                conn.close()
                await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande !register pour vous inscrire.")
                return
            wallet = wallet_row[0] or 0

            if wallet < price:
                conn.close()
                await ctx.send(f"❌ Solde insuffisant. Il vous faut {price} coins pour acheter cet item. Votre solde actuel : {wallet} coins.")
                return

            # Vérifier la présence en ligne comme pour le starterpack
            item_manager = self.bot.item_manager
            steam_id = item_manager.get_player_steamid(discord_id)
            if not steam_id:
                conn.close()
                await ctx.send("❌ Vous n'êtes pas encore enregistré. Utilisez la commande !register pour vous inscrire.")
                return
            if not item_manager.is_player_online(steam_id):
                conn.close()
                await ctx.send("❌ Vous devez être connecté au serveur pour acheter cet item.")
                return

            # Give l'item
            success, error_msg = await item_manager.give_item_to_player(discord_id, item_id, count)
            if success:
                # Mettre à jour le wallet
                new_wallet = wallet - price
                cursor.execute("UPDATE users SET wallet = ? WHERE discord_id = ?", (new_wallet, discord_id))
                conn.commit()
                conn.close()
                
                # 📝 LOG DE L'ACHAT RÉUSSI
                log_buy_command(ctx.author.display_name, item_name, count, price)
                
                await ctx.send(f"✅ L'item **{item_name}** (x{count}) t'a été donné avec succès ! Nouveau solde : {new_wallet} coins.")
            else:
                conn.close()
                
                # 📝 LOG DE L'ERREUR DE GIVE
                log_error("BUY_GIVE", f"Échec give pour {ctx.author.display_name} - Item: {item_name} (x{count}) - Erreur: {error_msg}")
                
                await ctx.send(f"❌ Impossible de donner l'item **{item_name}**. {error_msg if error_msg else ''}")
        except Exception as e:
            # 📝 LOG DE L'ERREUR GÉNÉRALE
            log_error("BUY_COMMAND", f"Erreur commande !buy pour {ctx.author.display_name} - ID: {id_item_shop} - Erreur: {str(e)}")
            
            await ctx.send(f"❌ Erreur lors de l'achat : {e}")

async def setup(bot):
    await bot.add_cog(Buy(bot))
