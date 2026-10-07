# Hermès — assistant de réunion et d'entretien

Serveur local (FastAPI) avec interface web : résumé de réunion (décisions, actions), questions d'entretien,
coaching de réponse, chat libre. Dictée et lecture vocales (navigateur), validation par mail.

## LLM pris en charge
- **Hermes 3** en local via [Ollama](https://ollama.com) (par défaut recommandé, gratuit, données locales)
- **Claude** (Anthropic) — clé API avec crédits
- **OpenAI** — clé API

## Installation (Windows)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # puis renseigner .env (jamais publié)
ollama pull hermes3          # si usage local
```

## Lancement
Double-cliquer sur `start_hermes.bat` (redémarre automatiquement le serveur s'il s'arrête), puis ouvrir
http://127.0.0.1:8765

## Sécurité
- Les clés API restent dans `.env`, exclu du dépôt par `.gitignore`.
- Le serveur écoute uniquement sur `127.0.0.1` (non accessible depuis le réseau).
- Aucun e-mail n'est envoyé sans clic de validation de l'utilisateur.
