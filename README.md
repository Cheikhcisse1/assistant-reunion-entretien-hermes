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

## Déploiement en ligne (Render, démo publique gratuite)

La démo en ligne est **ouverte à tous, sans mot de passe**, et utilise l'IA **gratuite** Google Gemini (Ollama n'existe pas en ligne).
Garde-fous du mode public (`PUBLIC_MODE=1`) : fournisseur d'IA imposé (Gemini), limite de requêtes par visiteur et par heure (`RATE_LIMIT_PER_HOUR`), taille des textes plafonnée, aucune action serveur sensible (envoi de mail ou modification des paramètres partagés désactivés).

1. Créer une clé gratuite sur https://aistudio.google.com/apikey.
2. Créer un compte sur render.com (avec ton compte GitHub).
3. **New + > Blueprint** > choisir ce dépôt : Render lit `render.yaml`.
4. Coller la clé dans la variable `GEMINI_API_KEY` du tableau de bord Render (jamais dans Git).
5. Ouvrir l'URL fournie par Render.

Limites : le plan gratuit met le service en veille après inactivité (premier chargement d'environ 1 minute) ; le quota gratuit de Gemini est limité par jour.
Pour un accès privé avec Claude à la place : retirer `PUBLIC_MODE`, définir `APP_PASSWORD` et `ANTHROPIC_API_KEY`.
