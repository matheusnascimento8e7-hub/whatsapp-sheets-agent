from groq import Groq
from dotenv import load_dotenv
import config, json

load_dotenv()

client = Groq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """
Você é um assistente que extrai informações estruturadas de mensagens de cobertura de escala de trabalho enviadas num grupo de WhatsApp.

As mensagens podem conter UMA ou MÚLTIPLAS coberturas. Analise cada item separadamente.

Exemplos de mensagens de cobertura:
●Jaiane 1 dia de suspensão(Marcela)
●Liliane falta(aline)
●Rafael falta(Rodrigo)
●Emerson cobrindo coleta monet(cristiane)
●1 lacunas(cesar)

Regras de extração:
- "cobrador" é quem está dentro dos parênteses (quem fez a cobertura)
- "coberto" é o nome antes do motivo (quem gerou o buraco). Fica VAZIO quando o motivo for lacuna
- "motivo" é falta, suspensão, lacuna, ou outro termo que indique o motivo
- "dias" é o número de dias mencionado (padrão 1 se não informado)
- "valor" é 120 por padrão. Se houver menção explícita de outro valor na mensagem, usa esse valor

Retorne SEMPRE um array JSON, mesmo que haja apenas uma cobertura:
[
  {
    "is_coverage": true,
    "cobrador": "nome de quem fez a cobertura",
    "coberto": "nome de quem foi coberto ou null se lacuna",
    "motivo": "falta/suspensão/lacuna/outro",
    "dias": 1,
    "valor": 120
  }
]

Se a mensagem não contiver NENHUMA cobertura, retorne:
[{"is_coverage": false}]

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