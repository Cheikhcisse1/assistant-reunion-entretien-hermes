"""Hermès — serveur local de l'agent IA d'assistance de réunion et d'entretien.

Lance:  uvicorn hermes_server:app --host 127.0.0.1 --port 8765
Les clés API sont lues dans .env (jamais en dur dans le code).
"""
import logging
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

import security
from pydantic import BaseModel

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
(BASE / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(BASE / "logs" / "hermes.log", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("hermes")

DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "anthropic")
# Mode public (démo en ligne ouverte à tous) : pas de mot de passe, IA gratuite Gemini imposée,
# taille des entrées et des réponses plafonnée, envoi de mail par le serveur désactivé.
PUBLIC_MODE = os.getenv("PUBLIC_MODE") == "1"
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "12000"))
MODELS = {
    "gemini": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-4o"),
    "ollama": os.getenv("OLLAMA_MODEL", "hermes3"),  # Hermes (Nous Research) via Ollama local
}
STARTED = time.time()


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(title="Hermès — assistant réunion & entretien", default_response_class=UTF8JSONResponse)
security.install(app, ("/chat", "/meeting", "/interview", "/mail"))


class ChatIn(BaseModel):
    prompt: str
    system: str | None = None
    provider: str | None = None
    model: str | None = None
    max_tokens: int = 1500


class TextIn(BaseModel):
    text: str
    provider: str | None = None
    language: str = "français"


class InterviewIn(BaseModel):
    role: str
    context: str = ""
    n: int = 8
    provider: str | None = None


async def call_llm(prompt: str, system: str | None, provider: str | None, model: str | None, max_tokens: int) -> str:
    provider = provider or DEFAULT_PROVIDER
    if PUBLIC_MODE:  # en démo publique, le visiteur ne choisit ni le fournisseur ni le modèle
        provider, model, max_tokens = "gemini", None, min(max_tokens, 2000)
    model = model or MODELS.get(provider)
    if provider not in MODELS:
        raise HTTPException(400, f"Fournisseur inconnu: {provider}")
    if len(prompt) > MAX_INPUT_CHARS:
        raise HTTPException(413, f"Texte trop long : {MAX_INPUT_CHARS} caractères maximum.")
    async with httpx.AsyncClient(timeout=120) as c:
        if provider == "gemini":
            key = os.getenv("GEMINI_API_KEY")
            if not key:
                raise HTTPException(503, "GEMINI_API_KEY manquante")
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.5}}
            if system:
                body["systemInstruction"] = {"parts": [{"text": system}]}
            r = await c.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                             json=body, headers={"x-goog-api-key": key})
            r.raise_for_status()
            cands = r.json().get("candidates") or []
            parts = (cands[0].get("content") or {}).get("parts", []) if cands else []
            text = "".join(p.get("text", "") for p in parts)
            if not text.strip():
                raise HTTPException(502, "L'IA n'a pas renvoyé de réponse. Reformule ta demande.")
            return text
        if provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise HTTPException(503, "ANTHROPIC_API_KEY manquante dans .env")
            body = {"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
            if system:
                body["system"] = system
            r = await c.post("https://api.anthropic.com/v1/messages", json=body,
                             headers={"x-api-key": key, "anthropic-version": "2023-06-01"})
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json()["content"])
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        if provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise HTTPException(503, "OPENAI_API_KEY manquante dans .env")
            r = await c.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}"},
                             json={"model": model, "messages": msgs, "max_tokens": max_tokens})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        r = await c.post(f"{host}/api/chat", json={"model": model, "messages": msgs, "stream": False})
        r.raise_for_status()
        return r.json()["message"]["content"]


async def safe(*a, **k) -> str:
    try:
        return await call_llm(*a, **k)
    except httpx.HTTPStatusError as e:
        log.error("Erreur LLM: %s %s", e, e.response.text)
        try:
            msg = e.response.json()["error"]["message"]
        except Exception:
            msg = e.response.text[:300]
        raise HTTPException(502, f"{e.response.status_code} — {msg}")
    except httpx.HTTPError as e:
        log.error("Erreur LLM: %s", e)
        raise HTTPException(502, f"Erreur du fournisseur LLM: {e}")


class MailIn(BaseModel):
    to: str
    subject: str
    body: str


def mail_ready() -> bool:
    return all(os.getenv(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD"))


@app.post("/mail/send")
async def mail_send(i: MailIn):
    """Envoie le résultat validé par l'utilisateur (SMTP configuré dans .env)."""
    if PUBLIC_MODE:
        raise HTTPException(403, "Envoi de mail désactivé dans la démo publique.")
    if not mail_ready():
        raise HTTPException(503, "SMTP non configuré dans .env (SMTP_HOST, SMTP_USER, SMTP_PASSWORD)")
    if "@" not in i.to:
        raise HTTPException(400, "Adresse e-mail invalide")
    import smtplib
    from email.message import EmailMessage
    from starlette.concurrency import run_in_threadpool

    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER"))
    msg["To"] = i.to
    msg["Subject"] = i.subject
    msg.set_content(i.body)

    def send():
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587")), timeout=30) as s:
            s.starttls()
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            s.send_message(msg)

    try:
        await run_in_threadpool(send)
    except Exception as e:
        log.error("Erreur mail: %s", e)
        raise HTTPException(502, f"Échec d'envoi: {e}")
    log.info("Mail envoyé à %s", i.to)
    return {"sent": True}


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "ui.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    if PUBLIC_MODE:
        return {"status": "ok", "public": True, "mail": False, "mail_to": "",
                "keys": {"gemini": bool(os.getenv("GEMINI_API_KEY"))}}
    return {"status": "ok", "uptime_s": int(time.time() - STARTED), "default_provider": DEFAULT_PROVIDER,
            "mail": mail_ready(), "mail_to": os.getenv("MAIL_TO", ""),
            "keys": {"anthropic": bool(os.getenv("ANTHROPIC_API_KEY")), "openai": bool(os.getenv("OPENAI_API_KEY")),
                     "gemini": bool(os.getenv("GEMINI_API_KEY"))}}


@app.post("/chat")
async def chat(i: ChatIn):
    return {"answer": await safe(i.prompt, i.system, i.provider, i.model, i.max_tokens)}


@app.post("/meeting/summarize")
async def summarize(i: TextIn):
    sys = (f"Tu es un assistant de réunion. Réponds en {i.language}. Produis: 1) Résumé en 5 lignes max, "
           "2) Décisions prises, 3) Actions (qui / quoi / échéance), 4) Points ouverts.")
    return {"summary": await safe(i.text, sys, i.provider, None, 1500)}


@app.post("/interview/questions")
async def questions(i: InterviewIn):
    sys = "Tu es un recruteur expert. Génère des questions d'entretien pertinentes, numérotées, avec ce qu'une bonne réponse doit contenir."
    p = f"Poste: {i.role}\nContexte: {i.context}\nNombre de questions: {i.n}"
    return {"questions": await safe(p, sys, i.provider, None, 2000)}


@app.post("/interview/feedback")
async def feedback(i: TextIn):
    sys = (f"Tu es un coach d'entretien. Réponds en {i.language}. Analyse la réponse du candidat: points forts, "
           "faiblesses, version améliorée, note /10.")
    return {"feedback": await safe(i.text, sys, i.provider, None, 1500)}
