from fastapi import FastAPI, Request
from parser import extract_coverage
from sheets import append_coverage
import config, json

app = FastAPI()

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

    # Log de diagnóstico — mostra TODAS as mensagens recebidas
    print(f"[Incoming] remote_jid={remote_jid!r} sender={sender_number!r}")

    if remote_jid != config.GROUP_JID:
        print(f"[Filter] grupo errado: {remote_jid!r} != {config.GROUP_JID!r}")
        return {"status": "ignored", "reason": "wrong group"}

    if sender_number not in config.ALLOWED_SENDERS:
        print(f"[Filter] sender nao autorizado: {sender_number!r} not in {config.ALLOWED_SENDERS}")
        return {"status": "ignored", "reason": f"sender not allowed: {sender_number}"}

    text = (
        message_data.get("conversation")
        or message_data.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored", "reason": "no text content"}

    print(f"[Webhook] Mensagem aceita de {sender_number}: {text}")

    coverages = extract_coverage(text)
    if coverages is None:
        print(f"[Parser] Nao identificado como cobertura")
        return {"status": "ignored", "reason": "not a coverage message"}

    for parsed in coverages:
        try:
            append_coverage(sender_number, parsed, text)
        except Exception as e:
            print(f"[Sheets] Erro ao gravar: {e}")

    print(f"[Webhook] {len(coverages)} cobertura(s) processada(s)")
    return {"status": "ok", "count": len(coverages), "extracted": coverages}

@app.get("/health")
def health():
    return {"status": "running"}
