import asyncio
import os
import sys
import logging

# Configurar codificación UTF-8 para consola de Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import discord
from discord.ext import commands
from discord import app_commands
import config

# Configuración básica de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DiscordBot")

# Configuración de Intents requeridos (NO requiere Privileged Members Intent)
intents = discord.Intents.default()
intents.message_content = True   # Para leer comandos de prefijo como !quien
intents.voice_states = True      # INDISPENSABLE: Para detectar quién entra y sale de voz
intents.guilds = True

class MultiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.COMMAND_PREFIX),
            intents=intents,
            help_command=None  # Usaremos nuestro propio sistema de ayuda personalizado
        )

    async def setup_hook(self):
        """Carga automáticamente todos los Cogs de la carpeta 'cogs'."""
        cogs_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                extension = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(extension)
                    logger.info(f"✅ Módulo cargado con éxito: {extension}")
                except Exception as e:
                    logger.error(f"❌ Error al cargar módulo {extension}: {e}", exc_info=True)

    async def on_ready(self):
        """Evento al conectarse a Discord."""
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"los canales de voz | {config.COMMAND_PREFIX}quien"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

        # Sincronizar comandos Slash en cada servidor conectado de forma instantánea
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"⚡ Sincronizados {len(synced)} comandos Slash en: {guild.name}")
            except Exception as e:
                logger.warning(f"No se pudieron sincronizar comandos en {guild.name}: {e}")

        logger.info(f"🤖 Bot iniciado como: {self.user} (ID: {self.user.id})")
        logger.info(f"🌐 Servidores conectados: {len(self.guilds)}")
        logger.info(f"📡 Latencia: {round(self.latency * 1000)}ms")
        logger.info(f"⌨️  Prefijo: {config.COMMAND_PREFIX} o Slash Commands (/)")

bot = MultiBot()

import aiohttp
import urllib.parse
import re
from typing import Optional

async def responder_consulta(consulta: str) -> discord.Embed:
    """Procesa y responde preguntas generales, de cultura o de comandos del bot."""
    q = consulta.strip()
    q_norm = re.sub(r'[^a-záéíóúüñ0-9 ]', '', q.lower())

    # 1. Caso especial: Países de Latinoamérica
    if any(k in q_norm for k in ["latinoamerica", "latino america", "america latina"]) and any(w in q_norm for w in ["paises", "pais", "cuantos", "cuales", "lista", "son"]):
        embed = discord.Embed(
            title="🌎 Países de América Latina",
            description=(
                "América Latina está conformada por **20 países soberanos**:\n\n"
                "1. 🇦🇷 **Argentina**\n"
                "2. 🇧🇴 **Bolivia**\n"
                "3. 🇧🇷 **Brasil** *(portugués)*\n"
                "4. 🇨🇱 **Chile**\n"
                "5. 🇨🇴 **Colombia**\n"
                "6. 🇨🇷 **Costa Rica**\n"
                "7. 🇨🇺 **Cuba**\n"
                "8. 🇪🇨 **Ecuador**\n"
                "9. 🇸🇻 **El Salvador**\n"
                "10. 🇬🇹 **Guatemala**\n"
                "11. 🇭🇹 **Haití** *(francés y criollo)*\n"
                "12. 🇭🇳 **Honduras**\n"
                "13. 🇲🇽 **México**\n"
                "14. 🇳🇮 **Nicaragua**\n"
                "15. 🇵🇦 **Panamá**\n"
                "16. 🇵🇾 **Paraguay**\n"
                "17. 🇵🇪 **Perú**\n"
                "18. 🇩🇴 **República Dominicana**\n"
                "19. 🇺🇾 **Uruguay**\n"
                "20. 🇻🇪 **Venezuela**\n\n"
                "📌 **Territorios y dependencias asociadas:**\n"
                "También incluye dependencias como **Puerto Rico** 🇵🇷 *(Estado Libre Asociado a EE.UU.)*, **Guayana Francesa** 🇬🇫, Guadalupe y Martinica."
            ),
            color=config.COLOR_DEFAULT
        )
        embed.set_footer(text=f"Consulta: {q}")
        return embed

    # 2. Dudas sobre comandos del bot (solo si se pregunta específicamente por los comandos)
    comandos_bot = ["quien entro", "quien salio", "comando quien", "comando radar", "comando fantasma", "como uso el bot", "como funciona", "que comandos hay"]
    if q_norm in ["quien", "!quien", "/quien", "radar", "fantasma", "ruleta", "equipos"] or any(k in q_norm for k in comandos_bot):
        embed = discord.Embed(
            title="🎙️ Ayuda: Rastreador de Voz",
            description=(
                "• **`/quien`** o **`!quien`**: Revisa automáticamente tu canal de voz actual, "
                "muestra quién está conectado y etiqueta a los que entraron o salieron con sus tiempos.\n"
                "• **`/fantasma`** o **`!fantasma`**: Filtra a los que entraron y salieron en menos de 30 segundos (ninjas).\n"
                "• **`/historial_voz`**: Muestra todo el registro cronológico del servidor."
            ),
            color=config.COLOR_VOICE
        )
        return embed

    # 3. Consulta con Gemini AI (si hay clave en .env)
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        system_text = (
            "Eres el asistente inteligente oficial de un servidor de Discord. Responde con máxima exactitud y veracidad en español.\n"
            "DIRECTIVAS ESTRICTAS DE PRECISIÓN:\n"
            "1. CERO ALUCINACIONES: Si no estás 100% seguro de un dato, di honestamente 'No dispongo de información confirmada sobre este tema' en lugar de inventar o especular.\n"
            "2. INFORMACIÓN EN TIEMPO REAL: Si la pregunta requiere datos actuales (noticias, fechas, resultados deportivos, cotizaciones o clima), utiliza la búsqueda web de Google para verificar los datos más recientes antes de responder.\n"
            "3. FORMATO DISCORD: Responde de forma clara, directa y agradable, utilizando negritas y viñetas de Markdown en 1 a 3 párrafos concisos."
        )

        model_name = "gemini-2.0-flash"
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"

        # Payload con System Prompt y Búsqueda en Google (Grounding)
        payload_with_search = {
            "system_instruction": {
                "parts": [{"text": system_text}]
            },
            "contents": [
                {"parts": [{"text": q}]}
            ],
            "tools": [
                {"google_search": {}}
            ]
        }

        # Payload alternativo sin search tool por si el modelo o la clave no tienen grounding activado
        payload_basic = {
            "system_instruction": {
                "parts": [{"text": system_text}]
            },
            "contents": [
                {"parts": [{"text": q}]}
            ]
        }

        async with aiohttp.ClientSession() as session:
            try:
                # Intento 1: Con Búsqueda Web de Google en tiempo real
                async with session.post(api_url, json=payload_with_search, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            text = "".join([p.get("text", "") for p in parts]).strip()
                            if text:
                                if len(text) > 4000:
                                    text = text[:3990] + "..."
                                embed = discord.Embed(
                                    title=f"💡 {q[:100]}",
                                    description=text,
                                    color=config.COLOR_DEFAULT
                                )
                                embed.set_footer(text="Google Gemini AI + Búsqueda en Vivo 🌐")
                                return embed
                    else:
                        logger.warning(f"Gemini grounding respondió con status {resp.status}. Intentando payload básico...")
            except Exception as e:
                logger.warning(f"Error en Gemini grounding: {e}. Reintentando con consulta estándar...")

            # Intento 2: Consulta directa sin tool si falló la búsqueda en vivo
            try:
                async with session.post(api_url, json=payload_basic, timeout=aiohttp.ClientTimeout(total=8)) as resp2:
                    if resp2.status == 200:
                        data2 = await resp2.json()
                        candidates2 = data2.get("candidates", [])
                        if candidates2 and "content" in candidates2[0]:
                            parts2 = candidates2[0]["content"].get("parts", [])
                            text2 = "".join([p.get("text", "") for p in parts2]).strip()
                            if text2:
                                if len(text2) > 4000:
                                    text2 = text2[:3990] + "..."
                                embed = discord.Embed(
                                    title=f"💡 {q[:100]}",
                                    description=text2,
                                    color=config.COLOR_DEFAULT
                                )
                                embed.set_footer(text="Google Gemini AI 🧠")
                                return embed
            except Exception as e:
                logger.error(f"Error al conectar con Gemini: {e}")

    # 4. Búsqueda y resumen de Wikipedia en Español
    try:
        headers = {'User-Agent': 'DiscordBot/1.0 (contacto: radarbot@discord.com)'}
        async with aiohttp.ClientSession(headers=headers) as session:
            search_url = 'https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch=' + urllib.parse.quote(q) + '&utf8=1&format=json'
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('query', {}).get('search', [])
                    if results:
                        title = results[0]['title']
                        sum_url = 'https://es.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title.replace(' ', '_'))
                        async with session.get(sum_url, timeout=aiohttp.ClientTimeout(total=5)) as resp2:
                            if resp2.status == 200:
                                sum_data = await resp2.json()
                                extract = sum_data.get('extract')
                                if extract:
                                    page_url = sum_data.get('content_urls', {}).get('desktop', {}).get('page', '')
                                    embed = discord.Embed(
                                        title=f"📚 {title}",
                                        description=f"{extract}\n\n[Leer más en Wikipedia]({page_url})" if page_url else extract,
                                        color=config.COLOR_DEFAULT
                                    )
                                    embed.set_footer(text=f"Consulta: {q}")
                                    return embed
    except Exception as e:
        logger.error(f"Error en consulta de Wikipedia: {e}")

    # 5. Respuesta por defecto
    embed = discord.Embed(
        title="❓ Consulta no encontrada",
        description=(
            f"No encontré una respuesta directa para: *'{q}'*.\n\n"
            "💡 **Tip:** Puedes escribir `/ayuda` sin parámetros para ver todos los comandos del bot."
        ),
        color=config.COLOR_WARNING
    )
    return embed

# ==========================================
# COMANDO DE PREGUNTA Y CONSULTAS
# ==========================================
@bot.hybrid_command(
    name="pregunta",
    aliases=["preguntar", "consulta", "consultar", "ask"],
    description="Responde preguntas de cultura general o geografía (ej: 'cuantos son los paises de latino america')."
)
@app_commands.describe(
    consulta="Escribe tu pregunta o duda (ej: 'cuantos son los paises de latino america')"
)
async def pregunta(ctx: commands.Context, *, consulta: str):
    """Responde preguntas directamente con información detallada."""
    await ctx.defer()
    embed = await responder_consulta(consulta)
    await ctx.reply(embed=embed)

# ==========================================
# COMANDO DE AYUDA
# ==========================================
@bot.hybrid_command(
    name="ayuda",
    aliases=["help", "comandos"],
    description="Muestra la lista de todos los comandos y funciones disponibles."
)
@app_commands.describe(
    consulta="Pregunta opcional (si la pones, te responderá la duda directamente)"
)
async def ayuda(ctx: commands.Context, *, consulta: Optional[str] = None):
    """Despliega el menú con todos los comandos o responde una consulta si se proporciona."""
    if consulta:
        await ctx.defer()
        embed = await responder_consulta(consulta)
        await ctx.reply(embed=embed)
        return

    prefix = config.COMMAND_PREFIX
    embed = discord.Embed(
        title="🤖 Menú de Ayuda y Funciones del Bot",
        description=(
            f"Puedes usar estos comandos con prefijo (`{prefix}comando`) o con barra diagonal (`/comando`).\n"
            f"Preguntas directas: **`{prefix}pregunta cuantos son los paises de latino america`**"
        ),
        color=config.COLOR_DEFAULT
    )

    # 1. Tracker de Voz
    embed.add_field(
        name="🎙️ Rastreador de Voz (Detector de Entradas/Salidas)",
        value=(
            f"• `{prefix}quien` o `/quien`: **Etiqueta a quiénes entraron y salieron** de tu canal de voz.\n"
            f"• `{prefix}fantasma` o `/fantasma`: **Detector de ninja/fantasmas** (los que entraron y salieron en menos de 30s).\n"
            f"• `{prefix}historial_voz` o `/historial_voz`: Historial completo de movimientos de voz.\n"
            f"• `{prefix}set_canal_logs #canal`: Configura un canal para alertas automáticas en tiempo real."
        ),
        inline=False
    )

    # 2. Herramientas de Voz
    embed.add_field(
        name="🎮 Dinámicas de Canal de Voz",
        value=(
            f"• `{prefix}ruleta`: Sortea al azar a uno de los miembros de tu canal de voz.\n"
            f"• `{prefix}equipos [cant]`: Divide a todos los de tu canal de voz en equipos equilibrados al azar.\n"
            f"• `{prefix}mutear_canal` / `{prefix}desmutear_canal`: Silencia o reactiva el micrófono de todos en el canal."
        ),
        inline=False
    )

    # 3. Utilidad
    embed.add_field(
        name="📊 Utilidad & Servidor",
        value=(
            f"• `{prefix}pregunta [texto]`: Responde preguntas y dudas (ej: países de Latinoamérica).\n"
            f"• `{prefix}ping`: Muestra la latencia del bot.\n"
            f"• `{prefix}userinfo [@usuario]`: Información detallada, fechas y roles.\n"
            f"• `{prefix}serverinfo`: Estadísticas completas del servidor.\n"
            f"• `{prefix}avatar [@usuario]`: Muestra y descarga el avatar en alta definición."
        ),
        inline=False
    )

    # 4. Moderación
    embed.add_field(
        name="🛡️ Moderación (Requiere Permisos)",
        value=(
            f"• `{prefix}limpiar [1-100]`: Borra mensajes recientes en el canal.\n"
            f"• `{prefix}expulsar [@usuario] [razon]`: Expulsa a un miembro.\n"
            f"• `{prefix}banear [@usuario] [razon]`: Banea a un miembro.\n"
            f"• `{prefix}aislar [@usuario] [minutos]`: Aplica timeout temporal."
        ),
        inline=False
    )

    # 5. Diversión
    embed.add_field(
        name="🎲 Juegos & Azar",
        value=(
            f"• `{prefix}8ball [pregunta]`: Consulta a la bola 8 mágica.\n"
            f"• `{prefix}dado [caras]`: Lanza un dado aleatorio.\n"
            f"• `{prefix}moneda`: Lanza una moneda al aire (cara o cruz)."
        ),
        inline=False
    )

    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    await ctx.reply(embed=embed)

# ==========================================
# COMANDO PARA FORZAR SYNC DE SLASH COMMANDS
# ==========================================
@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context):
    """Comando para sincronizar comandos de barra en el servidor actual al instante."""
    try:
        ctx.bot.tree.copy_global_to(guild=ctx.guild)
        synced = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.reply(f"⚡ Sincronizados `{len(synced)}` comandos en este servidor.")
    except Exception as e:
        await ctx.reply(f"❌ Error al sincronizar: {e}")

# ==========================================
# MANEJO GLOBAL DE ERRORES
# ==========================================
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return  # Ignorar comandos no reconocidos
    elif isinstance(error, commands.MissingPermissions):
        perms = ", ".join(error.missing_permissions)
        await ctx.reply(f"⛔ No tienes permisos suficientes para usar este comando: `{perms}`", ephemeral=True)
    elif isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(error.missing_permissions)
        await ctx.reply(f"⚠️ El bot no tiene los permisos necesarios en este servidor o canal: `{perms}`", ephemeral=True)
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(f"❓ Parámetro incorrecto: {error}", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"❓ Falta un argumento obligatorio: `{error.param.name}`", ephemeral=True)
    else:
        logger.error(f"Error no controlado en el comando '{ctx.command}': {error}", exc_info=True)
        try:
            await ctx.reply(f"⚠️ Ocurrió un error inesperado al procesar el comando.", ephemeral=True)
        except Exception:
            pass

# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================
def main():
    token = config.DISCORD_TOKEN.strip()
    if not token or token == "TU_TOKEN_AQUI":
        print("\n" + "!"*60)
        print("❌ ERROR: No se ha configurado el DISCORD_TOKEN.")
        print("Por favor, abre el archivo '.env' y coloca el token de tu bot:")
        print("DISCORD_TOKEN=tu_token_aqui")
        print("!"*60 + "\n")
        sys.exit(1)

    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print("\n" + "!"*60)
        print("❌ ERROR: El token proporcionado en '.env' es inválido.")
        print("Revisa que hayas copiado el Token correctamente desde Discord Developer Portal.")
        print("!"*60 + "\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Bot detenido por el usuario.")

if __name__ == "__main__":
    main()
