import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from typing import Optional
import config

class Moderation(commands.Cog):
    """Comandos esenciales de moderación y administración del servidor."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="limpiar",
        aliases=["clear", "purge", "borrar"],
        description="Borra una cantidad específica de mensajes recientes en el canal actual."
    )
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(cantidad="Número de mensajes a eliminar (entre 1 y 100)")
    async def limpiar(self, ctx: commands.Context, cantidad: int):
        """Elimina mensajes en lote."""
        if cantidad < 1 or cantidad > 100:
            await ctx.reply("❌ Puedes borrar entre 1 y 100 mensajes a la vez.", ephemeral=True)
            return

        # Para comandos de texto tradicionales se debe considerar el mensaje del comando
        purge_limit = cantidad if ctx.interaction else cantidad + 1
        deleted = await ctx.channel.purge(limit=purge_limit)
        count = len(deleted) if ctx.interaction else len(deleted) - 1

        msg = await ctx.send(f"🧹 Se han eliminado **{count}** mensajes.")
        await msg.delete(delay=4)

    @commands.hybrid_command(
        name="expulsar",
        aliases=["kick"],
        description="Expulsa a un miembro del servidor."
    )
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(
        miembro="El miembro que deseas expulsar",
        razon="Motivo de la expulsión"
    )
    async def expulsar(self, ctx: commands.Context, miembro: discord.Member, razon: Optional[str] = "No especificada"):
        """Expulsa a un miembro."""
        if miembro.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.reply("❌ No puedes expulsar a alguien con un rol igual o superior al tuyo.", ephemeral=True)
            return

        try:
            await miembro.kick(reason=f"Por {ctx.author}: {razon}")
            embed = discord.Embed(
                title="👢 Miembro Expulsado",
                description=f"{miembro.mention} (`{miembro.display_name}`) fue expulsado.\n**Razón:** {razon}",
                color=config.COLOR_WARNING
            )
            await ctx.reply(embed=embed)
        except discord.Forbidden:
            await ctx.reply("❌ No tengo permisos suficientes para expulsar a ese usuario.", ephemeral=True)

    @commands.hybrid_command(
        name="banear",
        aliases=["ban"],
        description="Banea permanentemente a un usuario del servidor."
    )
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        usuario="El miembro a banear",
        razon="Motivo del baneo"
    )
    async def banear(self, ctx: commands.Context, usuario: discord.Member, razon: Optional[str] = "No especificada"):
        """Banea a un usuario."""
        if usuario.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.reply("❌ No puedes banear a alguien con un rol igual o superior al tuyo.", ephemeral=True)
            return

        try:
            await usuario.ban(reason=f"Por {ctx.author}: {razon}", delete_message_days=0)
            embed = discord.Embed(
                title="🔨 Usuario Baneado",
                description=f"{usuario.mention} (`{usuario.display_name}`) ha sido baneado.\n**Razón:** {razon}",
                color=config.COLOR_ERROR
            )
            await ctx.reply(embed=embed)
        except discord.Forbidden:
            await ctx.reply("❌ No tengo permisos suficientes para banear a ese usuario.", ephemeral=True)

    @commands.hybrid_command(
        name="aislar",
        aliases=["timeout", "mutear"],
        description="Aplica un aislamiento temporal (timeout) a un usuario."
    )
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        miembro="El miembro a aislar",
        minutos="Minutos de duración del aislamiento",
        razon="Motivo del aislamiento"
    )
    async def aislar(self, ctx: commands.Context, miembro: discord.Member, minutos: int, razon: Optional[str] = "No especificada"):
        """Aplica timeout a un miembro."""
        if miembro.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            await ctx.reply("❌ No puedes aislar a alguien con un rol igual o superior al tuyo.", ephemeral=True)
            return

        if minutos < 1 or minutos > 40320:  # Max 28 días según Discord API
            await ctx.reply("❌ La duración debe ser entre 1 minuto y 28 días (40320 minutos).", ephemeral=True)
            return

        try:
            duration = timedelta(minutes=minutos)
            await miembro.timeout(duration, reason=f"Por {ctx.author}: {razon}")
            embed = discord.Embed(
                title="⏳ Usuario Aislado (Timeout)",
                description=f"{miembro.mention} fue aislado durante **{minutos} minutos**.\n**Razón:** {razon}",
                color=config.COLOR_WARNING
            )
            await ctx.reply(embed=embed)
        except discord.Forbidden:
            await ctx.reply("❌ No tengo permisos suficientes para aislar a ese usuario.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
