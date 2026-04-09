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
REGRA ABSOLUTA: FORA dos parenteses = COBRADOR (quem veio cobrir). DENTRO dos parenteses = COBERTO (quem faltou) + motivo + dias.
Excecao: se dentro dos parenteses nao houver nome de pessoa (apenas motivo como lacuna), coberto = null.

Exemplos:
- "Marcela (liliane atestado 5 dias)" -> cobrador=Marcela, coberto=Liliane, motivo=atestado, dias=5
- "Gabriel (moises falta)" -> cobrador=Gabriel, coberto=Moises, motivo=falta, dias=1
- "Cesar (rafael falta)" -> cobrador=Cesar, coberto=Rafael, motivo=falta, dias=1
- "Aline (lacuna)" -> cobrador=Aline, coberto=null, motivo=lacuna, dias=1
- "Rodrigo (lacuna suporte)" -> cobrador=Rodrigo, coberto=null, motivo=lacuna, dias=1

Ignore cabecalhos: "Bom dia", "Extra 09/04", datas, saudacoes.
Se nao houver cobertura clara: [{"is_coverage": false}]

Retorne SOMENTE array JSON:
[{"is_coverage": true, "cobrador": "nome ou null", "coberto": "nome ou null", "motivo": "falta/atestado/suspensao/lacuna/outro", "dias": 1, "valor": 120}]
""".strip()


def _is_motivo(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(m in text_lower for m in MOTIVOS_CONHECIDOS)


def _extract_motivo(text: str) -> str:
    text_lower = text.lower()
    for m in MOTIVOS_CONHECIDOS:
        if m in text_lower:
            return m
    return "falta"


def _extract_dias(text: str) -> int:
    match = re.search(r'(\d+)\s*dia', text.lower())
    return int(match.group(1)) if match else 1


def _extract_nome(text: str) -> str | None:
    resultado = text
    for m in MOTIVOS_CONHECIDOS:
        resultado = re.sub(rf'\b{m}\b', '', resultado, flags=re.IGNORECASE)
    resultado = re.sub(r'\d+\s*dias?', '', resultado, flags=re.IGNORECASE)
    resultado = resultado.strip().title()
    return resultado if resultado else None


def _parse_compact_line(line: str) -> dict | None:
    line = line.lstrip("- ").strip()
    match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', line)
    if not match:
        return None

    fora = match.group(1).strip()
    dentro = match.group(2).strip()

    dias = _extract_dias(dentro)
    motivo = _extract_motivo(dentro)
    nome_coberto = _extract_nome(dentro)

    return {
        "is_coverage": True,
        "cobrador": fora.title(),
        "coberto": nome_coberto,
        "motivo": motivo,
        "dias": dias,
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