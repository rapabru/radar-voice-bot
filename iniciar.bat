@echo off
chcp 65001 >nul
title Bot de Discord
echo ==============================================
echo       INICIANDO BOT DE DISCORD
echo ==============================================
echo.

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [!] Entorno virtual no encontrado. Creando entorno virtual...
    python -m venv .venv
    echo [!] Instalando dependencias...
    .venv\Scripts\pip install -r requirements.txt
)

.venv\Scripts\python.exe main.py
pause
