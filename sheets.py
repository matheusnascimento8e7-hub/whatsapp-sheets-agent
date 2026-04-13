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

        now = datetime.now(tz=timezone(timedelta(hours=-3)))
        timestamp = now.strftime("%d/%m/%Y %H:%M:%S")
        data = now.strftime("%d/%m/%Y")
        cobrador = parsed.get("cobrador") or ""
        coberto = parsed.get("coberto") or ""
        motivo = parsed.get("motivo", "")
        dias = parsed.get("dias", 1)
        valor = parsed.get("valor", 120)
        posto = parsed.get("posto", "Liberty")

        # Encontra a próxima linha vazia a partir da coluna A (Timestamp)
        all_values = sheet.col_values(1)
        next_row = len(all_values) + 1

        # Ordem das colunas na planilha:
        # A=Timestamp, B=Data, C=Remetente, D=Cobrador, E=Coberto,
        # F=Motivo, G=Dias, H=Valor, I=Posto, J=Mensagem Original
        sheet.update_cell(next_row, 1, timestamp)
        sheet.update_cell(next_row, 2, data)
        sheet.update_cell(next_row, 3, sender)
        sheet.update_cell(next_row, 4, cobrador)
        sheet.update_cell(next_row, 5, coberto)
        sheet.update_cell(next_row, 6, motivo)
        sheet.update_cell(next_row, 7, dias)
        sheet.update_cell(next_row, 8, valor)
        sheet.update_cell(next_row, 9, posto)
        sheet.update_cell(next_row, 10, raw_message)

        print(f"[Sheets] ✅ Linha {next_row} gravada: cobrador={cobrador} coberto={coberto} motivo={motivo}")

    except Exception as e:
        print(f"[Sheets] ❌ ERRO AO GRAVAR: {e}")
        print(traceback.format_exc())
        raise
