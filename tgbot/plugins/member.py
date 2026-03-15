from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio, os, re

from utils.helpers import is_admin, get_target_user, format_duration, is_owner_of_chat
from utils.afk_lines import get_afk_set_line, get_afk_tag_line, get_afk_return_line
from utils.fonts import convert_font, get_font_names
from database.helpers import (
    is_approved, is_gbanned, get_afk, set_afk, remove_afk, is_afk,
    get_flood_settings, set_flood_settings, get_flood_count,
    increment_flood, set_flood_warned, reset_flood, is_sudo_db
)
from config import Config
import datetime

_tagall_running = {}


# ── TAGALL ────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("tagall") & filters.group)
async def tagall_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    chat_id = message.chat.id
    if _tagall_running.get(chat_id):
        return await message.reply("**⚠️ A tagall is already in progress. Use /stoptagall to stop it.**")

    reason = " ".join(message.command[1:]) if len(message.command) > 1 else ""
    if message.reply_to_message and not reason:
        reason = message.reply_to_message.text or ""

    _tagall_running[chat_id] = True
    members = []
    async for member in client.get_chat_members(chat_id):
        if not member.user.is_bot:
            members.append(member.user)

    total = len(members)
    tagged = 0
    for i in range(0, len(members), 5):
        if not _tagall_running.get(chat_id):
            break
        chunk = members[i:i+5]
        mentions = " ".join([f"[{u.first_name}](tg://user?id={u.id})" for u in chunk])
        text = f"{mentions}"
        if reason:
            text += f"\n\n**{reason}**"
        await client.send_message(chat_id, text, disable_web_page_preview=True)
        tagged += len(chunk)
        await asyncio.sleep(1)

    _tagall_running.pop(chat_id, None)
    await client.send_message(chat_id, f"**📢 Tagall done! {tagged} members have been tagged.**")


@Client.on_message(filters.command("stoptagall") & filters.group)
async def stoptagall_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if not _tagall_running.get(message.chat.id):
        return await message.reply("**⚠️ No tagall is currently running.**")
    _tagall_running[message.chat.id] = False
    await message.reply("**✅ Tagall has been stopped.**")


# ── ANTIFLOOD ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("antiflood") & filters.group)
async def antiflood_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    settings = await get_flood_settings(message.chat.id)
    status = "ON ✅" if settings.get("enabled") else "OFF ❌"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ON", callback_data="flood_on"),
         InlineKeyboardButton("❌ OFF", callback_data="flood_off")]
    ])
    await message.reply(f"**🚨 Set your antiflood here:\nCurrent: {status}**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^flood_(on|off)$"))
async def flood_toggle(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    val = callback.matches[0].group(1) == "on"
    await set_flood_settings(callback.message.chat.id, enabled=val)
    status = "ON ✅" if val else "OFF ❌"
    await callback.message.edit_text(f"**🚨 Antiflood is now {status}**")

@Client.on_message(filters.command("setfloodtype") & filters.group)
async def setfloodtype_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban", callback_data="floodtype_ban"),
         InlineKeyboardButton("🔇 Mute", callback_data="floodtype_mute")],
        [InlineKeyboardButton("👢 Kick", callback_data="floodtype_kick"),
         InlineKeyboardButton("⚠️ Warn", callback_data="floodtype_warn")]
    ])
    await message.reply("**⚙️ Select flood action type:**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^floodtype_(ban|mute|kick|warn)$"))
async def floodtype_callback(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    action = callback.matches[0].group(1)
    await set_flood_settings(callback.message.chat.id, action=action)
    await callback.message.edit_text(f"**✅ Flood action set to: {action}**")

@Client.on_message(filters.command("setfloodlimit") & filters.group)
async def setfloodlimit_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    settings = await get_flood_settings(message.chat.id)
    limit = settings.get("limit", 5)
    await message.reply(f"**⚙️ Current flood limit: {limit} messages**",
                        reply_markup=_flood_limit_buttons(limit))

def _flood_limit_buttons(limit: int):
    rows = []
    if limit < 20:
        rows.append([InlineKeyboardButton("📈 Increase Limit", callback_data="floodlimit_increase")])
    else:
        rows.append([InlineKeyboardButton("🔄 Back to Default", callback_data="floodlimit_reset")])
    rows.append([InlineKeyboardButton("✅ Close & Save", callback_data="floodlimit_close")])
    return InlineKeyboardMarkup(rows)

@Client.on_callback_query(filters.regex("^floodlimit_(increase|reset|close)$"))
async def floodlimit_callback(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    action = callback.matches[0].group(1)
    settings = await get_flood_settings(callback.message.chat.id)
    limit = settings.get("limit", 5)
    if action == "increase" and limit < 20:
        limit += 5
        await set_flood_settings(callback.message.chat.id, limit=limit)
    elif action == "reset":
        limit = 5
        await set_flood_settings(callback.message.chat.id, limit=limit)
    elif action == "close":
        return await callback.message.edit_text(f"**✅ Flood limit saved: {limit} messages**")
    await callback.message.edit_text(
        f"**⚙️ Current flood limit: {limit} messages**",
        reply_markup=_flood_limit_buttons(limit))

@Client.on_message(filters.group & ~filters.command([]))
async def flood_listener(client: Client, message: Message):
    if not message.from_user:
        return
    if await is_admin(client, message.chat.id, message.from_user.id):
        return
    if await is_approved(message.chat.id, message.from_user.id):
        return
    settings = await get_flood_settings(message.chat.id)
    if not settings.get("enabled"):
        return
    limit = settings.get("limit", 5)
    action = settings.get("action", "mute")
    await increment_flood(message.chat.id, message.from_user.id)
    data = await get_flood_count(message.chat.id, message.from_user.id)
    count = data.get("count", 0)
    warned = data.get("warned", False)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"

    if count >= limit and not warned:
        await set_flood_warned(message.chat.id, message.from_user.id)
        await message.reply(f"**⚠️ {mention}, please slow down! You're flooding the chat.**",
                            disable_web_page_preview=True)
    elif count >= limit * 2 and warned:
        await reset_flood(message.chat.id, message.from_user.id)
        from utils.helpers import MUTE_PERMISSIONS
        if action == "ban":
            await client.ban_chat_member(message.chat.id, message.from_user.id)
            await message.reply(f"**🚫 {mention} has been banned for flooding.**", disable_web_page_preview=True)
        elif action == "mute":
            await client.restrict_chat_member(message.chat.id, message.from_user.id, MUTE_PERMISSIONS)
            await message.reply(f"**🔇 {mention} has been muted for flooding.**", disable_web_page_preview=True)
        elif action == "kick":
            await client.ban_chat_member(message.chat.id, message.from_user.id)
            await client.unban_chat_member(message.chat.id, message.from_user.id)
            await message.reply(f"**👢 {mention} has been kicked for flooding.**", disable_web_page_preview=True)
        elif action == "warn":
            from database.helpers import add_warn, get_warn_limit, reset_warns
            lmt = await get_warn_limit(message.chat.id)
            cnt = await add_warn(message.chat.id, message.from_user.id, "Flooding")
            if cnt > lmt:
                await client.ban_chat_member(message.chat.id, message.from_user.id)
                await reset_warns(message.chat.id, message.from_user.id)
                await message.reply(f"**🚫 {mention} has been banned after reaching max warnings.**",
                                    disable_web_page_preview=True)
            else:
                await message.reply(f"**⚠️ {mention} has been warned for flooding! ({cnt}/{lmt})**",
                                    disable_web_page_preview=True)


# ── ID ────────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("id"))
async def id_cmd(client: Client, message: Message):
    # Username provided
    if len(message.command) > 1:
        target = await get_target_user(client, message)
        if target:
            mention = f"[{target.first_name}](tg://user?id={target.id})"
            return await message.reply(f"**{mention} ID: `{target.id}`**", disable_web_page_preview=True)

    # Reply to channel message
    if message.reply_to_message and message.reply_to_message.sender_chat:
        chat = message.reply_to_message.sender_chat
        return await message.reply(f"**{chat.title} ID: `{chat.id}`**")

    # Reply to user message
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        return await message.reply(f"**{mention} ID: `{user.id}`**", disable_web_page_preview=True)

    # DM - show self
    if message.chat.type == "private":
        user = message.from_user
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        return await message.reply(f"**User {mention} ID is: `{user.id}`**", disable_web_page_preview=True)

    # Group - show self + chat
    return await message.reply(
        f"**Your ID: `{message.from_user.id}`\nChat ID: `{message.chat.id}`**")


# ── INFO ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("info"))
async def info_cmd(client: Client, message: Message):
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        target = await get_target_user(client, message)
    else:
        target = message.from_user

    if not target:
        return await message.reply("**❌ User not found.**")
    if target.is_bot and not hasattr(target, 'first_name'):
        return await message.reply("**❌ This command only works on users and bots.**")

    try:
        full_user = await client.get_users(target.id)
    except Exception:
        full_user = target

    full_name = f"{full_user.first_name or ''} {full_user.last_name or ''}".strip()
    username = f"@{full_user.username}" if full_user.username else "@none"
    mention = f"[{full_user.first_name}](tg://user?id={full_user.id})"
    is_bot = "Yes" if full_user.is_bot else "No"
    gbanned = "Yes ⚠️" if await is_gbanned(full_user.id) else "No ✅"
    bio = getattr(full_user, 'bio', None) or "(none)"

    if message.chat.type == "private":
        caption = (
            f"**👤 User Information:**\n\n"
            f"**User ID:** `{full_user.id}`\n"
            f"**Mention:** {mention}\n"
            f"**Full Name:** {full_name}\n"
            f"**Username:** {username}\n"
            f"**Bio:** {bio}\n"
            f"**Bot:** {is_bot}\n"
            f"**Gbanned:** {gbanned}"
        )
    else:
        # Get group status
        try:
            member = await client.get_chat_member(message.chat.id, full_user.id)
            if member.status == "creator":
                status = "👑 Owner"
            elif member.status == "administrator":
                status = "⭐ Admin"
            else:
                status = "👤 Member"
        except Exception:
            status = "Unknown"

        caption = (
            f"**👤 User Information:**\n\n"
            f"**User ID:** `{full_user.id}`\n"
            f"**Mention:** {mention}\n"
            f"**Full Name:** {full_name}\n"
            f"**Username:** {username}\n"
            f"**Bio:** {bio}\n"
            f"**Group Status:** {status}\n"
            f"**Bot:** {is_bot}\n"
            f"**Gbanned:** {gbanned}"
        )

    try:
        photos = await client.get_profile_photos(full_user.id, limit=1)
        if photos.total_count > 0:
            await message.reply_photo(photos[0].file_id, caption=caption, disable_web_page_preview=True)
        else:
            await message.reply(caption, disable_web_page_preview=True)
    except Exception:
        await message.reply(caption, disable_web_page_preview=True)


# ── AFK ───────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("afk"))
async def afk_cmd(client: Client, message: Message):
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else None
    await set_afk(message.from_user.id, reason)
    line = get_afk_set_line()
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    if reason:
        text = f"**{mention} is now AFK, {line}\nReason: {reason}**"
    else:
        text = f"**{mention} is now AFK, {line}**"
    await message.reply(text, disable_web_page_preview=True)

@Client.on_message(filters.group & ~filters.command([]))
async def afk_watcher(client: Client, message: Message):
    if not message.from_user:
        return

    # Check if sender is AFK and now sends a message (return from AFK)
    if await is_afk(message.from_user.id):
        afk_data = await get_afk(message.from_user.id)
        await remove_afk(message.from_user.id)
        since = afk_data.get("since", datetime.datetime.utcnow())
        duration = format_duration((datetime.datetime.utcnow() - since).total_seconds())
        reason = afk_data.get("reason")
        line = get_afk_return_line()
        mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
        if reason:
            text = f"**Welcome back {mention}, {line}\nYou were AFK for: {duration}\nReason: {reason}**"
        else:
            text = f"**Welcome back {mention}, {line}\nYou were AFK for: {duration}**"
        await message.reply(text, disable_web_page_preview=True)
        return

    # Check if someone is mentioning an AFK user
    if message.entities or message.text:
        for entity in (message.entities or []):
            uid = None
            if entity.type.name == "MENTION" and message.text:
                username = message.text[entity.offset+1:entity.offset+entity.length]
                try:
                    user = await client.get_users(username)
                    uid = user.id
                    uname = user.first_name
                except Exception:
                    continue
            elif entity.type.name == "TEXT_MENTION" and entity.user:
                uid = entity.user.id
                uname = entity.user.first_name

            if uid and await is_afk(uid):
                afk_data = await get_afk(uid)
                since = afk_data.get("since", datetime.datetime.utcnow())
                duration = format_duration((datetime.datetime.utcnow() - since).total_seconds())
                reason = afk_data.get("reason")
                line = get_afk_tag_line()
                mention = f"[{uname}](tg://user?id={uid})"
                if reason:
                    text = f"**{mention} {line}\nSince: {duration}\nReason: {reason}**"
                else:
                    text = f"**{mention} {line}\nSince: {duration}**"
                await message.reply(text, disable_web_page_preview=True)
                break

    # Reply to AFK user
    if message.reply_to_message and message.reply_to_message.from_user:
        uid = message.reply_to_message.from_user.id
        uname = message.reply_to_message.from_user.first_name
        if await is_afk(uid):
            afk_data = await get_afk(uid)
            since = afk_data.get("since", datetime.datetime.utcnow())
            duration = format_duration((datetime.datetime.utcnow() - since).total_seconds())
            reason = afk_data.get("reason")
            line = get_afk_tag_line()
            mention = f"[{uname}](tg://user?id={uid})"
            if reason:
                text = f"**{mention} {line}\nSince: {duration}\nReason: {reason}**"
            else:
                text = f"**{mention} {line}\nSince: {duration}**"
            await message.reply(text, disable_web_page_preview=True)


# ── FONT ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("font"))
async def font_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return
    text = " ".join(message.command[1:])
    font_names = get_font_names()
    rows = []
    for i in range(0, len(font_names), 3):
        row = [InlineKeyboardButton(fn, callback_data=f"font_{i+j}_{text[:30]}")
               for j, fn in enumerate(font_names[i:i+3])]
        rows.append(row)
    await message.reply(f"**{text}**", reply_markup=InlineKeyboardMarkup(rows))

@Client.on_callback_query(filters.regex(r"^font_(\d+)_(.+)$"))
async def font_callback(client: Client, callback: CallbackQuery):
    idx = int(callback.matches[0].group(1))
    text = callback.matches[0].group(2)
    font_names = get_font_names()
    if idx >= len(font_names):
        return await callback.answer("Font not found!", show_alert=True)
    font_name = font_names[idx]
    converted = convert_font(text, font_name)
    rows = []
    for i in range(0, len(font_names), 3):
        row = [InlineKeyboardButton(fn, callback_data=f"font_{i+j}_{text[:30]}")
               for j, fn in enumerate(font_names[i:i+3])]
        rows.append(row)
    await callback.message.edit_text(converted, reply_markup=InlineKeyboardMarkup(rows))


# ── GPT ───────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("gpt"))
async def gpt_cmd(client: Client, message: Message):
    if not message.from_user:
        return
    if await _is_blocked_user(message.from_user.id):
        return await message.reply("**❌ You are blocked from using this bot.**")
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /gpt your question**")
    question = " ".join(message.command[1:])
    thinking = await message.reply("**🤖 Thinking...**")
    try:
        import openai
        openai.api_key = Config.OPENAI_API_KEY
        response = await asyncio.to_thread(
            lambda: openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": question}]
            )
        )
        answer = response.choices[0].message.content
        await thinking.delete()
        bot_msg = await message.reply(f"**🤖 {answer}**")
        await asyncio.sleep(300)
        try:
            await message.delete()
            await bot_msg.delete()
        except Exception:
            pass
    except Exception as e:
        await thinking.delete()
        await message.reply(f"**❌ Error: {str(e)}**")

async def _is_blocked_user(user_id: int) -> bool:
    from database.helpers import is_blocked
    return await is_blocked(user_id)


# ── YT ────────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("yt"))
async def yt_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /yt youtube_link**")
    link = message.command[1]
    status = await message.reply("**⬇️ Downloading your video, please wait...**")
    try:
        import yt_dlp
        opts = {
            "format": "best[filesize<1900M]/best",
            "outtmpl": "/tmp/%(title)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
        if os.path.getsize(filename) > 2000 * 1024 * 1024:
            await status.edit("**❌ Video is too large to send (max 2GB).**")
            os.remove(filename)
            return
        await status.edit("**📤 Uploading...**")
        await message.reply_video(filename, caption=f"**🎬 {info.get('title', 'Video')}**")
        await status.delete()
        os.remove(filename)
    except Exception as e:
        await status.edit(f"**❌ Failed to download: {str(e)}**")


# ── IG ────────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("ig"))
async def ig_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /ig instagram_link**")
    link = message.command[1]
    status = await message.reply("**⬇️ Downloading your reel, please wait...**")
    try:
        import yt_dlp
        opts = {
            "format": "best",
            "outtmpl": "/tmp/%(title)s.%(ext)s",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
        if os.path.getsize(filename) > 2000 * 1024 * 1024:
            await status.edit("**❌ File is too large to send (max 2GB).**")
            os.remove(filename)
            return
        await status.edit("**📤 Uploading...**")
        await message.reply_video(filename, caption="**📸 Instagram Reel**")
        await status.delete()
        os.remove(filename)
    except Exception as e:
        await status.edit(f"**❌ Failed to download: {str(e)}**")


# ── REPORT ────────────────────────────────────────────────────────────────────

@Client.on_message((filters.command("report") | filters.regex(r"^@admin$")) & filters.group)
async def report_cmd(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply("**❌ Please reply to a message to report it.**")
    reporter = message.from_user
    reported_msg = message.reply_to_message
    reported_text = reported_msg.text or reported_msg.caption or "[media]"

    admins = await client.get_chat_members(message.chat.id, filter="administrators")
    me = await client.get_me()

    report_text = (
        f"**⚠️ New Report!\n\n"
        f"Reported by: [{reporter.first_name}](tg://user?id={reporter.id})\n"
        f"Group: {message.chat.title}\n"
        f"Reported message: {reported_text[:200]}**"
    )

    notified = 0
    for admin in admins:
        if admin.user.id == me.id or admin.user.is_bot:
            continue
        try:
            await client.send_message(admin.user.id, report_text, disable_web_page_preview=True)
            notified += 1
        except Exception:
            pass

    await message.reply(f"**✅ Admins have been notified! ({notified} admins)**")
