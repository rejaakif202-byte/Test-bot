from pyrogram import Client
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta


# ── PERMISSIONS ───────────────────────────────────────────────────────────────

MUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False
)

UNMUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_send_polls=True,
    can_invite_users=True
)


# ── ADMIN CHECKS ──────────────────────────────────────────────────────────────

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False

async def is_owner_of_chat(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status == ChatMemberStatus.OWNER
    except Exception:
        return False

async def check_bot_admin(client: Client, chat_id: int) -> bool:
    me = await client.get_me()
    return await is_admin(client, chat_id, me.id)

async def bot_has_right(client: Client, chat_id: int, right: str) -> bool:
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        return getattr(member.privileges, right, False)
    except Exception:
        return False

async def admin_has_right(client: Client, chat_id: int, user_id: int, right: str) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        return getattr(member.privileges, right, False)
    except Exception:
        return False

async def is_user_in_chat(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status not in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED,
            ChatMemberStatus.RESTRICTED
        )
    except Exception:
        return False


# ── USER EXTRACTION ───────────────────────────────────────────────────────────

async def get_target_user(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        identifier = message.command[1]
        try:
            if identifier.lstrip("@").isdigit():
                return await client.get_users(int(identifier.lstrip("@")))
            return await client.get_users(identifier.lstrip("@"))
        except Exception:
            return None
    return None


# ── TIME PARSING ──────────────────────────────────────────────────────────────

async def extract_time(time_str: str):
    """Parse time string like 30s, 2m, 1h, 7d into seconds. No minimum limit."""
    if not time_str:
        return None
    time_str = time_str.strip().lower()
    unit = time_str[-1]
    try:
        value = int(time_str[:-1])
        if value <= 0:
            return None
    except ValueError:
        return None
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if unit not in multipliers:
        return None
    return value * multipliers[unit]

def format_duration(seconds: float) -> str:
    """Format seconds into human readable duration."""
    seconds = int(seconds)
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    parts = []
    if days: parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours: parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes: parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds: parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    return ", ".join(parts) if parts else "0 seconds"


# ── MISC ──────────────────────────────────────────────────────────────────────

def extract_reason(message: Message, offset: int = 2) -> str:
    if len(message.command) > offset:
        return " ".join(message.command[offset:])
    return "No reason provided"

async def get_user_link(user) -> str:
    name = user.first_name or "User"
    return f"**[{name}](tg://user?id={user.id})**"

async def get_user_link_plain(user) -> str:
    name = user.first_name or "User"
    return f"[{name}](tg://user?id={user.id})"
