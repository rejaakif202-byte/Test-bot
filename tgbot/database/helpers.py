from database.db import *
from datetime import datetime

_sudo_cache = set()

# ── SUDO ─────────────────────────────────────────────────────────────────────

def get_sudo_users_sync():
    return _sudo_cache

async def load_sudo_cache():
    docs = await sudo_col.find({}).to_list(None)
    _sudo_cache.clear()
    _sudo_cache.update(doc["_id"] for doc in docs)

async def add_sudo(user_id: int):
    await sudo_col.update_one({"_id": user_id}, {"$set": {}}, upsert=True)
    _sudo_cache.add(user_id)

async def remove_sudo(user_id: int):
    await sudo_col.delete_one({"_id": user_id})
    _sudo_cache.discard(user_id)

async def get_sudo_users():
    docs = await sudo_col.find({}).to_list(None)
    return {doc["_id"] for doc in docs}

async def is_sudo_db(user_id: int) -> bool:
    from config import Config
    return Config.is_owner(user_id) or user_id in _sudo_cache

# ── USER & GROUP ──────────────────────────────────────────────────────────────

async def save_user(user_id: int, username: str = None, full_name: str = None):
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"username": username, "full_name": full_name, "last_seen": datetime.utcnow()}},
        upsert=True
    )

async def save_group(chat_id: int, title: str = None):
    await groups_col.update_one(
        {"_id": chat_id},
        {"$set": {"title": title}},
        upsert=True
    )

async def get_all_groups():
    return await groups_col.find({}).to_list(None)

async def get_all_users():
    return await users_col.find({}).to_list(None)

async def total_groups():
    return await groups_col.count_documents({})

async def total_users():
    return await users_col.count_documents({})

# ── BLOCKED USERS ─────────────────────────────────────────────────────────────

async def block_user(user_id: int):
    await blocked_col.update_one({"_id": user_id}, {"$set": {}}, upsert=True)

async def unblock_user(user_id: int):
    await blocked_col.delete_one({"_id": user_id})

async def is_blocked(user_id: int) -> bool:
    return bool(await blocked_col.find_one({"_id": user_id}))

# ── WARNS ─────────────────────────────────────────────────────────────────────

async def add_warn(chat_id: int, user_id: int, reason: str = None, expires: datetime = None) -> int:
    doc = await warns_col.find_one({"chat_id": chat_id, "user_id": user_id})
    warns = doc["warns"] + 1 if doc else 1
    await warns_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"warns": warns, "last_reason": reason, "expires": expires}},
        upsert=True
    )
    return warns

async def remove_warn(chat_id: int, user_id: int) -> int:
    doc = await warns_col.find_one({"chat_id": chat_id, "user_id": user_id})
    if not doc or doc["warns"] <= 0:
        return 0
    warns = doc["warns"] - 1
    if warns <= 0:
        await warns_col.delete_one({"chat_id": chat_id, "user_id": user_id})
        return 0
    await warns_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"warns": warns}}
    )
    return warns

async def get_warns(chat_id: int, user_id: int) -> int:
    doc = await warns_col.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc["warns"] if doc else 0

async def reset_warns(chat_id: int, user_id: int):
    await warns_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_warn_limit(chat_id: int) -> int:
    doc = await settings_col.find_one({"_id": chat_id})
    return doc.get("warn_limit", 3) if doc else 3

async def set_warn_limit(chat_id: int, limit: int):
    await settings_col.update_one({"_id": chat_id}, {"$set": {"warn_limit": limit}}, upsert=True)

# ── GBAN ──────────────────────────────────────────────────────────────────────

async def gban_user(user_id: int, reason: str = None):
    await gbans_col.update_one(
        {"_id": user_id},
        {"$set": {"reason": reason, "date": datetime.utcnow()}},
        upsert=True
    )

async def ungban_user(user_id: int):
    await gbans_col.delete_one({"_id": user_id})

async def is_gbanned(user_id: int) -> bool:
    return bool(await gbans_col.find_one({"_id": user_id}))

async def get_gban(user_id: int):
    return await gbans_col.find_one({"_id": user_id})

async def get_gban_list():
    return await gbans_col.find({}).to_list(None)

# ── GMUTE ─────────────────────────────────────────────────────────────────────

async def gmute_user(user_id: int, reason: str = None):
    await gmutes_col.update_one(
        {"_id": user_id},
        {"$set": {"reason": reason, "date": datetime.utcnow()}},
        upsert=True
    )

async def ungmute_user(user_id: int):
    await gmutes_col.delete_one({"_id": user_id})

async def is_gmuted(user_id: int) -> bool:
    return bool(await gmutes_col.find_one({"_id": user_id}))

async def get_gmute_list():
    return await gmutes_col.find({}).to_list(None)

# ── APPROVED ──────────────────────────────────────────────────────────────────

async def approve_user(chat_id: int, user_id: int):
    await approved_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"approved": True}},
        upsert=True
    )

async def unapprove_user(chat_id: int, user_id: int):
    await approved_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def is_approved(chat_id: int, user_id: int) -> bool:
    return bool(await approved_col.find_one({"chat_id": chat_id, "user_id": user_id}))

async def get_approved_users(chat_id: int):
    return await approved_col.find({"chat_id": chat_id}).to_list(None)

async def approve_all(chat_id: int, user_ids: list):
    for uid in user_ids:
        await approve_user(chat_id, uid)

async def unapprove_all(chat_id: int):
    await approved_col.delete_many({"chat_id": chat_id})

# ── BLACKLIST ─────────────────────────────────────────────────────────────────

async def add_blacklist(chat_id: int, word: str):
    await blacklist_col.update_one(
        {"chat_id": chat_id, "word": word},
        {"$set": {}},
        upsert=True
    )

async def remove_blacklist(chat_id: int, word: str):
    await blacklist_col.delete_one({"chat_id": chat_id, "word": word})

async def get_blacklist(chat_id: int):
    docs = await blacklist_col.find({"chat_id": chat_id}).to_list(None)
    return [doc["word"] for doc in docs]

# ── BLACKLIST CHATS ───────────────────────────────────────────────────────────

async def blacklist_chat(chat_id: int, title: str = None):
    await blacklistchat_col.update_one(
        {"_id": chat_id},
        {"$set": {"title": title}},
        upsert=True
    )

async def whitelist_chat(chat_id: int):
    await blacklistchat_col.delete_one({"_id": chat_id})

async def is_chat_blacklisted(chat_id: int) -> bool:
    return bool(await blacklistchat_col.find_one({"_id": chat_id}))

async def get_blacklisted_chats():
    return await blacklistchat_col.find({}).to_list(None)

# ── FILTERS ───────────────────────────────────────────────────────────────────

async def add_filter(chat_id: int, trigger: str, response: str, buttons: list = None, file_id: str = None, file_type: str = None):
    await filters_col.update_one(
        {"chat_id": chat_id, "trigger": trigger.lower()},
        {"$set": {"response": response, "buttons": buttons or [], "file_id": file_id, "file_type": file_type}},
        upsert=True
    )

async def remove_filter(chat_id: int, trigger: str):
    await filters_col.delete_one({"chat_id": chat_id, "trigger": trigger.lower()})

async def remove_all_filters(chat_id: int):
    await filters_col.delete_many({"chat_id": chat_id})

async def get_filters(chat_id: int):
    return await filters_col.find({"chat_id": chat_id}).to_list(None)

async def get_filter(chat_id: int, trigger: str):
    return await filters_col.find_one({"chat_id": chat_id, "trigger": trigger.lower()})

# ── LOCKS ─────────────────────────────────────────────────────────────────────

async def lock_type(chat_id: int, lock: str):
    await locks_col.update_one(
        {"_id": chat_id},
        {"$addToSet": {"locked": lock}},
        upsert=True
    )

async def unlock_type(chat_id: int, lock: str):
    await locks_col.update_one(
        {"_id": chat_id},
        {"$pull": {"locked": lock}}
    )

async def get_locks(chat_id: int):
    doc = await locks_col.find_one({"_id": chat_id})
    return doc.get("locked", []) if doc else []

async def is_locked(chat_id: int, lock: str) -> bool:
    locks = await get_locks(chat_id)
    return lock in locks

# ── SETTINGS ──────────────────────────────────────────────────────────────────

async def get_setting(chat_id: int, key: str, default=None):
    doc = await settings_col.find_one({"_id": chat_id})
    return doc.get(key, default) if doc else default

async def set_setting(chat_id: int, key: str, value):
    await settings_col.update_one({"_id": chat_id}, {"$set": {key: value}}, upsert=True)

# ── AFK ───────────────────────────────────────────────────────────────────────

async def set_afk(user_id: int, reason: str = None):
    await afk_col.update_one(
        {"_id": user_id},
        {"$set": {"reason": reason, "since": datetime.utcnow()}},
        upsert=True
    )

async def remove_afk(user_id: int):
    await afk_col.delete_one({"_id": user_id})

async def get_afk(user_id: int):
    return await afk_col.find_one({"_id": user_id})

async def is_afk(user_id: int) -> bool:
    return bool(await afk_col.find_one({"_id": user_id}))

# ── FLOOD ─────────────────────────────────────────────────────────────────────

async def get_flood_settings(chat_id: int):
    doc = await flood_col.find_one({"_id": chat_id})
    if not doc:
        return {"enabled": False, "limit": 5, "action": "mute"}
    return doc

async def set_flood_settings(chat_id: int, **kwargs):
    await flood_col.update_one({"_id": chat_id}, {"$set": kwargs}, upsert=True)

async def get_flood_count(chat_id: int, user_id: int):
    doc = await flood_tracker_col.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc if doc else {"count": 0, "warned": False}

async def increment_flood(chat_id: int, user_id: int):
    await flood_tracker_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"count": 1}, "$set": {"last_msg": datetime.utcnow()}},
        upsert=True
    )

async def set_flood_warned(chat_id: int, user_id: int):
    await flood_tracker_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"warned": True}}
    )

async def reset_flood(chat_id: int, user_id: int):
    await flood_tracker_col.delete_one({"chat_id": chat_id, "user_id": user_id})

# ── PROMOTED BY BOT ───────────────────────────────────────────────────────────

async def save_promoted(chat_id: int, user_id: int):
    await promoted_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {}},
        upsert=True
    )

async def is_promoted_by_bot(chat_id: int, user_id: int) -> bool:
    return bool(await promoted_col.find_one({"chat_id": chat_id, "user_id": user_id}))

async def remove_promoted(chat_id: int, user_id: int):
    await promoted_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def remove_all_promoted(chat_id: int):
    await promoted_col.delete_many({"chat_id": chat_id})

# ── MSG STATS ─────────────────────────────────────────────────────────────────

async def increment_msg_count(chat_id: int, user_id: int, username: str = None, full_name: str = None):
    await msg_stats_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"count": 1}, "$set": {"username": username, "full_name": full_name}},
        upsert=True
    )

async def get_top_users(chat_id: int, limit: int = 10):
    return await msg_stats_col.find({"chat_id": chat_id}).sort("count", -1).limit(limit).to_list(None)
