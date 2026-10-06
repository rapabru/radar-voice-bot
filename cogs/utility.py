import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime, timezone
import config

class Utility(commands.Cog):
    """Comandos de utilidad, estadísticas e información del servidor y usuarios."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        aliases=["latencia"],
        description="Comprueba la latencia del bot con los servidores de Discord."
    )
    async def ping(self, ctx: commands.Context):
        """Muestra el tiempo de respuesta."""
        latency_ms = round(self.bot.latency * 1000)
        color = config.COLOR_SUCCESS if latency_ms < 150 else config.COLOR_WARNING
        embed = discord.Embed(
            title="🏓 ¡Pong!",
            description=f"Latencia de la API: **{latency_ms} ms**",
            color=color
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="userinfo",
        aliases=["perfil", "usuario"],
        description="Muestra información detallada sobre un usuario del servidor."
    )
    @app_commands.describe(usuario="El miembro a consultar (por defecto tú mismo)")
    async def userinfo(self, ctx: commands.Context, usuario: Optional[discord.Member] = None):
        """Obtiene datos como fecha de creación, roles y estado de voz."""
        member = usuario or ctx.author

        created_ts = int(member.created_at.timestamp())
        joined_ts = int(member.joined_at.timestamp()) if member.joined_at else 0

        roles = [r.mention for r in reversed(member.roles) if r.name != "@everyone"]
        roles_str = ", ".join(roles[:10]) if roles else "Ninguno"
        if len(roles) > 10:
            roles_str += f" y {len(roles) - 10} más..."

        voice_info = "Desconectado"
        if member.voice and member.voice.channel:
            voice_info = f"🔊 En **{member.voice.channel.name}**"

        embed = discord.Embed(
            title=f"👤 Información de {member.display_name}",
            color=member.color if member.color.value != 0 else config.COLOR_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Nombre / Tag", value=f"`{member}`", inline=True)
        embed.add_field(name="ID de Discord", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Estado de Voz", value=voice_info, inline=True)

        embed.add_field(name="Cuenta Creada", value=f"<t:{created_ts}:D> (<t:{created_ts}:R>)", inline=False)
        embed.add_field(name="Se Unió al Servidor", value=f"<t:{joined_ts}:D> (<t:{joined_ts}:R>)", inline=False)
        embed.add_field(name=f"Roles [{len(member.roles) - 1}]", value=roles_str, inline=False)

        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        aliases=["servidor", "server"],
        description="Muestra estadísticas e información general del servidor."
    )
    async def serverinfo(self, ctx: commands.Context):
        """Muestra estadísticas del servidor actual."""
        guild = ctx.guild
        created_ts = int(guild.created_at.timestamp())

        total_members = guild.member_count
        voice_channels = len(guild.voice_channels)
        text_channels = len(guild.text_channels)
        categories = len(guild.categories)
        roles_count = len(guild.roles)

        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            color=config.COLOR_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Propietario", value=f"{guild.owner.mention if guild.owner else 'Desconocido'}", inline=True)
        embed.add_field(name="🆔 ID Servidor", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="📅 Creado el", value=f"<t:{created_ts}:D>", inline=True)

        embed.add_field(name="👥 Miembros", value=f"**{total_members}**", inline=True)
        embed.add_field(name="💬 Canales de Texto", value=f"**{text_channels}**", inline=True)
        embed.add_field(name="🔊 Canales de Voz", value=f"**{voice_channels}**", inline=True)
        embed.add_field(name="📁 Categorías", value=f"**{categories}**", inline=True)
        embed.add_field(name="🏷️ Roles", value=f"**{roles_count}**", inline=True)
        embed.add_field(name="🛡️ Nivel de Verificación", value=f"`{guild.verification_level}`", inline=True)

        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="avatar",
        aliases=["foto", "pfp"],
        description="Muestra y da el enlace del avatar de un usuario en alta resolución."
    )
    @app_commands.describe(usuario="El miembro cuyo avatar deseas ver (por defecto el tuyo)")
    async def avatar(self, ctx: commands.Context, usuario: Optional[discord.Member] = None):
        """Muestra el avatar del usuario seleccionado."""
        member = usuario or ctx.author
        avatar_url = member.display_avatar.with_size(1024).url

        embed = discord.Embed(
            title=f"🖼️ Avatar de {member.display_name}",
            color=config.COLOR_DEFAULT
        )
        embed.set_image(url=avatar_url)
        embed.description = f"[Haz clic aquí para ver en tamaño original]({avatar_url})"
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
