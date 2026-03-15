from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant
from datetime import datetime, timedelta
import asyncio

from utils.helpers import (is_admin, get_target_user, extract_time, extract_reason,
                            MUTE_PERMISSIONS, UNMUTE_PERMISSIONS, get_user_link,
                            check_bot_admin, bot_has_right, admin_has_right, is_user_in_chat,
                            format_duration)
from database.helpers import (add_warn, remove_warn, get_warns, reset_warns,
                               get_warn_limit, set_warn_limit)
from config import Config


async def _checks(client, message, target, need_ban_right=True):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return "**❌ You must be an admin to use this command.**"
    if not await check_bot_admin(client, message.chat.id):
        return "**❌ I'm not an admin in this group.**"
    if need_ban_right and not await bot_has_right(client, message.chat.id, "can_restrict_members"):
        return "**❌ I don't have permission to restrict members.**"
    if target:
        if await is_admin(client, message.chat.id, target.id):
            return "**❌ I can't act on an admin.**"
        if not await is_user_in_chat(client, message.chat.id, target.id):
            return "**❌ This user is no longer in the group.**"
    return None


# ── BAN ───────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("ban") & filters.group)
async def ban_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    reason = extract_reason(message)
    await client.ban_chat_member(message.chat.id, target.id)
    await message.reply(f"**🚫 [{target.first_name}](tg://user?id={target.id}) is now banned from the chat.\nReason: {reason}**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("unban") & filters.group)
async def unban_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    await client.unban_chat_member(message.chat.id, target.id)
    await message.reply(f"**✅ [{target.first_name}](tg://user?id={target.id}) is now unbanned from the chat.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("sban") & filters.group)
async def sban_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    await message.delete()
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await client.ban_chat_member(message.chat.id, target.id)

@Client.on_message(filters.command("tban") & filters.group)
async def tban_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    time_str = message.command[2] if len(message.command) > 2 else None
    if not time_str:
        return await message.reply("**❌ Please provide a time. Example: /tban @user 1h**")
    seconds = await extract_time(time_str)
    if not seconds:
        return await message.reply("**❌ Invalid time format. Use: 30s, 1m, 2h, 7d**")
    until = datetime.utcnow() + timedelta(seconds=seconds)
    await client.ban_chat_member(message.chat.id, target.id, until_date=until)
    await message.reply(f"**⏳ [{target.first_name}](tg://user?id={target.id}) has been temporarily banned for {time_str}.\nThey will be unbanned automatically.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("dban") & filters.group)
async def dban_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await message.delete()
    await client.ban_chat_member(message.chat.id, target.id)
    sent = await client.send_message(message.chat.id,
        f"**🗑️🚫 Message deleted and [{target.first_name}](tg://user?id={target.id}) has been banned.**",
        disable_web_page_preview=True)


# ── MUTE ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("mute") & filters.group)
async def mute_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS)
    await message.reply(f"**🔇 [{target.first_name}](tg://user?id={target.id}) is now muted from the chat.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    await client.restrict_chat_member(message.chat.id, target.id, UNMUTE_PERMISSIONS)
    await message.reply(f"**🔊 [{target.first_name}](tg://user?id={target.id}) is now unmuted from the chat.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("smute") & filters.group)
async def smute_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    await message.delete()
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS)

@Client.on_message(filters.command("tmute") & filters.group)
async def tmute_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    time_str = message.command[2] if len(message.command) > 2 else None
    if not time_str:
        return await message.reply("**❌ Please provide a time. Example: /tmute @user 1h**")
    seconds = await extract_time(time_str)
    if not seconds:
        return await message.reply("**❌ Invalid time format. Use: 30s, 1m, 2h, 7d**")
    until = datetime.utcnow() + timedelta(seconds=seconds)
    await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS, until_date=until)
    await message.reply(f"**⏳ [{target.first_name}](tg://user?id={target.id}) has been temporarily muted for {time_str}.\nThey will be unmuted automatically.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("dmute") & filters.group)
async def dmute_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await message.delete()
    await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS)
    await client.send_message(message.chat.id,
        f"**🗑️🔇 Message deleted and [{target.first_name}](tg://user?id={target.id}) has been muted.**",
        disable_web_page_preview=True)


# ── KICK ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("kick") & filters.group)
async def kick_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err: return await message.reply(err)
    await client.ban_chat_member(message.chat.id, target.id)
    await client.unban_chat_member(message.chat.id, target.id)
    await message.reply(f"**👢 [{target.first_name}](tg://user?id={target.id}) has been kicked from the chat.**",
                        disable_web_page_preview=True)


# ── WARN ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("warn") & filters.group)
async def warn_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err: return await message.reply(err)
    reason = extract_reason(message)
    limit = await get_warn_limit(message.chat.id)
    count = await add_warn(message.chat.id, target.id, reason)
    if count > limit:
        await client.ban_chat_member(message.chat.id, target.id)
        await reset_warns(message.chat.id, target.id)
        return await message.reply(
            f"**🚫 [{target.first_name}](tg://user?id={target.id}) has reached the maximum warnings and has been banned.**",
            disable_web_page_preview=True)
    await message.reply(
        f"**⚠️ [{target.first_name}](tg://user?id={target.id}) has been warned! ({count}/{limit})\nReason: {reason}**",
        disable_web_page_preview=True)

@Client.on_message(filters.command("unwarn") & filters.group)
async def unwarn_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    count = await remove_warn(message.chat.id, target.id)
    limit = await get_warn_limit(message.chat.id)
    await message.reply(
        f"**✅ One warning removed from [{target.first_name}](tg://user?id={target.id}). ({count}/{limit})**",
        disable_web_page_preview=True)

@Client.on_message(filters.command("swarn") & filters.group)
async def swarn_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err: return await message.reply(err)
    reason = extract_reason(message)
    limit = await get_warn_limit(message.chat.id)
    await message.delete()
    if message.reply_to_message:
        await message.reply_to_message.delete()
    count = await add_warn(message.chat.id, target.id, reason)
    if count > limit:
        await client.ban_chat_member(message.chat.id, target.id)
        await reset_warns(message.chat.id, target.id)

@Client.on_message(filters.command("twarn") & filters.group)
async def twarn_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err: return await message.reply(err)
    time_str = message.command[2] if len(message.command) > 2 else None
    if not time_str:
        return await message.reply("**❌ Please provide a time. Example: /twarn @user 1h**")
    seconds = await extract_time(time_str)
    if not seconds:
        return await message.reply("**❌ Invalid time format. Use: 30s, 1m, 2h, 7d**")
    reason = extract_reason(message, offset=3)
    limit = await get_warn_limit(message.chat.id)
    count = await add_warn(message.chat.id, target.id, reason, expires=datetime.utcnow() + timedelta(seconds=seconds))
    await message.reply(
        f"**⏳ [{target.first_name}](tg://user?id={target.id}) has been temporarily warned for {time_str}. ({count}/{limit})**",
        disable_web_page_preview=True)
    # Auto unwarn after timer
    await asyncio.sleep(seconds)
    await remove_warn(message.chat.id, target.id)

@Client.on_message(filters.command("dwarn") & filters.group)
async def dwarn_cmd(client: Client, message: Message):
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err: return await message.reply(err)
    reason = extract_reason(message)
    limit = await get_warn_limit(message.chat.id)
    if message.reply_to_message:
        await message.reply_to_message.delete()
    await message.delete()
    count = await add_warn(message.chat.id, target.id, reason)
    if count > limit:
        await client.ban_chat_member(message.chat.id, target.id)
        await reset_warns(message.chat.id, target.id)
        return await client.send_message(message.chat.id,
            f"**🚫 [{target.first_name}](tg://user?id={target.id}) has reached the maximum warnings and has been banned.**",
            disable_web_page_preview=True)
    await client.send_message(message.chat.id,
        f"**🗑️⚠️ Message deleted and [{target.first_name}](tg://user?id={target.id}) has been warned! ({count}/{limit})\nReason: {reason}**",
        disable_web_page_preview=True)

@Client.on_message(filters.command("warns") & filters.group)
async def warns_cmd(client: Client, message: Message):
    target = await get_target_user(client, message) or message.from_user
    count = await get_warns(message.chat.id, target.id)
    limit = await get_warn_limit(message.chat.id)
    await message.reply(f"**⚠️ [{target.first_name}](tg://user?id={target.id}) has {count}/{limit} warnings.**",
                        disable_web_page_preview=True)


# ── SETWARNLIMIT ──────────────────────────────────────────────────────────────

@Client.on_message(filters.command("setwarnlimit") & filters.group)
async def setwarnlimit_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    limit = await get_warn_limit(message.chat.id)
    buttons = _warn_limit_buttons(limit)
    await message.reply(f"**⚙️ Your default warn limit is: {limit}**", reply_markup=buttons)

def _warn_limit_buttons(limit: int):
    rows = []
    if limit < 5:
        rows.append([InlineKeyboardButton("📈 Increase Limit", callback_data="warnlimit_increase")])
    else:
        rows.append([InlineKeyboardButton("🔄 Back to Default", callback_data="warnlimit_reset")])
    rows.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    return InlineKeyboardMarkup(rows)

@Client.on_callback_query(filters.regex("^warnlimit_(increase|reset)$"))
async def warnlimit_callback(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    action = callback.matches[0].group(1)
    current = await get_warn_limit(callback.message.chat.id)
    if action == "increase" and current < 5:
        current += 1
        await set_warn_limit(callback.message.chat.id, current)
    elif action == "reset":
        current = 3
        await set_warn_limit(callback.message.chat.id, current)
    if current >= 5:
        text = f"**⚙️ Your default warn limit set to: {current}\nThis is the maximum warn limit.**"
    else:
        text = f"**⚙️ Your default warn limit is: {current}**"
    await callback.message.edit_text(text, reply_markup=_warn_limit_buttons(current))


# ── DEL ───────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("del") & filters.group)
async def del_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if not message.reply_to_message:
        return await message.reply("**❌ Please reply to a message to delete it.**")
    await message.reply_to_message.delete()
    await message.delete()


# ── PURGE ─────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("purge") & filters.group)
async def purge_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if not await bot_has_right(client, message.chat.id, "can_delete_messages"):
        return await message.reply("**❌ I don't have permission to delete messages.**")
    if not message.reply_to_message:
        return await message.reply("**❌ Please reply to a message to start purge from.**")
    start_id = message.reply_to_message.id
    end_id = message.id
    deleted = 0
    msg_ids = list(range(start_id, end_id + 1))
    for i in range(0, len(msg_ids), 100):
        chunk = msg_ids[i:i+100]
        try:
            await client.delete_messages(message.chat.id, chunk)
            deleted += len(chunk)
        except Exception:
            pass
    sent = await client.send_message(message.chat.id,
        f"**🧹 Purge completed, {deleted} messages deleted in {message.chat.title}.**")
    await asyncio.sleep(5)
    await sent.delete()
