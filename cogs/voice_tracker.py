import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from collections import deque
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
import config

@dataclass
class VoiceEvent:
    member_id: int
    member_name: str
    member_display_name: str
    channel_id: int
    channel_name: str
    event_type: str  # "join", "leave", "switch_from", "switch_to"
    timestamp: datetime
    duration_seconds: Optional[float] = None
    target_channel_name: Optional[str] = None

    @property
    def is_ghost(self) -> bool:
        """Indica si el usuario estuvo menos tiempo que el umbral configurado."""
        return self.duration_seconds is not None and self.duration_seconds <= config.GHOST_THRESHOLD_SECONDS

    def format_duration(self) -> str:
        if self.duration_seconds is None:
            return "N/A"
        secs = int(self.duration_seconds)
        if secs < 60:
            return f"{secs}s"
        mins = secs // 60
        rem_secs = secs % 60
        if mins < 60:
            return f"{mins}m {rem_secs}s"
        hours = mins // 60
        rem_mins = mins % 60
        return f"{hours}h {rem_mins}m {rem_secs}s"


class VoiceTracker(commands.Cog):
    """Cog para rastrear conexiones, desconexiones y 'fantasmas' en canales de voz."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Estructura: guild_id -> { channel_id -> deque([VoiceEvent, ...]) }
        self.channel_history: Dict[int, Dict[int, deque]] = {}
        # Estructura: guild_id -> deque([VoiceEvent, ...]) (historial global del servidor)
        self.guild_history: Dict[int, deque] = {}
        # Registro de sesiones activas: (guild_id, member_id) -> (join_time, channel_id, channel_name)
        self.active_sessions: Dict[Tuple[int, int], Tuple[datetime, int, str]] = {}
        # Canales de texto para notificaciones automáticas opcionales: guild_id -> text_channel_id
        self.log_channels: Dict[int, int] = {}
        self.logging_enabled: Dict[int, bool] = {}

    def _get_channel_deque(self, guild_id: int, channel_id: int) -> deque:
        if guild_id not in self.channel_history:
            self.channel_history[guild_id] = {}
        if channel_id not in self.channel_history[guild_id]:
            self.channel_history[guild_id][channel_id] = deque(maxlen=60)
        return self.channel_history[guild_id][channel_id]

    def _get_guild_deque(self, guild_id: int) -> deque:
        if guild_id not in self.guild_history:
            self.guild_history[guild_id] = deque(maxlen=150)
        return self.guild_history[guild_id]

    def _record_event(self, event: VoiceEvent, guild_id: int):
        # Guardar en el canal específico
        ch_deque = self._get_channel_deque(guild_id, event.channel_id)
        ch_deque.appendleft(event)
        # Guardar en el historial general del servidor
        g_deque = self._get_guild_deque(guild_id)
        g_deque.appendleft(event)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Monitorea en tiempo real cambios de estado de voz."""
        # Ignorar si no hubo cambio de canal (por ejemplo si solo se muteó/desmuteó)
        if before.channel == after.channel:
            return

        now = datetime.now(timezone.utc)
        guild = member.guild
        session_key = (guild.id, member.id)

        # 1. CASO: DESCONEXIÓN O CAMBIO DE CANAL (El usuario estaba en before.channel)
        if before.channel is not None:
            duration = None
            if session_key in self.active_sessions:
                join_time, prev_channel_id, _ = self.active_sessions.pop(session_key)
                if prev_channel_id == before.channel.id:
                    duration = (now - join_time).total_seconds()

            if after.channel is None:
                # Se desconectó completamente de voz
                event = VoiceEvent(
                    member_id=member.id,
                    member_name=str(member),
                    member_display_name=member.display_name,
                    channel_id=before.channel.id,
                    channel_name=before.channel.name,
                    event_type="leave",
                    timestamp=now,
                    duration_seconds=duration
                )
                self._record_event(event, guild.id)
                await self._notify_log_channel(guild, event, member)
            else:
                # Se cambió a otro canal de voz
                event = VoiceEvent(
                    member_id=member.id,
                    member_name=str(member),
                    member_display_name=member.display_name,
                    channel_id=before.channel.id,
                    channel_name=before.channel.name,
                    event_type="switch_from",
                    timestamp=now,
                    duration_seconds=duration,
                    target_channel_name=after.channel.name
                )
                self._record_event(event, guild.id)

        # 2. CASO: CONEXIÓN O ENTRADA DESDE OTRO CANAL (El usuario ahora está en after.channel)
        if after.channel is not None:
            # Iniciar nueva sesión activa
            self.active_sessions[session_key] = (now, after.channel.id, after.channel.name)

            event_type = "switch_to" if before.channel is not None else "join"
            event = VoiceEvent(
                member_id=member.id,
                member_name=str(member),
                member_display_name=member.display_name,
                channel_id=after.channel.id,
                channel_name=after.channel.name,
                event_type=event_type,
                timestamp=now,
                target_channel_name=before.channel.name if before.channel else None
            )
            self._record_event(event, guild.id)
            if event_type == "join":
                await self._notify_log_channel(guild, event, member)

    async def _notify_log_channel(self, guild: discord.Guild, event: VoiceEvent, member: discord.Member):
        """Envía notificación automática al canal de logs si está activado."""
        if not self.logging_enabled.get(guild.id, False):
            return
        log_channel_id = self.log_channels.get(guild.id)
        if not log_channel_id:
            return
        log_channel = guild.get_channel(log_channel_id)
        if not isinstance(log_channel, discord.TextChannel):
            return

        ts_unix = int(event.timestamp.timestamp())
        if event.event_type == "join":
            embed = discord.Embed(
                title="🟢 Conexión a Canal de Voz",
                description=f"{member.mention} (`{member.display_name}`) entró a **{event.channel_name}** (<t:{ts_unix}:R>).",
                color=config.COLOR_SUCCESS,
                timestamp=event.timestamp
            )
        else:
            dur_str = f" • Permanencia: `{event.format_duration()}`" if event.duration_seconds is not None else ""
            ghost_alert = " ⚠️ **¡Entrada y salida rápida!**" if event.is_ghost else ""
            embed = discord.Embed(
                title="🔴 Desconexión de Canal de Voz",
                description=f"{member.mention} (`{member.display_name}`) salió de **{event.channel_name}** (<t:{ts_unix}:R>).{dur_str}{ghost_alert}",
                color=config.COLOR_ERROR,
                timestamp=event.timestamp
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        try:
            await log_channel.send(embed=embed)
        except Exception:
            pass

    # ==========================================
    # COMANDOS: QUIÉN ENTRÓ / SALIÓ (PRINCIPAL)
    # ==========================================

    @commands.hybrid_command(
        name="quien",
        aliases=["quien_entro", "quien_salio", "radar"],
        description="Muestra y etiqueta a quiénes se conectaron o desconectaron recientemente de tu canal de voz."
    )
    @app_commands.describe(canal="Canal de voz a consultar (por defecto el canal en el que estás actualmente)")
    async def quien(self, ctx: commands.Context, canal: Optional[discord.VoiceChannel] = None):
        """
        Detecta y etiqueta a las personas que entraron o salieron del canal de voz.
        Si estás en un canal de audio, automáticamente revisa ese canal.
        """
        # Determinar el canal objetivo
        target_channel = canal
        if target_channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                target_channel = ctx.author.voice.channel
            else:
                await ctx.reply(
                    "❌ **No estás en ningún canal de voz** ni especificaste uno.\n"
                    "👉 Conéctate a un canal de voz y vuelve a ejecutar `!quien`, o usa `!quien #nombre-del-canal`.",
                    ephemeral=True
                )
                return

        guild_id = ctx.guild.id
        ch_deque = self._get_channel_deque(guild_id, target_channel.id)

        # Obtener miembros actualmente en el canal
        current_members = target_channel.members
        if current_members:
            current_str = ", ".join([f"<@{m.id}>" for m in current_members[:15]])
            if len(current_members) > 15:
                current_str += f" y {len(current_members) - 15} más..."
        else:
            current_str = "*Nadie conectado actualmente*"

        embed = discord.Embed(
            title=f"👁️ Radar de Voz: #{target_channel.name}",
            color=config.COLOR_VOICE,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(
            name=f"👥 En el canal ahora ({len(current_members)})",
            value=current_str,
            inline=False
        )

        if not ch_deque:
            embed.add_field(
                name="📜 Movimientos recientes",
                value="*No hay entradas ni salidas registradas en este canal desde que el bot se inició.*",
                inline=False
            )
            await ctx.reply(embed=embed)
            return

        # Tomar los últimos 10 movimientos
        recent_events = list(ch_deque)[:10]

        lines = []
        for ev in recent_events:
            ts_unix = int(ev.timestamp.timestamp())
            user_tag = f"<@{ev.member_id}>"

            if ev.event_type == "join":
                lines.append(f"🟢 **Entró**: {user_tag} (<t:{ts_unix}:R>)")
            elif ev.event_type == "leave":
                dur = f" • Estuvo: `{ev.format_duration()}`" if ev.duration_seconds is not None else ""
                ghost = " 👻 **¡Entrada y salida relámpago!**" if ev.is_ghost else ""
                lines.append(f"🔴 **Salió**: {user_tag} (<t:{ts_unix}:R>){dur}{ghost}")
            elif ev.event_type == "switch_from":
                lines.append(f"🔀 **Se cambió a** `{ev.target_channel_name}`: {user_tag} (<t:{ts_unix}:R>)")
            elif ev.event_type == "switch_to":
                lines.append(f"🔀 **Llegó desde** `{ev.target_channel_name}`: {user_tag} (<t:{ts_unix}:R>)")

        embed.add_field(
            name=f"📜 Últimos movimientos ({len(recent_events)})",
            value="\n".join(lines),
            inline=False
        )
        embed.set_footer(text=f"Consulta por {ctx.author.display_name} | Usa !fantasma para ver salidas rápidas")
        await ctx.reply(embed=embed)

    # ==========================================
    # COMANDO: DETECTOR DE FANTASMAS (SALIDA RÁPIDA)
    # ==========================================

    @commands.hybrid_command(
        name="fantasma",
        aliases=["ninja", "quienfue"],
        description="Etiqueta específicamente a quienes entraron y salieron de inmediato (menos de 30s)."
    )
    @app_commands.describe(canal="Canal de voz específico a consultar (opcional)")
    async def fantasma(self, ctx: commands.Context, canal: Optional[discord.VoiceChannel] = None):
        """
        Busca a usuarios que entraron y salieron rápidamente (modo fantasma/ninja) y los etiqueta.
        """
        target_channel = canal
        if target_channel is None and ctx.author.voice and ctx.author.voice.channel:
            target_channel = ctx.author.voice.channel

        guild_id = ctx.guild.id
        if target_channel:
            source_events = list(self._get_channel_deque(guild_id, target_channel.id))
            channel_name = target_channel.name
        else:
            source_events = list(self._get_guild_deque(guild_id))
            channel_name = "Todo el Servidor"

        ghosts = [ev for ev in source_events if ev.is_ghost][:10]

        if not ghosts:
            embed = discord.Embed(
                title="👻 Detector de Fantasmas",
                description=f"No se detectaron usuarios que hayan entrado y salido inmediatamente (menos de {config.GHOST_THRESHOLD_SECONDS}s) en **{channel_name}**.",
                color=config.COLOR_SUCCESS
            )
            await ctx.reply(embed=embed)
            return

        lines = []
        for ev in ghosts:
            ts_unix = int(ev.timestamp.timestamp())
            user_tag = f"<@{ev.member_id}>"
            lines.append(
                f"👻 **¡Cazado!** {user_tag} entró a **{ev.channel_name}** y se desconectó a los **{ev.format_duration()}** (<t:{ts_unix}:R>)"
            )

        embed = discord.Embed(
            title=f"👻 Fantasmas Detectados en {channel_name}",
            description="\n".join(lines),
            color=0xFF5555,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Umbral configurado: {config.GHOST_THRESHOLD_SECONDS} segundos")
        await ctx.reply(embed=embed)

    # ==========================================
    # COMANDO: HISTORIAL COMPLETO DE VOZ
    # ==========================================

    @commands.hybrid_command(
        name="historial_voz",
        aliases=["historialvoz", "voicehistory"],
        description="Muestra el historial cronológico completo de actividad de voz en el servidor o canal."
    )
    @app_commands.describe(canal="Canal de voz específico (opcional)")
    async def historial_voz(self, ctx: commands.Context, canal: Optional[discord.VoiceChannel] = None):
        """Muestra una lista detallada con los últimos movimientos de voz."""
        guild_id = ctx.guild.id
        if canal:
            events = list(self._get_channel_deque(guild_id, canal.id))[:15]
            title = f"📜 Historial de Voz: #{canal.name}"
        else:
            events = list(self._get_guild_deque(guild_id))[:15]
            title = "📜 Historial Global de Voz del Servidor"

        if not events:
            await ctx.reply(f"ℹ️ Aún no hay eventos registrados en {title}.", ephemeral=True)
            return

        lines = []
        for ev in events:
            ts_unix = int(ev.timestamp.timestamp())
            user_tag = f"<@{ev.member_id}>"

            if ev.event_type == "join":
                lines.append(f"🟢 {user_tag} se unió a **{ev.channel_name}** (<t:{ts_unix}:R>)")
            elif ev.event_type == "leave":
                dur = f" (estuvo `{ev.format_duration()}`)" if ev.duration_seconds is not None else ""
                lines.append(f"🔴 {user_tag} salió de **{ev.channel_name}**{dur} (<t:{ts_unix}:R>)")
            elif ev.event_type == "switch_from":
                lines.append(f"🔀 {user_tag} pasó de **{ev.channel_name}** ➔ **{ev.target_channel_name}** (<t:{ts_unix}:R>)")

        embed = discord.Embed(
            title=title,
            description="\n".join(lines) if lines else "Sin actividad.",
            color=config.COLOR_DEFAULT,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Mostrando los últimos {len(lines)} registros")
        await ctx.reply(embed=embed)

    # ==========================================
    # COMANDOS DE CONFIGURACIÓN DE LOGS DE VOZ
    # ==========================================

    @commands.hybrid_command(
        name="set_canal_logs",
        aliases=["setlogs"],
        description="Configura un canal de texto para recibir alertas automáticas de voz en tiempo real."
    )
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(canal="Canal de texto donde se enviarán los logs automáticos de voz")
    async def set_canal_logs(self, ctx: commands.Context, canal: discord.TextChannel):
        """Asigna un canal de texto para emitir alertas de entrada y salida de voz automáticamente."""
        self.log_channels[ctx.guild.id] = canal.id
        self.logging_enabled[ctx.guild.id] = True
        await ctx.reply(f"✅ Canal de logs de voz establecido en {canal.mention}. Alertas automáticas activadas!")

    @commands.hybrid_command(
        name="toggle_logs_voz",
        aliases=["togglelogs"],
        description="Activa o desactiva las notificaciones automáticas de voz."
    )
    @commands.has_permissions(manage_guild=True)
    async def toggle_logs_voz(self, ctx: commands.Context):
        """Alterna entre activar o pausar los mensajes automáticos de voz."""
        current = self.logging_enabled.get(ctx.guild.id, False)
        self.logging_enabled[ctx.guild.id] = not current
        estado = "activadas ✅" if not current else "desactivadas ⏸️"
        await ctx.reply(f"🔔 Notificaciones automáticas de voz {estado}.")

    @commands.hybrid_command(
        name="limpiar_historial_voz",
        aliases=["resetvoz"],
        description="Limpia la memoria del registro de voz del servidor."
    )
    @commands.has_permissions(manage_guild=True)
    async def limpiar_historial_voz(self, ctx: commands.Context):
        """Borra todos los registros guardados de voz para este servidor."""
        if ctx.guild.id in self.channel_history:
            self.channel_history[ctx.guild.id].clear()
        if ctx.guild.id in self.guild_history:
            self.guild_history[ctx.guild.id].clear()
        await ctx.reply("🧹 Historial de voz borrado con éxito.")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceTracker(bot))
