import logging
import datetime
from pyrogram import Client
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Client(
    "mitsuri_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    Config.BOT_START_TIME = datetime.datetime.utcnow()
    logger.info(f"Starting {Config.BOT_NAME}...")
    app.run()
    logger.info("Bot stopped.")
