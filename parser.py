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
[ausente] ([cobrador])
[ausente] motivo([cobrador])
●[ausente] motivo([cobrador])

Regras de extração:
- No FORMATO 2: o nome FORA dos parênteses é o COBERTO (ausente), o nome DENTRO dos parênteses é o COBRADOR (quem cobre). Exceção: se o conteúdo dentro dos parênteses for um motivo (lacuna, falta, suspensão), então é o motivo e coberto fica null.
- No FORMATO 1: "Nome do extra" = COBERTO, "Nome de quem tá cobrindo" = COBRADOR
- "motivo" = falta, atestado, suspensão, lacuna, coletor, lacuna externa, ou outro termo
- Se o COBRADOR for "lacuna", "lacuna externa" ou qualquer variante de lacuna, defina cobrador como null — significa que ninguém cobriu, a vaga ficou em aberto. O registro AINDA deve ser gravado com is_coverage: true.
- Se o COBERTO for lacuna, defina coberto como null.
- "dias" = número de dias (padrão 1)
- "valor" = 120 por padrão
- "posto" = nome do posto mencionado na mensagem (exemplos: Liberty, Socialtel Lapa, B&B Forte, B&B SDU, Wave by Yoo). Se a mensagem mencionar um posto no cabeçalho (ex: "Extra liberty 10/04", "Extra B&B SDU"), esse posto se aplica a TODAS as coberturas da mensagem. Se não houver menção alguma a posto, use "Liberty" como padrão.

Instruções críticas:
1. Ignore linhas de ruído como "Bom dia", "Extra 09/04/26", "Extra liberty08/04", "Extra", datas soltas e saudações — mas extraia o nome do posto dessas linhas se houver um.
2. A mensagem pode conter múltiplos blocos "Nome do extra / Nome de quem tá cobrindo / Motivo" separados por linhas de ruído. Extraia TODOS os blocos válidos e ignore as linhas de ruído entre eles.
3. Um registro é válido mesmo que cobrador seja null (lacuna) ou coberto seja null (lacuna). Nesses casos, is_coverage AINDA é true.
4. Só retorne is_coverage: false se a mensagem não tiver nenhuma informação de ausência ou cobertura.
5. Na dúvida, is_coverage: false

Retorne SEMPRE um array JSON:
[
  {
    "is_coverage": true,
    "cobrador": "nome de quem cobriu ou null se lacuna",
    "coberto": "nome do ausente ou null se lacuna",
    "motivo": "falta/atestado/suspensão/lacuna/coletor/lacuna externa/outro",
    "dias": 1,
    "valor": 120,
    "posto": "nome do posto ou Liberty se não mencionado"
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
