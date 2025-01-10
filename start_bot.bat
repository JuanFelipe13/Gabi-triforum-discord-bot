@echo off
title Music Bot
echo Iniciando Music Bot...

REM Verificar si existe el archivo .env
if not exist ".env" (
    echo ERROR: No se encuentra el archivo .env
    echo Creando archivo .env...
    echo DISCORD_TOKEN=tu_token_aqui > .env
    echo Por favor, edita el archivo .env con tu token de Discord
    notepad .env
    pause
    exit
)

REM Iniciar el bot
echo Iniciando bot...
MusicBot.exe

REM Si el bot se cierra con un error, pausar para ver el mensaje
if %errorlevel% neq 0 (
    echo.
    echo El bot se cerro con un error. Presiona cualquier tecla para salir.
    pause >nul
)
