import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import config, json, traceback

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    print(f"[Sheets] Conectando... SPREADSHEET_ID={config.SPREADSHEET_ID} SHEET_NAME={config.SHEET_NAME}")
    creds_dict = json.loads(config.GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(config.SPREADSHEET_ID)
    ws = sh.worksheet(config.SHEET_NAME)
    print(f"[Sheets] Planilha aberta com sucesso: {ws.title}")
    return ws

def ensure_header(sheet):
    try:
        val = sheet.cell(1, 1).value
        if not val:
            sheet.append_row(["Timestamp Recebimento", "Remetente", "Cobrador", "Coberto", "Motivo", "Dias", "Valor", "Posto", "Mensagem Original"])
            print("[Sheets] Cabeçalho inserido")
    except Exception as e:
        print(f"[Sheets] Erro ao verificar cabeçalho: {e}")

def append_coverage(sender: str, parsed: dict, raw_message: str):
    try:
        sheet = get_sheet()
        ensure_header(sheet)
        row = [
            datetime.now(tz=timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M:%S"),
            sender,
            parsed.get("cobrador") or "",
            parsed.get("coberto") or "",
            parsed.get("motivo", ""),
            parsed.get("dias", ""),
            parsed.get("valor", 120),
            parsed.get("posto", "Liberty"),
            raw_message
        ]
        sheet.append_row(row)
        print(f"[Sheets] ✅ Linha gravada: cobrador={row[2]} coberto={row[3]} motivo={row[4]}")
    except Exception as e:
        print(f"[Sheets] ❌ ERRO AO GRAVAR: {e}")
        print(traceback.format_exc())
        raise
