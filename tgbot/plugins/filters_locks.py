from pyrogram import Client, filters
from pyrogram.types import (Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery)
from pyrogram.enums import MessageEntityType
import asyncio, re

from utils.helpers import is_admin, get_target_user, is_user_in_chat, check_bot_admin, bot_has_right
from database.helpers import (
    add_filter, remove_filter, remove_all_filters, get_filters, get_filter,
    add_blacklist, remove_blacklist, get_blacklist,
    blacklist_chat, whitelist_chat, is_chat_blacklisted, get_blacklisted_chats,
    lock_type, unlock_type, get_locks, is_locked,
    approve_user, unapprove_user, is_approved, get_approved_users,
    approve_all, unapprove_all,
    get_setting, set_setting,
    is_sudo_db
)
from config import Config

LOCK_TYPES = ["album", "anonchannel", "audio", "bot", "command",
              "contact", "document", "onlyemoji", "gif", "text",
              "url", "media", "invitelink", "sticker", "video"]


# ── FILTERS ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("filter") & filters.group)
async def add_filter_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    text = message.text or ""
    match = re.match(r'/filter\s+"(.+?)"(.*)', text, re.DOTALL)
    if not match:
        return await message.reply('**❌ Usage: /filter "trigger" response text\n[Button](buttonurl:link)**')
    trigger = match.group(1).strip().lower()
    response_raw = match.group(2).strip()

    # Parse buttons
    buttons = []
    button_pattern = re.compile(r'\[(.+?)\]\(buttonurl:(.+?)\)')
    for btn_match in button_pattern.finditer(response_raw):
        buttons.append({"text": btn_match.group(1), "url": btn_match.group(2)})
    response = button_pattern.sub("", response_raw).strip()

    file_id = file_type = None
    if message.reply_to_message:
        if message.reply_to_message.photo:
            file_id = message.reply_to_message.photo.file_id
            file_type = "photo"
        elif message.reply_to_message.video:
            file_id = message.reply_to_message.video.file_id
            file_type = "video"
        elif message.reply_to_message.document:
            file_id = message.reply_to_message.document.file_id
            file_type = "document"

    await add_filter(message.chat.id, trigger, response, buttons, file_id, file_type)
    await message.reply(f"**✅ Saved 1 filter in {message.chat.title}:\n- `{trigger}`**")


@Client.on_message(filters.command("stop") & filters.group)
async def stop_filter_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /stop trigger**")
    trigger = " ".join(message.command[1:]).lower()
    await remove_filter(message.chat.id, trigger)
    await message.reply(f"**✅ Filter `{trigger}` has been stopped.**")


@Client.on_message(filters.command("stopall") & filters.group)
async def stopall_filters_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data="stopall_yes"),
         InlineKeyboardButton("❌ No", callback_data="stopall_no")]
    ])
    await message.reply("**⚠️ Are you sure you want to stop all filters?**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^stopall_(yes|no)$"))
async def stopall_callback(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    if callback.matches[0].group(1) == "no":
        return await callback.message.edit_text("**❌ Cancelled.**")
    await remove_all_filters(callback.message.chat.id)
    await callback.message.edit_text("**✅ All filters have been stopped.**")


@Client.on_message(filters.command("filters") & filters.group)
async def list_filters_cmd(client: Client, message: Message):
    fltrs = await get_filters(message.chat.id)
    if not fltrs:
        return await message.reply("**📋 No filters set in this group.**")
    lines = [f"**Filters in {message.chat.title}:**\n"]
    for i, f in enumerate(fltrs, 1):
        lines.append(f"**{i}.** `{f['trigger']}`")
    await message.reply("\n".join(lines))


@Client.on_message(filters.group & ~filters.command([]))
async def filter_listener(client: Client, message: Message):
    if not message.text and not message.caption:
        return
    text = (message.text or message.caption or "").lower()
    fltrs = await get_filters(message.chat.id)
    for f in fltrs:
        if f["trigger"] in text:
            btns = []
            for btn in (f.get("buttons") or []):
                btns.append([InlineKeyboardButton(btn["text"], url=btn["url"])])
            markup = InlineKeyboardMarkup(btns) if btns else None
            response = f.get("response", "")
            file_id = f.get("file_id")
            file_type = f.get("file_type")
            try:
                if file_type == "photo" and file_id:
                    await message.reply_photo(file_id, caption=response or None, reply_markup=markup)
                elif file_type == "video" and file_id:
                    await message.reply_video(file_id, caption=response or None, reply_markup=markup)
                elif file_type == "document" and file_id:
                    await message.reply_document(file_id, caption=response or None, reply_markup=markup)
                elif response:
                    await message.reply(f"**{response}**", reply_markup=markup, disable_web_page_preview=True)
            except Exception:
                pass
            break


# ── BLACKLIST ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("blacklist") & filters.group)
async def blacklist_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /blacklist word**")
    word = " ".join(message.command[1:])
    await add_blacklist(message.chat.id, word)
    await message.reply(f"**✅ `{word}` has been added to the blacklist.**")

@Client.on_message(filters.command("unblacklist") & filters.group)
async def unblacklist_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /unblacklist word**")
    word = " ".join(message.command[1:])
    await remove_blacklist(message.chat.id, word)
    await message.reply(f"**✅ `{word}` has been removed from the blacklist.**")

@Client.on_message(filters.command("allblacklist") & filters.group)
async def allblacklist_cmd(client: Client, message: Message):
    words = await get_blacklist(message.chat.id)
    if not words:
        return await message.reply("**📋 No words blacklisted in this group.**")
    lines = [f"**Blacklisted items in {message.chat.title}:**\n"]
    for i, w in enumerate(words, 1):
        lines.append(f"**{i}.** `{w}`")
    await message.reply("\n".join(lines))

@Client.on_message(filters.group & ~filters.command([]))
async def blacklist_listener(client: Client, message: Message):
    if not message.from_user:
        return
    if await is_admin(client, message.chat.id, message.from_user.id):
        return
    if await is_approved(message.chat.id, message.from_user.id):
        return
    text = (message.text or message.caption or "").lower()
    words = await get_blacklist(message.chat.id)
    for word in words:
        if word.lower() in text:
            await message.delete()
            sent = await message.reply(
                f"**🚫 [{message.from_user.first_name}](tg://user?id={message.from_user.id})'s message was deleted due to blacklisted word: `{word}`**",
                disable_web_page_preview=True)
            await asyncio.sleep(5)
            await sent.delete()
            return


# ── BLACKLIST CHATS ───────────────────────────────────────────────────────────

@Client.on_message(filters.command("blacklistchat"))
async def blacklistchat_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /blacklistchat chat_id**")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply("**❌ Please provide a valid chat ID.**")
    try:
        chat = await client.get_chat(chat_id)
        title = chat.title
        await client.leave_chat(chat_id)
    except Exception:
        title = str(chat_id)
    await blacklist_chat(chat_id, title)
    await message.reply(f"**✅ Left and blacklisted chat: {title} (`{chat_id}`)**")

@Client.on_message(filters.command("whitelistchat"))
async def whitelistchat_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    if len(message.command) < 2:
        return await message.reply("**❌ Usage: /whitelistchat chat_id**")
    try:
        chat_id = int(message.command[1])
    except ValueError:
        return await message.reply("**❌ Please provide a valid chat ID.**")
    await whitelist_chat(chat_id)
    await message.reply(f"**✅ Chat `{chat_id}` has been removed from the blacklist.**")

@Client.on_message(filters.command("allblacklistchats"))
async def allblacklistchats_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    docs = await get_blacklisted_chats()
    if not docs:
        return await message.reply("**📋 No chats are blacklisted.**")
    lines = ["**🚫 Blacklisted Chats:**\n"]
    for i, doc in enumerate(docs, 1):
        title = doc.get("title", "Unknown")
        cid = doc["_id"]
        lines.append(f"**{i}. {title} — `{cid}`**")
    await message.reply("\n".join(lines))


# ── LOCK ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("lock") & filters.group)
async def lock_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if len(message.command) < 2:
        return await message.reply(f"**❌ Usage: /lock type\nAvailable: {', '.join(LOCK_TYPES)}, all**")
    ltype = message.command[1].lower()
    if ltype == "all":
        for lt in LOCK_TYPES:
            await lock_type(message.chat.id, lt)
        return await message.reply("**🔒 Locked all**")
    if ltype not in LOCK_TYPES:
        return await message.reply(f"**❌ Invalid type. Use /locktypes to see available types.**")
    locked = await get_locks(message.chat.id)
    if ltype in locked:
        return await message.reply(f"**🔒 {ltype} is already locked.**")
    await lock_type(message.chat.id, ltype)
    await message.reply(f"**🔒 Locked {ltype}**")

@Client.on_message(filters.command("unlock") & filters.group)
async def unlock_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if len(message.command) < 2:
        return await message.reply(f"**❌ Usage: /unlock type**")
    ltype = message.command[1].lower()
    if ltype == "all":
        for lt in LOCK_TYPES:
            await unlock_type(message.chat.id, lt)
        return await message.reply("**🔓 Unlocked all**")
    locked = await get_locks(message.chat.id)
    if ltype not in locked:
        return await message.reply(f"**🔓 {ltype} is already unlocked.**")
    await unlock_type(message.chat.id, ltype)
    await message.reply(f"**🔓 Unlocked {ltype}**")

@Client.on_message(filters.command("locktypes") & filters.group)
async def locktypes_cmd(client: Client, message: Message):
    rows = []
    for i in range(0, len(LOCK_TYPES), 3):
        row = [InlineKeyboardButton(lt, callback_data=f"lockinfo_{lt}") for lt in LOCK_TYPES[i:i+3]]
        rows.append(row)
    markup = InlineKeyboardMarkup(rows)
    try:
        from plugins.start import START_IMAGE
        await message.reply_photo(START_IMAGE, caption="**🔒 The available lock types are:**", reply_markup=markup)
    except Exception:
        await message.reply("**🔒 The available lock types are:**", reply_markup=markup)

@Client.on_message(filters.group & ~filters.command([]))
async def lock_listener(client: Client, message: Message):
    if not message.from_user:
        return
    if await is_admin(client, message.chat.id, message.from_user.id):
        return
    if await is_approved(message.chat.id, message.from_user.id):
        return
    locked = await get_locks(message.chat.id)
    ltype = None
    if "text" in locked and message.text and not message.sticker:
        ltype = "text"
    elif "media" in locked and (message.photo or message.video or message.audio or message.document):
        ltype = "media"
    elif "photo" in locked and message.photo:
        ltype = "photo"
    elif "video" in locked and message.video:
        ltype = "video"
    elif "audio" in locked and message.audio:
        ltype = "audio"
    elif "document" in locked and message.document:
        ltype = "document"
    elif "sticker" in locked and message.sticker:
        ltype = "sticker"
    elif "gif" in locked and message.animation:
        ltype = "gif"
    elif "url" in locked and message.entities:
        for e in message.entities:
            if e.type in (MessageEntityType.URL, MessageEntityType.TEXT_LINK):
                ltype = "url"
                break
    elif "invitelink" in locked and message.text and "t.me/" in message.text:
        ltype = "invitelink"
    elif "contact" in locked and message.contact:
        ltype = "contact"
    elif "command" in locked and message.text and message.text.startswith("/"):
        ltype = "command"
    elif "anonchannel" in locked and message.sender_chat:
        ltype = "anonchannel"
    elif "onlyemoji" in locked and message.text and all(
            ord(c) > 127 or c.isspace() for c in message.text):
        ltype = "onlyemoji"
    elif "album" in locked and message.media_group_id:
        ltype = "album"

    if ltype:
        await message.delete()
        sent = await client.send_message(
            message.chat.id,
            f"**🔒 {ltype} is locked in this group, so your message was deleted.**")
        await asyncio.sleep(5)
        await sent.delete()


# ── APPROVE ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("approve") & filters.group)
async def approve_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    await approve_user(message.chat.id, target.id)
    await message.reply(f"**✅ [{target.first_name}](tg://user?id={target.id}) has been approved.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("unapprove") & filters.group)
async def unapprove_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    await unapprove_user(message.chat.id, target.id)
    await message.reply(f"**❌ [{target.first_name}](tg://user?id={target.id}) has been unapproved.**",
                        disable_web_page_preview=True)

@Client.on_message(filters.command("approveall") & filters.group)
async def approveall_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    from utils.helpers import is_owner_of_chat
    if not await is_owner_of_chat(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ Only the group owner can use /approveall.**")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data="approveall_yes"),
         InlineKeyboardButton("❌ No", callback_data="approveall_no")]
    ])
    await message.reply("**⚠️ Are you sure you want to approve all members?**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^approveall_(yes|no)$"))
async def approveall_callback(client: Client, callback: CallbackQuery):
    from utils.helpers import is_owner_of_chat
    if not await is_owner_of_chat(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Owner only!", show_alert=True)
    if callback.matches[0].group(1) == "no":
        return await callback.message.edit_text("**❌ Cancelled.**")
    members = await client.get_chat_members(callback.message.chat.id)
    uids = [m.user.id for m in members if not m.user.is_bot]
    await approve_all(callback.message.chat.id, uids)
    await callback.message.edit_text(f"**✅ All {len(uids)} members have been approved.**")

@Client.on_message(filters.command("unapproveall") & filters.group)
async def unapproveall_cmd(client: Client, message: Message):
    from utils.helpers import is_owner_of_chat
    if not await is_owner_of_chat(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ Only the group owner can use /unapproveall.**")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes", callback_data="unapproveall_yes"),
         InlineKeyboardButton("❌ No", callback_data="unapproveall_no")]
    ])
    await message.reply("**⚠️ Are you sure you want to unapprove all members?**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^unapproveall_(yes|no)$"))
async def unapproveall_callback(client: Client, callback: CallbackQuery):
    from utils.helpers import is_owner_of_chat
    if not await is_owner_of_chat(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Owner only!", show_alert=True)
    if callback.matches[0].group(1) == "no":
        return await callback.message.edit_text("**❌ Cancelled.**")
    await unapprove_all(callback.message.chat.id)
    await callback.message.edit_text("**✅ All members have been unapproved.**")

@Client.on_message(filters.command("approvelist") & filters.group)
async def approvelist_cmd(client: Client, message: Message):
    docs = await get_approved_users(message.chat.id)
    if not docs:
        return await message.reply("**📋 No approved users in this group.**")
    lines = []
    for i, doc in enumerate(docs, 1):
        uid = doc["user_id"]
        lines.append(f"**{i}. [{uid}](tg://user?id={uid}) - <code>{uid}</code>**")
    await message.reply("\n".join(lines), disable_web_page_preview=True)


# ── PIN ───────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("pin") & filters.group)
async def pin_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if not await bot_has_right(client, message.chat.id, "can_pin_messages"):
        return await message.reply("**❌ I don't have permission to pin messages.**")
    if not message.reply_to_message:
        return await message.reply("**❌ Please reply to a message to pin it.**")
    await message.reply_to_message.pin()
    await message.reply("**📌 Message has been pinned!**")

@Client.on_message(filters.command("unpin") & filters.group)
async def unpin_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if not await bot_has_right(client, message.chat.id, "can_pin_messages"):
        return await message.reply("**❌ I don't have permission to unpin messages.**")
    await client.unpin_chat_message(message.chat.id)
    await message.reply("**📌 Message has been unpinned!**")

@Client.on_message(filters.command("unpinall") & filters.group)
async def unpinall_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Yes, Unpin All", callback_data="unpinall_yes"),
         InlineKeyboardButton("❌ No, Cancel", callback_data="unpinall_no")]
    ])
    await message.reply("**⚠️ Are you sure you want to unpin all messages?**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^unpinall_(yes|no)$"))
async def unpinall_callback(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    if callback.matches[0].group(1) == "no":
        return await callback.message.edit_text("**❌ Cancelled.**")
    await client.unpin_all_chat_messages(callback.message.chat.id)
    await callback.message.edit_text("**✅ All messages have been unpinned!**")


# ── DELEDITMSG ────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("deleditmsg") & filters.group)
async def deleditmsg_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ On", callback_data="deleditmsg_on"),
         InlineKeyboardButton("❌ Off", callback_data="deleditmsg_off")]
    ])
    await message.reply("**⚙️ Set your delete edited message to:**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^deleditmsg_(on|off)$"))
async def deleditmsg_toggle(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    val = callback.matches[0].group(1) == "on"
    await set_setting(callback.message.chat.id, "deleditmsg", val)
    status = "ON ✅" if val else "OFF ❌"
    await callback.message.edit_text(f"**✅ Delete edited message is now {status}**")

@Client.on_message(filters.command("setdelmsgtimer") & filters.group)
async def setdelmsgtimer_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    timer = await get_setting(message.chat.id, "deleditmsg_timer", 5)
    await message.reply(
        f"**⏱️ Set your edited message delete timer\nCurrent: {timer} minutes**",
        reply_markup=_timer_buttons(timer))

def _timer_buttons(timer: int):
    rows = []
    if timer < 30:
        rows.append([InlineKeyboardButton("📈 Increase Timer", callback_data="deltimer_increase")])
    else:
        rows.append([InlineKeyboardButton("🔄 Back to Default", callback_data="deltimer_reset")])
    rows.append([InlineKeyboardButton("✅ Close & Save", callback_data="deltimer_close")])
    return InlineKeyboardMarkup(rows)

@Client.on_callback_query(filters.regex("^deltimer_(increase|reset|close)$"))
async def deltimer_callback(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    action = callback.matches[0].group(1)
    timer = await get_setting(callback.message.chat.id, "deleditmsg_timer", 5)
    if action == "increase" and timer < 30:
        timer += 5
        await set_setting(callback.message.chat.id, "deleditmsg_timer", timer)
    elif action == "reset":
        timer = 5
        await set_setting(callback.message.chat.id, "deleditmsg_timer", timer)
    elif action == "close":
        await set_setting(callback.message.chat.id, "deleditmsg_timer", timer)
        return await callback.message.edit_text(f"**✅ Timer saved: {timer} minutes**")
    await callback.message.edit_text(
        f"**⏱️ Set your edited message delete timer\nCurrent: {timer} minutes**",
        reply_markup=_timer_buttons(timer))

@Client.on_edited_message(filters.group)
async def edited_msg_listener(client: Client, message: Message):
    if not message.from_user:
        return
    if await is_admin(client, message.chat.id, message.from_user.id):
        return
    if await is_approved(message.chat.id, message.from_user.id):
        return
    enabled = await get_setting(message.chat.id, "deleditmsg", False)
    if not enabled:
        return
    timer_mins = await get_setting(message.chat.id, "deleditmsg_timer", 5)
    mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    sent = await message.reply(
        f"**✏️ Edit message detected, {mention} your message and this message will be deleted in {timer_mins} minutes.**",
        disable_web_page_preview=True)
    await asyncio.sleep(timer_mins * 60)
    try:
        await message.delete()
        await sent.delete()
    except Exception:
        pass
