import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import config, json

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    creds_dict = json.loads(config.GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(config.SPREADSHEET_ID)
    return sh.worksheet(config.SHEET_NAME)

def ensure_header(sheet):
    if sheet.row_count == 0 or sheet.cell(1, 1).value is None:
        sheet.append_row([
            "Timestamp Recebimento",
            "Remetente",
            "Cobrador",
            "Coberto",
            "Motivo",
            "Dias",
            "Valor",
            "Mensagem Original"
        ])

def append_coverage(sender: str, parsed: dict, raw_message: str):
    sheet = get_sheet()
    ensure_header(sheet)

    # Registro com fuso horário fixo (Brasília -3h)
    row = [
        datetime.now(tz=timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M:%S"),
        sender,
        parsed.get("cobrador", ""),
        parsed.get("coberto", "") or "",
        parsed.get("motivo", ""),
        parsed.get("dias", ""),
        parsed.get("valor", 120),
        raw_message
    ]

    sheet.append_row(row)
    print(f"[Sheets] Linha adicionada: {row[:4]}")