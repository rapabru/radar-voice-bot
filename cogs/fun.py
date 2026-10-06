import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional
import config

RESPUESTAS_8BALL = [
    # Positivas
    "En mi opinión, sí.",
    "Es decididamente así.",
    "Sin duda alguna.",
    "Sí, definitivamente.",
    "Puedes confiar en ello.",
    "Como yo lo veo, sí.",
    "Muy probablemente.",
    "Perspectiva buena.",
    "Todo apunta a que sí.",
    # Neutrales
    "Respuesta vaga, vuelve a intentar.",
    "Pregunta de nuevo más tarde.",
    "Mejor no decirte ahora.",
    "No se puede predecir ahora.",
    "Concéntrate y pregunta de nuevo.",
    # Negativas
    "No cuentes con ello.",
    "Mi respuesta es no.",
    "Mis fuentes dicen que no.",
    "Las perspectivas no son muy buenas.",
    "Muy dudoso."
]

class Fun(commands.Cog):
    """Comandos divertidos y juegos rápidos para la comunidad."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="8ball",
        aliases=["bola8", "pregunta"],
        description="Hazle una pregunta a la bola mágica 8."
    )
    @app_commands.describe(pregunta="¿Qué quieres consultar a la bola mágica?")
    async def eight_ball(self, ctx: commands.Context, *, pregunta: str):
        """Responde con el destino de la bola 8."""
        respuesta = random.choice(RESPUESTAS_8BALL)
        embed = discord.Embed(
            title="🎱 La Bola Mágica 8",
            color=0x2B2D31
        )
        embed.add_field(name="❓ Pregunta", value=pregunta, inline=False)
        embed.add_field(name="🔮 Respuesta", value=f"**{respuesta}**", inline=False)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="dado",
        aliases=["roll", "tirardado"],
        description="Tira un dado con el número de caras que elijas."
    )
    @app_commands.describe(caras="Número de caras del dado (por defecto 6)")
    async def dado(self, ctx: commands.Context, caras: int = 6):
        """Lanza un dado aleatorio."""
        if caras < 2 or caras > 1000:
            await ctx.reply("❌ El dado debe tener entre 2 y 1000 caras.", ephemeral=True)
            return

        resultado = random.randint(1, caras)
        embed = discord.Embed(
            title="🎲 Lanzamiento de Dado",
            description=f"🎲 Has lanzado un dado de **{caras}** caras y ha salido: **{resultado}**!",
            color=config.COLOR_DEFAULT
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="moneda",
        aliases=["flip", "caracruz"],
        description="Lanza una moneda al aire (Cara o Cruz)."
    )
    async def moneda(self, ctx: commands.Context):
        """Cara o Cruz."""
        resultado = random.choice(["Cara 🪙", "Cruz 🪙"])
        embed = discord.Embed(
            title="🪙 Cara o Cruz",
            description=f"La moneda giró en el aire y cayó en... ¡**{resultado}**!",
            color=config.COLOR_WARNING
        )
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
