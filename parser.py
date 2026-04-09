from groq import Groq
from dotenv import load_dotenv
import config, json

load_dotenv()

client = Groq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """
Você é um assistente que extrai informações estruturadas de mensagens de cobertura de escala de trabalho enviadas num grupo de WhatsApp.

As mensagens podem vir em dois formatos:

FORMATO 1 (estruturado com labels):
Nome do extra: [nome do ausente]
Nome de quem tá cobrindo: [nome do cobrador]
Motivo: [motivo]

FORMATO 2 (compacto com parênteses):
[cobrador] ([coberto])
[cobrador] motivo([coberto])
●[cobrador] motivo([coberto])

Regras de extração:
- No FORMATO 2: o nome DENTRO dos parênteses é o COBERTO (ausente), o nome FORA é o COBRADOR (quem cobre)
- No FORMATO 1: "Nome do extra" = COBERTO, "Nome de quem tá cobrindo" = COBRADOR
- "motivo" = falta, atestado, suspensão, lacuna, coleta, ou outro termo
- Se o conteúdo dentro dos parênteses for um motivo (Ex: "lacuna", "falta"), então aquilo é o motivo — não um nome de pessoa
- Se o motivo for lacuna, o campo "coberto" deve ser null
- "dias" = número de dias mencionado (padrão 1 se não informado)
- "valor" = 120 por padrão

Instruções Críticas:
1. Ignore linhas de cabeçalho ou saudações como "Bom dia", "Extra 09/04/26", "Extra liberty08/04".
2. Se NÃO houver nenhuma cobertura clara, retorne: [{"is_coverage": false}]
3. Seja conservador: na dúvida, is_coverage: false.

Retorne SEMPRE um array JSON:
[
  {
    "is_coverage": true,
    "cobrador": "nome de quem cobriu",
    "coberto": "nome do ausente ou null se lacuna",
    "motivo": "falta/atestado/suspensão/lacuna/outro",
    "dias": 1,
    "valor": 120
  }
]

Retorne SOMENTE o JSON array, sem explicações.
""".strip()

def extract_coverage(message_text: str) -> list | None:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message_text}
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, list):
        return None

    coverages = [item for item in data if item.get("is_coverage")]
    return coverages if coverages else None