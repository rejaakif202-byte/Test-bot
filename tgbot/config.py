import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot credentials
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.environ.get("DB_NAME", "mitsuribot")

    # Bot owner - hardcoded
    OWNER_ID = 7846306818

    # Bot info
    BOT_NAME = "Mitsuri Kanroji"
    BOT_USERNAME = "mitsuri_Zprobot"
    SUPPORT_CHANNEL = "https://t.me/ANIMEXVERSE"
    CREATOR_LINK = "tg://openmessage?user_id=7846306818"
    ADD_GROUP_LINK = "https://t.me/mitsuri_Zprobot?startgroup=true"

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # Default settings
    MAX_WARN = 3
    BOT_START_TIME = None  # Set in bot.py on startup

    @classmethod
    def is_sudo(cls, user_id: int) -> bool:
        from database.helpers import get_sudo_users_sync
        sudo = get_sudo_users_sync()
        return user_id == cls.OWNER_ID or user_id in sudo

    @classmethod
    def is_owner(cls, user_id: int) -> bool:
        return user_id == cls.OWNER_ID
