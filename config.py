import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWM_API_KEY = os.getenv("OWM_API_KEY")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Москва")
DEFAULT_TIME = os.getenv("DEFAULT_TIME", "07:30")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
USERS_FILE = "users.json"
