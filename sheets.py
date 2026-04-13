import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import config, json, traceback

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheet():
    creds_dict = json.loads(config.GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(config.SPREADSHEET_ID)
    return sh.worksheet(config.SHEET_NAME)

def append_coverage(sender: str, parsed: dict, raw_message: str):
    try:
        sheet = get_sheet()

        timestamp = datetime.now(tz=timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M:%S")
        cobrador = parsed.get("cobrador") or ""
        coberto = parsed.get("coberto") or ""
        motivo = parsed.get("motivo", "")
        dias = parsed.get("dias", 1)
        valor = parsed.get("valor", 120)
        posto = parsed.get("posto", "Liberty")

        # Encontra a próxima linha vazia a partir da linha 2 (pula cabeçalho)
        all_values = sheet.col_values(1)  # coluna A (Timestamp)
        next_row = len(all_values) + 1

        # Grava cada coluna individualmente pelo índice para evitar
        # problemas de ordem com tabelas formatadas do Google Sheets
        sheet.update_cell(next_row, 1, timestamp)
        sheet.update_cell(next_row, 2, sender)
        sheet.update_cell(next_row, 3, cobrador)
        sheet.update_cell(next_row, 4, coberto)
        sheet.update_cell(next_row, 5, motivo)
        sheet.update_cell(next_row, 6, dias)
        sheet.update_cell(next_row, 7, valor)
        sheet.update_cell(next_row, 8, posto)
        sheet.update_cell(next_row, 9, raw_message)

        print(f"[Sheets] ✅ Linha {next_row} gravada: cobrador={cobrador} coberto={coberto} motivo={motivo}")

    except Exception as e:
        print(f"[Sheets] ❌ ERRO AO GRAVAR: {e}")
        print(traceback.format_exc())
        raise
