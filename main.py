from fastapi import FastAPI, Request
from parser import extract_coverage
from sheets import append_coverage
import config, json

app = FastAPI()

ALLOWED_SENDER = "5524992222943"
GROUP_JID = "120363182491077390@g.us"

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

    # Filtra por grupo específico
    if remote_jid != GROUP_JID:
        return {"status": "ignored", "reason": "wrong group or direct message"}

    # Filtra por remetente autorizado
    if sender_number != ALLOWED_SENDER:
        return {"status": "ignored", "reason": f"sender not allowed: {sender_number}"}

    text = (
        message_data.get("conversation")
        or message_data.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored", "reason": "no text content"}

    # Correção 3: Logando o texto completo para auditoria
    print(f"[Webhook] Mensagem de {sender_number}: {text}")

    coverages = extract_coverage(text)

    if coverages is None:
        return {"status": "ignored", "reason": "not a coverage message"}

    # Correção 2: Try/Except individual por cobertura no loop
    for parsed in coverages:
        try:
            append_coverage(sender_number, parsed, text)
        except Exception as e:
            print(f"[Webhook] ❌ Falha ao gravar cobertura {parsed}: {e}")

    print(f"[Webhook] {len(coverages)} cobertura(s) processada(s)")
    return {"status": "ok", "count": len(coverages), "extracted": coverages}


@app.get("/health")
def health():
    return {"status": "running"}
