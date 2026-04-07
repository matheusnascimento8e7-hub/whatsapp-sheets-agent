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

    # 1. Ignora mensagens enviadas pelo próprio bot
    if key.get("fromMe"):
        return {"status": "ignored", "reason": "from me"}

    # 2. Filtra remetente — só processa o número autorizado
    remote_jid = key.get("remoteJid", "")
    participant = data.get("participant", "")

    # Em grupos, o remetente vem em "participant"
    # Em conversa direta, vem em "remoteJid"
    sender = participant or remote_jid
    sender_number = sender.replace("@s.whatsapp.net", "").replace("@g.us", "")

    if sender_number != ALLOWED_SENDER:
        return {"status": "ignored", "reason": "sender not allowed"}

    # 3. Extrai o texto da mensagem
    text = (
        message_data.get("conversation")
        or message_data.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return {"status": "ignored", "reason": "no text content"}

    print(f"[Webhook] Mensagem de {sender_number}: {text[:80]}...")

    # 4. Extrai cobertura via LLM
    parsed = extract_coverage(text)

    if parsed is None:
        return {"status": "ignored", "reason": "not a coverage message"}

    # 5. Grava no Sheets
    append_coverage(sender_number, parsed, text)

    return {"status": "ok", "extracted": parsed}


@app.get("/health")
def health():
    return {"status": "running"}