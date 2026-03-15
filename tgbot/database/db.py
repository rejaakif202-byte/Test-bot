from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

client = AsyncIOMotorClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

# Collections
users_col         = db["users"]
groups_col        = db["groups"]
warns_col         = db["warns"]
gbans_col         = db["gbans"]
gmutes_col        = db["gmutes"]
approved_col      = db["approved"]
sudo_col          = db["sudo_users"]
blocked_col       = db["blocked_users"]
blacklist_col     = db["blacklist"]
blacklistchat_col = db["blacklist_chats"]
filters_col       = db["filters"]
settings_col      = db["settings"]
afk_col           = db["afk"]
locks_col         = db["locks"]
flood_col         = db["flood_settings"]
flood_tracker_col = db["flood_tracker"]
promoted_col      = db["promoted_by_bot"]
pin_col           = db["pinned_messages"]
msg_stats_col     = db["msg_stats"]
