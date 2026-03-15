from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatMemberStatus
from datetime import datetime, timedelta
import asyncio

from utils.helpers import (get_target_user, extract_time, extract_reason,
                            MUTE_PERMISSIONS, UNMUTE_PERMISSIONS, bot_has_right)
from database.helpers import (add_warn, remove_warn, get_warns, reset_warns,
                               get_warn_limit, set_warn_limit)
from config import Config


async def _get_member_status(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member
    except Exception:
        return None


async def _checks(client, message, target, need_ban_right=True):
    if not message.from_user:
        return "**❌ Could not identify sender.**"

    # Sender admin check - direct API call
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender:
        return "**❌ You must be an admin to use this command.**"
    if sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return "**❌ You must be an admin to use this command.**"

    # Bot admin check
    me = await client.get_me()
    bot_member = await _get_member_status(client, message.chat.id, me.id)
    if not bot_member:
        return "**❌ I'm not an admin in this group.**"
    if bot_member.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return "**❌ I'm not an admin in this group.**"

    # Bot restrict rights
    if need_ban_right:
        if bot_member.status == ChatMemberStatus.OWNER:
            pass  # Owner has all rights
        elif not bot_member.privileges or not bot_member.privileges.can_restrict_members:
            return "**❌ I don't have permission to restrict members.**"

    if target:
        # Bot khudpe action nahi
        if target.id == me.id:
            return "**❌ I can't act on myself.**"
        # Khudpe action nahi
        if target.id == message.from_user.id:
            return "**❌ You can't act on yourself.**"
        # Owner pe action nahi
        if target.id == Config.OWNER_ID:
            return "**❌ I can't act on the bot owner.**"
        # Admin pe action nahi
        target_member = await _get_member_status(client, message.chat.id, target.id)
        if not target_member:
            return "**❌ Could not find this user in the group.**"
        if target_member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            return "**❌ I can't act on an admin.**"
        if target_member.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
            return "**❌ This user is no longer in the group.**"

    return None


# ── BAN ───────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("ban") & filters.group)
async def ban_cmd(client: Client, message: Message):
    if not message.from_user:
        await message.reply("**DEBUG: from_user is None**")
        return
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        await message.reply(
            f"**DEBUG INFO:**\n"
            f"Status: `{member.status}`\n"
            f"User ID: `{message.from_user.id}`\n"
            f"Chat ID: `{message.chat.id}`\n"
            f"Is OWNER: `{member.status == ChatMemberStatus.OWNER}`\n"
            f"Is ADMIN: `{member.status == ChatMemberStatus.ADMINISTRATOR}`"
        )
    except Exception as e:
        await message.reply(f"**DEBUG ERROR:** `{str(e)}`")


@Client.on_message(filters.command("unban") & filters.group)
async def unban_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("**❌ You must be an admin.**")
    try:
        await client.unban_chat_member(message.chat.id, target.id)
        await message.reply(
            f"**✅ [{target.first_name}](tg://user?id={target.id}) is now unbanned from the chat.**",
            disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


@Client.on_message(filters.command("sban") & filters.group)
async def sban_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    try:
        await message.delete()
        if message.reply_to_message:
            await message.reply_to_message.delete()
        await client.ban_chat_member(message.chat.id, target.id)
    except Exception:
        pass


@Client.on_message(filters.command("tban") & filters.group)
async def tban_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    time_str = message.command[2] if len(message.command) > 2 else None
    if not time_str:
        return await message.reply("**❌ Please provide a time. Example: /tban @user 1h**")
    seconds = await extract_time(time_str)
    if not seconds:
        return await message.reply("**❌ Invalid time format. Use: 30s, 1m, 2h, 7d**")
    until = datetime.utcnow() + timedelta(seconds=seconds)
    try:
        await client.ban_chat_member(message.chat.id, target.id, until_date=until)
        await message.reply(
            f"**⏳ [{target.first_name}](tg://user?id={target.id}) has been temporarily banned for {time_str}.\nThey will be unbanned automatically.**",
            disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


@Client.on_message(filters.command("dban") & filters.group)
async def dban_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    try:
        if message.reply_to_message:
            await message.reply_to_message.delete()
        await message.delete()
        await client.ban_chat_member(message.chat.id, target.id)
        await client.send_message(
            message.chat.id,
            f"**🗑️🚫 Message deleted and [{target.first_name}](tg://user?id={target.id}) has been banned.**",
            disable_web_page_preview=True)
    except Exception as e:
        await client.send_message(message.chat.id, f"**❌ Failed: {str(e)}**")


# ── MUTE ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("mute") & filters.group)
async def mute_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    try:
        await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS)
        await message.reply(
            f"**🔇 [{target.first_name}](tg://user?id={target.id}) is now muted from the chat.**",
            disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


@Client.on_message(filters.command("unmute") & filters.group)
async def unmute_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("**❌ You must be an admin.**")
    try:
        await client.restrict_chat_member(message.chat.id, target.id, UNMUTE_PERMISSIONS)
        await message.reply(
            f"**🔊 [{target.first_name}](tg://user?id={target.id}) is now unmuted from the chat.**",
            disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


@Client.on_message(filters.command("smute") & filters.group)
async def smute_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    try:
        await message.delete()
        if message.reply_to_message:
            await message.reply_to_message.delete()
        await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS)
    except Exception:
        pass


@Client.on_message(filters.command("tmute") & filters.group)
async def tmute_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    time_str = message.command[2] if len(message.command) > 2 else None
    if not time_str:
        return await message.reply("**❌ Please provide a time. Example: /tmute @user 1h**")
    seconds = await extract_time(time_str)
    if not seconds:
        return await message.reply("**❌ Invalid time format. Use: 30s, 1m, 2h, 7d**")
    until = datetime.utcnow() + timedelta(seconds=seconds)
    try:
        await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS, until_date=until)
        await message.reply(
            f"**⏳ [{target.first_name}](tg://user?id={target.id}) has been temporarily muted for {time_str}.\nThey will be unmuted automatically.**",
            disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


@Client.on_message(filters.command("dmute") & filters.group)
async def dmute_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    try:
        if message.reply_to_message:
            await message.reply_to_message.delete()
        await message.delete()
        await client.restrict_chat_member(message.chat.id, target.id, MUTE_PERMISSIONS)
        await client.send_message(
            message.chat.id,
            f"**🗑️🔇 Message deleted and [{target.first_name}](tg://user?id={target.id}) has been muted.**",
            disable_web_page_preview=True)
    except Exception as e:
        await client.send_message(message.chat.id, f"**❌ Failed: {str(e)}**")


# ── KICK ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("kick") & filters.group)
async def kick_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target)
    if err:
        return await message.reply(err)
    try:
        await client.ban_chat_member(message.chat.id, target.id)
        await client.unban_chat_member(message.chat.id, target.id)
        await message.reply(
            f"**👢 [{target.first_name}](tg://user?id={target.id}) has been kicked from the chat.**",
            disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


# ── WARN ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("warn") & filters.group)
async def warn_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err:
        return await message.reply(err)
    reason = extract_reason(message)
    limit = await get_warn_limit(message.chat.id)
    count = await add_warn(message.chat.id, target.id, reason)
    if count > limit:
        try:
            await client.ban_chat_member(message.chat.id, target.id)
        except Exception:
            pass
        await reset_warns(message.chat.id, target.id)
        return await message.reply(
            f"**🚫 [{target.first_name}](tg://user?id={target.id}) has reached the maximum warnings and has been banned.**",
            disable_web_page_preview=True)
    await message.reply(
        f"**⚠️ [{target.first_name}](tg://user?id={target.id}) has been warned! ({count}/{limit})\nReason: {reason}**",
        disable_web_page_preview=True)


@Client.on_message(filters.command("unwarn") & filters.group)
async def unwarn_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("**❌ You must be an admin.**")
    count = await remove_warn(message.chat.id, target.id)
    limit = await get_warn_limit(message.chat.id)
    await message.reply(
        f"**✅ One warning removed from [{target.first_name}](tg://user?id={target.id}). ({count}/{limit})**",
        disable_web_page_preview=True)


@Client.on_message(filters.command("swarn") & filters.group)
async def swarn_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err:
        return await message.reply(err)
    reason = extract_reason(message)
    limit = await get_warn_limit(message.chat.id)
    try:
        await message.delete()
        if message.reply_to_message:
            await message.reply_to_message.delete()
    except Exception:
        pass
    count = await add_warn(message.chat.id, target.id, reason)
    if count > limit:
        try:
            await client.ban_chat_member(message.chat.id, target.id)
        except Exception:
            pass
        await reset_warns(message.chat.id, target.id)


@Client.on_message(filters.command("twarn") & filters.group)
async def twarn_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err:
        return await message.reply(err)
    time_str = message.command[2] if len(message.command) > 2 else None
    if not time_str:
        return await message.reply("**❌ Please provide a time. Example: /twarn @user 1h**")
    seconds = await extract_time(time_str)
    if not seconds:
        return await message.reply("**❌ Invalid time format. Use: 30s, 1m, 2h, 7d**")
    reason = extract_reason(message, offset=3)
    limit = await get_warn_limit(message.chat.id)
    count = await add_warn(message.chat.id, target.id, reason,
                           expires=datetime.utcnow() + timedelta(seconds=seconds))
    await message.reply(
        f"**⏳ [{target.first_name}](tg://user?id={target.id}) has been temporarily warned for {time_str}. ({count}/{limit})**",
        disable_web_page_preview=True)
    await asyncio.sleep(seconds)
    await remove_warn(message.chat.id, target.id)


@Client.on_message(filters.command("dwarn") & filters.group)
async def dwarn_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    err = await _checks(client, message, target, need_ban_right=False)
    if err:
        return await message.reply(err)
    reason = extract_reason(message)
    limit = await get_warn_limit(message.chat.id)
    try:
        if message.reply_to_message:
            await message.reply_to_message.delete()
        await message.delete()
    except Exception:
        pass
    count = await add_warn(message.chat.id, target.id, reason)
    if count > limit:
        try:
            await client.ban_chat_member(message.chat.id, target.id)
        except Exception:
            pass
        await reset_warns(message.chat.id, target.id)
        return await client.send_message(
            message.chat.id,
            f"**🚫 [{target.first_name}](tg://user?id={target.id}) has reached the maximum warnings and has been banned.**",
            disable_web_page_preview=True)
    await client.send_message(
        message.chat.id,
        f"**🗑️⚠️ Message deleted and [{target.first_name}](tg://user?id={target.id}) has been warned! ({count}/{limit})\nReason: {reason}**",
        disable_web_page_preview=True)


@Client.on_message(filters.command("warns") & filters.group)
async def warns_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    target = await get_target_user(client, message) or message.from_user
    count = await get_warns(message.chat.id, target.id)
    limit = await get_warn_limit(message.chat.id)
    await message.reply(
        f"**⚠️ [{target.first_name}](tg://user?id={target.id}) has {count}/{limit} warnings.**",
        disable_web_page_preview=True)


# ── SETWARNLIMIT ──────────────────────────────────────────────────────────────

@Client.on_message(filters.command("setwarnlimit") & filters.group)
async def setwarnlimit_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("**❌ You must be an admin.**")
    limit = await get_warn_limit(message.chat.id)
    await message.reply(f"**⚙️ Your default warn limit is: {limit}**",
                        reply_markup=_warn_limit_buttons(limit))


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
    sender = await _get_member_status(client, callback.message.chat.id, callback.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
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
    if not message.from_user:
        return
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        return await message.reply("**❌ You must be an admin.**")
    if not message.reply_to_message:
        return await message.reply("**❌ Please reply to a message to delete it.**")
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await message.reply(f"**❌ Failed: {str(e)}**")


# ── PURGE ─────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("purge") & filters.group)
async def purge_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    sender = await _get_member_status(client, message.chat.id, message.from_user.id)
    if not sender or sender.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
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
        chunk = msg_ids[i:i + 100]
        try:
            await client.delete_messages(message.chat.id, chunk)
            deleted += len(chunk)
        except Exception:
            pass
    sent = await client.send_message(
        message.chat.id,
        f"**🧹 Purge completed, {deleted} messages deleted in {message.chat.title}.**")
    await asyncio.sleep(5)
    await sent.delete()
