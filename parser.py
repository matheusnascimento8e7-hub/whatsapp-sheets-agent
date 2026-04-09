from groq import Groq
from dotenv import load_dotenv
import config, json, re

load_dotenv()
client = Groq(api_key=config.GROQ_API_KEY)

MOTIVOS_CONHECIDOS = {"lacuna", "falta", "atestado", "suspensao", "coleta", "suporte"}

SYSTEM_PROMPT = """
Voce e um assistente que extrai informacoes de mensagens de cobertura de escala de trabalho de um grupo WhatsApp.

FORMATO 1 (com labels explicitas):
Nome do extra: Joao
Nome de quem ta cobrindo: Maria
Motivo: falta

FORMATO 2 (compacto com parenteses):
REGRA ABSOLUTA: FORA dos parenteses = COBERTO (quem faltou). DENTRO dos parenteses = COBRADOR (quem cobriu).
Excecao: se o conteudo dentro dos parenteses for motivo (lacuna, falta, suspensao, atestado, coleta), coberto = null e cobrador = null.

Exemplos:
- "Marcela (liliane)" -> coberto=Marcela, cobrador=Liliane, motivo=falta
- "Aline (lacuna)" -> coberto=null, cobrador=null, motivo=lacuna
- "Gabriel (moises)" -> coberto=Gabriel, cobrador=Moises, motivo=falta
- "Rodrigo (lacuna suporte)" -> coberto=null, cobrador=null, motivo=lacuna
- "Cesar (rafael)" -> coberto=Cesar, cobrador=Rafael, motivo=falta

Ignore cabecalhos: "Bom dia", "Extra 09/04", datas, saudacoes.
Se nao houver cobertura clara: [{"is_coverage": false}]

Retorne SOMENTE array JSON:
[{"is_coverage": true, "cobrador": "nome ou null", "coberto": "nome ou null", "motivo": "falta/atestado/suspensao/lacuna/outro", "dias": 1, "valor": 120}]
""".strip()


def _is_motivo(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(m in text_lower for m in MOTIVOS_CONHECIDOS)


def _parse_compact_line(line: str) -> dict | None:
    line = line.lstrip("- ").strip()
    match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', line)
    if not match:
        return None

    fora = match.group(1).strip()
    dentro = match.group(2).strip()

    if _is_motivo(fora):
        return None

    if _is_motivo(dentro):
        motivo = dentro.split()[0].lower()
        return {
            "is_coverage": True,
            "cobrador": None,
            "coberto": None,
            "motivo": motivo,
            "dias": 1,
            "valor": 120
        }
    else:
        return {
            "is_coverage": True,
            "cobrador": dentro.title(),
            "coberto": fora.title(),
            "motivo": "falta",
            "dias": 1,
            "valor": 120
        }


def _preprocess_compact(text: str) -> tuple[list[dict], str]:
    lines = text.strip().splitlines()
    regex_results = []
    leftover_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        result = _parse_compact_line(line)
        if result:
            regex_results.append(result)
        else:
            leftover_lines.append(line)

    return regex_results, "\n".join(leftover_lines)


def extract_coverage(message_text: str) -> list | None:
    regex_results, leftover = _preprocess_compact(message_text)

    llm_results = []

    if leftover.strip():
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": leftover}
            ],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = []
        if isinstance(data, list):
            llm_results = [item for item in data if item.get("is_coverage")]

    all_results = regex_results + llm_results
    return all_results if all_results else None