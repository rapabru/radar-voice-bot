import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Token del bot
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# Prefijo predeterminado para comandos de texto tradicionales
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# Colores estéticos para los mensajes Embed
COLOR_DEFAULT = 0x5865F2      # Azul Blurple de Discord
COLOR_SUCCESS = 0x57F287      # Verde éxito
COLOR_WARNING = 0xFEE75C      # Amarillo advertencia
COLOR_ERROR = 0xED4245        # Rojo error
COLOR_VOICE = 0xEB459E        # Fucsia/Rosa para eventos de voz

# Umbral en segundos para considerar a alguien un "Fantasma" (entró y salió de inmediato)
GHOST_THRESHOLD_SECONDS = int(os.getenv("GHOST_THRESHOLD_SECONDS", "30"))
