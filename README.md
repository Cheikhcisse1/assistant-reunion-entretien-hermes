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

## Déploiement en ligne (Render)

> En ligne, **Ollama n'existe pas** : l'IA passe par l'API Claude (ou OpenAI) avec TA clé, qui sera facturée selon l'usage.
> Le serveur est protégé par mot de passe et limite les requêtes par IP (voir `security.py`) : sans `APP_PASSWORD`,
> il refuse de démarrer.

1. Créer un compte sur [render.com](https://render.com) (avec ton compte GitHub).
2. **New +** > **Blueprint** > choisir ce dépôt : Render lit `render.yaml`.
3. Renseigner les variables demandées dans le tableau de bord Render (jamais dans Git) :
   - `APP_PASSWORD` : le mot de passe d'accès (nom d'utilisateur libre) ;
   - `ANTHROPIC_API_KEY` : ta clé (nécessite des crédits sur console.anthropic.com).
4. Une fois déployé, ouvrir l'URL fournie par Render et saisir le mot de passe.

Limites à connaître : le plan gratuit met le service en veille après inactivité (premier chargement lent) ;
le disque est éphémère (les paramètres modifiés en ligne sont perdus à chaque redéploiement) ; l'image Docker n'a
pas été testée localement par l'auteur.
