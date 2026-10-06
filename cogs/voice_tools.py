import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional
import config

class VoiceTools(commands.Cog):
    """Herramientas y dinámicas interactivas para canales de voz."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ruleta",
        aliases=["ruletavoz", "elegir_uno"],
        description="Elige a un miembro al azar entre todos los conectados en tu canal de voz."
    )
    async def ruleta(self, ctx: commands.Context):
        """Sortea a un participante del canal de voz actual."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ Debes estar conectado a un canal de voz para usar la ruleta.", ephemeral=True)
            return

        channel = ctx.author.voice.channel
        # Filtrar bots si hay
        members = [m for m in channel.members if not m.bot]

        if not members:
            await ctx.reply("⚠️ No hay personas reales en tu canal de voz.", ephemeral=True)
            return

        chosen = random.choice(members)
        embed = discord.Embed(
            title="🎯 ¡La Ruleta de Voz ha decidido!",
            description=f"Canal: **{channel.name}**\nParticipantes: `{len(members)}`\n\n🏆 El elegido es: {chosen.mention} (`{chosen.display_name}`)!",
            color=config.COLOR_VOICE
        )
        embed.set_thumbnail(url=chosen.display_avatar.url)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="equipos",
        aliases=["sortearequipos", "teams"],
        description="Divide a todos los miembros de tu canal de voz en equipos equilibrados al azar."
    )
    @app_commands.describe(numero_equipos="Cantidad de equipos a crear (por defecto 2)")
    async def equipos(self, ctx: commands.Context, numero_equipos: int = 2):
        """Crea equipos al azar con los usuarios de tu canal de voz actual."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ Debes estar conectado a un canal de voz para crear equipos.", ephemeral=True)
            return

        if numero_equipos < 2 or numero_equipos > 10:
            await ctx.reply("❌ El número de equipos debe ser entre 2 y 10.", ephemeral=True)
            return

        channel = ctx.author.voice.channel
        members = [m for m in channel.members if not m.bot]

        if len(members) < numero_equipos:
            await ctx.reply(
                f"❌ Hay `{len(members)}` miembros en el canal, no se pueden dividir en `{numero_equipos}` equipos.",
                ephemeral=True
            )
            return

        random.shuffle(members)
        teams = [[] for _ in range(numero_equipos)]
        for i, member in enumerate(members):
            teams[i % numero_equipos].append(member)

        embed = discord.Embed(
            title="⚔️ Equipos Generados al Azar",
            description=f"Canal de origen: **{channel.name}** | Total participantes: `{len(members)}`",
            color=config.COLOR_DEFAULT
        )

        emojis = ["🔴", "🔵", "🟢", "🟡", "🟣", "🟠", "🟤", "⚪", "🔥", "⚡"]
        for idx, team in enumerate(teams):
            emoji = emojis[idx % len(emojis)]
            team_members_str = "\n".join([f"• {m.mention} (`{m.display_name}`)" for m in team])
            embed.add_field(
                name=f"{emoji} Equipo {idx + 1} ({len(team)} miembros)",
                value=team_members_str,
                inline=False
            )

        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="mutear_canal",
        aliases=["muteall", "silenciartodos"],
        description="Mutea a todos los miembros de tu canal de voz (útil para juegos de votación o reuniones)."
    )
    @commands.has_permissions(mute_members=True)
    async def mutear_canal(self, ctx: commands.Context):
        """Silencia el micrófono de todos en el canal actual."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ Debes estar conectado a un canal de voz.", ephemeral=True)
            return

        channel = ctx.author.voice.channel
        muted_count = 0
        for member in channel.members:
            if not member.bot and not member.voice.mute:
                try:
                    await member.edit(mute=True, reason=f"Mutear canal por {ctx.author.name}")
                    muted_count += 1
                except Exception:
                    pass

        await ctx.reply(f"🔇 Se silenciaron `{muted_count}` miembros en **{channel.name}**.")

    @commands.hybrid_command(
        name="desmutear_canal",
        aliases=["unmuteall", "desilenciartodos"],
        description="Desilencia a todos los miembros de tu canal de voz."
    )
    @commands.has_permissions(mute_members=True)
    async def desmutear_canal(self, ctx: commands.Context):
        """Desmutea el micrófono de todos en el canal actual."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ Debes estar conectado a un canal de voz.", ephemeral=True)
            return

        channel = ctx.author.voice.channel
        unmuted_count = 0
        for member in channel.members:
            if not member.bot and member.voice.mute:
                try:
                    await member.edit(mute=False, reason=f"Desmutear canal por {ctx.author.name}")
                    unmuted_count += 1
                except Exception:
                    pass

        await ctx.reply(f"🔊 Se desilenciaron `{unmuted_count}` miembros en **{channel.name}**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceTools(bot))
