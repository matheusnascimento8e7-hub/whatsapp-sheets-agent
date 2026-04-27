from dotenv import load_dotenv
import os, json

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Coberturas")

GROUP_JID = os.getenv("GROUP_JID")
ALLOWED_SENDERS = set(filter(None, os.getenv("ALLOWED_SENDERS", "").split(",")))