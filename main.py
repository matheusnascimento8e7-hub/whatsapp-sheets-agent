from fastapi import FastAPI, Request
from parser import extract_coverage
from sheets import append_coverage
import config

app = FastAPI()

ALLOWED_SENDER = "5524992222943"

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()

    data = body.get("data", {})
    key = data.get("key", {})
    message_data = data.get("message", {})

    if key.get("fromMe"):
        return {"status": "ignored", "reason": "from me"}

    remote_jid = key.get("remoteJid", "")
    participant = data.get("participant", "")
    sender = participant or remote_jid
    sender_number = sender.replace("@s.whatsapp.net", "").replace("@g.us", "")

    if sender_number != ALLOWED_SENDER:
        return {"status": "ignored", "reason": "sender not allowed"}

    text = (
        message_data.get("conversation")
        or message_data.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored", "reason": "no text content"}

    print(f"[Webhook] Mensagem de {sender_number}: {text[:80]}...")

    coverages = extract_coverage(text)

    if coverages is None:
        return {"status": "ignored", "reason": "not a coverage message"}

    for parsed in coverages:
        append_coverage(sender_number, parsed, text)

    print(f"[Webhook] {len(coverages)} cobertura(s) gravada(s)")
    return {"status": "ok", "count": len(coverages), "extracted": coverages}


@app.get("/health")
def health():
    return {"status": "running"}