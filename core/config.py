import os
from dotenv import load_dotenv

# Cargamos las variables de entorno del archivo .env
load_dotenv(override=True)

class Settings:
    NEON_DATABASE_URL: str = os.getenv("NEON_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

settings = Settings()
