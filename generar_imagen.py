import os
import shutil
from PIL import Image, ImageDraw, ImageFont

# Dimensiones y paleta de colores estilo Discord Dark Theme
BG_COLOR = (30, 31, 34)          # #1e1f22
CARD_BG = (43, 45, 49)           # #2b2d31
HEADER_BG = (35, 36, 40)         # #232428
ROW_ALT_BG = (39, 41, 45)        # #27292d
BORDER_COLOR = (54, 57, 63)      # #36393f
PILL_BG = (30, 31, 34)           # #1e1f22
TEXT_WHITE = (242, 243, 245)     # #f2f3f5
TEXT_MUTED = (219, 222, 225)     # #dbdee1
CODE_COLOR = (245, 194, 130)     # Amarillo/naranja de código Discord
HEADER_TEXT = (200, 203, 208)

FONT_TITLE_PATH = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_BODY_PATH = r"C:\Windows\Fonts\segoeui.ttf"
FONT_CODE_PATH = r"C:\Windows\Fonts\consola.ttf"
FONT_EMOJI_PATH = r"C:\Windows\Fonts\seguiemj.ttf"

font_title = ImageFont.truetype(FONT_TITLE_PATH, 22)
font_emoji_title = ImageFont.truetype(FONT_EMOJI_PATH, 20)
font_header = ImageFont.truetype(FONT_TITLE_PATH, 16)
font_body = ImageFont.truetype(FONT_BODY_PATH, 15)
font_code = ImageFont.truetype(FONT_CODE_PATH, 14)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

tables_data = [
    {
        "emoji": "🎮",
        "title": "2. Dinámicas de Canal de Voz",
        "rows": [
            (
                "/ruleta o !ruleta",
                "!ruletavoz, !elegir_uno",
                "Elige a un usuario al azar entre todos los que están conectados en tu canal de voz actual (ideal para ver a quién le toca pagar, elegir juego/mapa, etc.)."
            ),
            (
                "/equipos [cantidad] o !equipos 2",
                "!teams, !sortearequipos",
                "Divide a todos los miembros de tu canal de voz actual en equipos equilibrados y aleatorios (por defecto 2 equipos, ajustable)."
            ),
            (
                "/mutear_canal o !mutear_canal",
                "!muteall, !silenciartodos",
                "Silencia el micrófono de todos los miembros del canal de voz (útil para partidas de Among Us, estudio o avisos)."
            ),
            (
                "/desmutear_canal o !desmutear_canal",
                "!unmuteall, !desilenciartodos",
                "Reactiva el micrófono de todos en el canal de voz."
            )
        ]
    },
    {
        "emoji": "📊",
        "title": "3. Información y Utilidad",
        "rows": [
            (
                "/pregunta [consulta] o !pregunta",
                "!preguntar, !consulta",
                "Responde preguntas de cultura general, geografía o dudas (ej: 'cuántos son los países de Latinoamérica')."
            ),
            (
                "/ping o !ping",
                "!latencia",
                "Muestra la latencia y tiempo de respuesta del bot con Discord en milisegundos."
            ),
            (
                "/userinfo [@usuario] o !userinfo",
                "!perfil, !usuario",
                "Muestra la ficha de un usuario: avatar, fecha de creación de cuenta, cuándo se unió al servidor, roles y si está en algún canal de voz."
            ),
            (
                "/serverinfo o !serverinfo",
                "!servidor, !server",
                "Muestra estadísticas completas del servidor (miembros, canales de voz y texto, dueño, fecha de creación)."
            ),
            (
                "/avatar [@usuario] o !avatar",
                "!foto, !pfp",
                "Muestra y entrega el enlace directo para descargar el avatar en máxima resolución (1024x1024)."
            ),
            (
                "/ayuda o !ayuda",
                "!help, !comandos",
                "Despliega en Discord una ventana visual con todos los comandos y su explicación."
            )
        ]
    }
]

dummy_img = Image.new("RGB", (100, 100))
dummy_draw = ImageDraw.Draw(dummy_img)

COL_CMD_W = 340
COL_ALIAS_W = 270
COL_DESC_W = 550
TABLE_W = COL_CMD_W + COL_ALIAS_W + COL_DESC_W # 1160
IMG_W = TABLE_W + 80 # 1240

# Precalcular alturas de filas
for tbl in tables_data:
    tbl_row_heights = []
    for cmd, alias, desc in tbl["rows"]:
        wrapped_desc = wrap_text(desc, font_body, COL_DESC_W - 30, dummy_draw)
        # Manejar si el alias tiene múltiples líneas
        alias_lines = [a.strip() for a in alias.split(", ")] if (", " in alias and len(alias) > 20) else [alias]
        needed_lines = max(len(wrapped_desc), len(alias_lines))
        h = max(52, needed_lines * 24 + 26)
        tbl_row_heights.append((h, wrapped_desc, alias_lines))
    tbl["row_heights"] = tbl_row_heights

total_h = 50
for tbl in tables_data:
    total_h += 42 # título
    total_h += 44 # header
    for h, _, _ in tbl["row_heights"]:
        total_h += h
    total_h += 38 # espacio entre tablas

img = Image.new("RGB", (IMG_W, total_h), BG_COLOR)
draw = ImageDraw.Draw(img)

curr_y = 35

for tbl in tables_data:
    # Dibujar emoji de sección
    draw.text((40, curr_y + 1), tbl["emoji"], font=font_emoji_title, embedded_color=True)
    # Dibujar título de sección
    draw.text((72, curr_y), tbl["title"], font=font_title, fill=TEXT_WHITE)
    curr_y += 40

    table_start_y = curr_y
    table_content_h = 44 + sum(h for h, _, _ in tbl["row_heights"])
    
    # Fondo y borde exterior de la tabla
    draw.rounded_rectangle(
        [(40, table_start_y), (40 + TABLE_W, table_start_y + table_content_h)],
        radius=8,
        fill=CARD_BG,
        outline=BORDER_COLOR,
        width=1
    )

    # Header de la tabla
    draw.rounded_rectangle(
        [(40, table_start_y), (40 + TABLE_W, table_start_y + 44)],
        radius=8,
        fill=HEADER_BG
    )
    draw.rectangle([(40, table_start_y + 30), (40 + TABLE_W, table_start_y + 44)], fill=HEADER_BG)

    # Textos del Header
    draw.text((55, table_start_y + 12), "Comando", font=font_header, fill=HEADER_TEXT)
    draw.text((40 + COL_CMD_W + 15, table_start_y + 12), "Alias con !", font=font_header, fill=HEADER_TEXT)
    draw.text((40 + COL_CMD_W + COL_ALIAS_W + 15, table_start_y + 12), "¿Qué hace?", font=font_header, fill=HEADER_TEXT)

    # Línea inferior del header
    draw.line([(40, table_start_y + 44), (40 + TABLE_W, table_start_y + 44)], fill=BORDER_COLOR, width=1)

    curr_row_y = table_start_y + 44
    for idx, (cmd, alias, desc) in enumerate(tbl["rows"]):
        row_h, wrapped_desc, alias_lines = tbl["row_heights"][idx]
        
        # Color alterno sutil
        if idx % 2 == 1:
            draw.rectangle([(41, curr_row_y), (39 + TABLE_W, curr_row_y + row_h)], fill=ROW_ALT_BG)

        # Líneas separadoras de columnas
        draw.line([(40 + COL_CMD_W, curr_row_y), (40 + COL_CMD_W, curr_row_y + row_h)], fill=BORDER_COLOR, width=1)
        draw.line([(40 + COL_CMD_W + COL_ALIAS_W, curr_row_y), (40 + COL_CMD_W + COL_ALIAS_W, curr_row_y + row_h)], fill=BORDER_COLOR, width=1)

        # Dibujar Comando (Pill)
        cmd_y = curr_row_y + 14
        bbox = draw.textbbox((0, 0), cmd, font=font_code)
        pw = min(COL_CMD_W - 30, bbox[2] - bbox[0] + 16)
        draw.rounded_rectangle([(52, cmd_y), (52 + pw, cmd_y + 26)], radius=5, fill=PILL_BG, outline=BORDER_COLOR, width=1)
        draw.text((60, cmd_y + 4), cmd, font=font_code, fill=CODE_COLOR)

        # Dibujar Alias (Pill)
        alias_y = curr_row_y + 14
        for a_idx, a_line in enumerate(alias_lines):
            ay = alias_y + a_idx * 28
            bbox_a = draw.textbbox((0, 0), a_line, font=font_code)
            paw = min(COL_ALIAS_W - 30, bbox_a[2] - bbox_a[0] + 16)
            draw.rounded_rectangle([(40 + COL_CMD_W + 15, ay), (40 + COL_CMD_W + 15 + paw, ay + 24)], radius=5, fill=PILL_BG, outline=BORDER_COLOR, width=1)
            draw.text((40 + COL_CMD_W + 23, ay + 3), a_line, font=font_code, fill=CODE_COLOR)

        # Dibujar Descripción (Multiline)
        text_start_y = curr_row_y + 14
        for line_idx, line in enumerate(wrapped_desc):
            draw.text((40 + COL_CMD_W + COL_ALIAS_W + 15, text_start_y + line_idx * 22), line, font=font_body, fill=TEXT_MUTED)

        # Línea separadora de fila
        draw.line([(40, curr_row_y + row_h), (40 + TABLE_W, curr_row_y + row_h)], fill=BORDER_COLOR, width=1)
        curr_row_y += row_h

    curr_y = table_start_y + table_content_h + 38

out_path = r"c:\Users\Bru\Desktop\programacion\bots\discord\comandos_bot.png"
img.save(out_path, format="PNG", quality=95)
print(f"Imagen guardada en: {out_path}")

artifact_dir = r"C:\Users\Bru\.gemini\antigravity\brain\2b0e0a6f-6cde-438a-8432-6e848b422e83"
if os.path.exists(artifact_dir):
    artifact_img_path = os.path.join(artifact_dir, "comandos_bot.png")
    shutil.copyfile(out_path, artifact_img_path)
    print(f"Copiada al directorio de artefactos: {artifact_img_path}")
