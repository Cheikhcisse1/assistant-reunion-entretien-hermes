@echo off
rem Lance Hermes en continu (24h/24): redemarre automatiquement s'il s'arrete.
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul
title Hermes - serveur local (http://127.0.0.1:8765)
start "" http://127.0.0.1:8765
:loop
echo [%date% %time%] Demarrage de Hermes...
".venv\Scripts\python.exe" -m uvicorn hermes_server:app --host 127.0.0.1 --port 8765
echo [%date% %time%] Hermes arrete, redemarrage dans 5 s... (Ctrl+C pour quitter)
timeout /t 5 /nobreak >nul
goto loop
