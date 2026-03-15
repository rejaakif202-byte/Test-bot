from pyrogram import Client, filters
from pyrogram.types import (Message, ChatMemberUpdated,
                             InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery)
from database.helpers import (save_user, save_group, is_gbanned, is_gmuted,
                               get_setting, set_setting)
from utils.helpers import is_admin, MUTE_PERMISSIONS
from config import Config

WELCOME_KEYWORDS = ["{first_name}", "{mention}", "{uid}", "{chatname}", "{username}", "{last_name}"]

def fill_keywords(text: str, user, chat) -> str:
    mention = f"[{user.first_name}](tg://user?id={user.id})"
    return (text
            .replace("{first_name}", user.first_name or "")
            .replace("{last_name}", user.last_name or "")
            .replace("{mention}", mention)
            .replace("{uid}", str(user.id))
            .replace("{chatname}", chat.title or "")
            .replace("{username}", f"@{user.username}" if user.username else "@none"))

DEFAULT_WELCOME = "**Hey there {first_name}, welcome to {chatname}. How are you!?**"
DEFAULT_GOODBYE = "**Goodbye {first_name}, we'll miss you in {chatname}!**"


@Client.on_chat_member_updated()
async def member_update(client: Client, update: ChatMemberUpdated):
    if not update.chat or update.chat.type not in ("group", "supergroup"):
        return
    user = (update.new_chat_member.user if update.new_chat_member
            else update.old_chat_member.user if update.old_chat_member else None)
    if not user or user.is_bot:
        return

    await save_user(user.id, user.username, user.first_name)
    await save_group(update.chat.id, update.chat.title)

    old_status = update.old_chat_member.status if update.old_chat_member else None
    new_status = update.new_chat_member.status if update.new_chat_member else None

    # User joined
    if old_status in (None, "left", "kicked") and new_status == "member":
        # Gban check
        if await is_gbanned(user.id):
            await client.ban_chat_member(update.chat.id, user.id)
            await client.send_message(update.chat.id,
                f"**🌐🚫 [{user.first_name}](tg://user?id={user.id}) is globally banned and was removed.**",
                disable_web_page_preview=True)
            return
        # Gmute check
        if await is_gmuted(user.id):
            await client.restrict_chat_member(update.chat.id, user.id, MUTE_PERMISSIONS)

        # Welcome
        welcome_on = await get_setting(update.chat.id, "welcome_on", True)
        if welcome_on:
            welcome_text = await get_setting(update.chat.id, "welcome_text", DEFAULT_WELCOME)
            welcome_media = await get_setting(update.chat.id, "welcome_media", None)
            text = fill_keywords(welcome_text, user, update.chat)
            if welcome_media:
                await client.send_photo(update.chat.id, welcome_media, caption=text)
            else:
                await client.send_message(update.chat.id, text, disable_web_page_preview=True)

    # User left
    elif old_status == "member" and new_status in ("left", None):
        goodbye_on = await get_setting(update.chat.id, "goodbye_on", True)
        if goodbye_on:
            goodbye_text = await get_setting(update.chat.id, "goodbye_text", DEFAULT_GOODBYE)
            text = fill_keywords(goodbye_text, user, update.chat)
            await client.send_message(update.chat.id, text, disable_web_page_preview=True)

    # Bot added to group
    me = await client.get_me()
    if update.new_chat_member and update.new_chat_member.user.id == me.id:
        await save_group(update.chat.id, update.chat.title)
        from config import Config
        text = (
            f"**Wassup Groupmates!**\n\n"
            f"**Thanks for adding {Config.BOT_NAME} in {update.chat.title}.**\n"
            f"**Make me admin to use all my features.**\n\n"
            f"**Type /help to see commands.**"
        )
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 Commands", callback_data="help_menu"),
                InlineKeyboardButton("📢 Support Channel", url=Config.SUPPORT_CHANNEL)
            ]
        ])
        try:
            from plugins.start import START_IMAGE
            await client.send_photo(update.chat.id, START_IMAGE, caption=text, reply_markup=buttons)
        except Exception:
            await client.send_message(update.chat.id, text, reply_markup=buttons, disable_web_page_preview=True)


# ── WELCOME COMMANDS ──────────────────────────────────────────────────────────

@Client.on_message(filters.command("welcome") & filters.group)
async def welcome_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    current = await get_setting(message.chat.id, "welcome_on", True)
    status = "ON ✅" if current else "OFF ❌"
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ON", callback_data="welcome_on"),
            InlineKeyboardButton("❌ OFF", callback_data="welcome_off")
        ]
    ])
    await message.reply(f"**Set your welcome here\nCurrent: {status}**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^welcome_(on|off)$"))
async def welcome_toggle(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    val = callback.matches[0].group(1) == "on"
    await set_setting(callback.message.chat.id, "welcome_on", val)
    status = "ON ✅" if val else "OFF ❌"
    await callback.message.edit_text(f"**Welcome message is now {status}**")

@Client.on_message(filters.command("setwelcome") & filters.group)
async def set_welcome(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or DEFAULT_WELCOME
        media = None
        if message.reply_to_message.photo:
            media = message.reply_to_message.photo.file_id
        await set_setting(message.chat.id, "welcome_text", text)
        if media:
            await set_setting(message.chat.id, "welcome_media", media)
        return await message.reply("**✅ Welcome message has been set!**")
    elif len(message.command) > 1:
        text = " ".join(message.command[1:])
        await set_setting(message.chat.id, "welcome_text", text)
        return await message.reply("**✅ Welcome message has been set!**")
    await message.reply("**❌ Please provide a message or reply to one.**")

@Client.on_message(filters.command("resetwelcome") & filters.group)
async def reset_welcome(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    await set_setting(message.chat.id, "welcome_text", DEFAULT_WELCOME)
    await set_setting(message.chat.id, "welcome_media", None)
    await message.reply("**✅ Welcome message has been reset to default.**")

@Client.on_message(filters.command("goodbye") & filters.group)
async def goodbye_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    current = await get_setting(message.chat.id, "goodbye_on", True)
    status = "ON ✅" if current else "OFF ❌"
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ ON", callback_data="goodbye_on"),
            InlineKeyboardButton("❌ OFF", callback_data="goodbye_off")
        ]
    ])
    await message.reply(f"**Set your goodbye here\nCurrent: {status}**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^goodbye_(on|off)$"))
async def goodbye_toggle(client: Client, callback: CallbackQuery):
    if not await is_admin(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Admins only!", show_alert=True)
    val = callback.matches[0].group(1) == "on"
    await set_setting(callback.message.chat.id, "goodbye_on", val)
    status = "ON ✅" if val else "OFF ❌"
    await callback.message.edit_text(f"**Goodbye message is now {status}**")

@Client.on_message(filters.command("setgoodbye") & filters.group)
async def set_goodbye(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or DEFAULT_GOODBYE
        media = None
        if message.reply_to_message.photo:
            media = message.reply_to_message.photo.file_id
        await set_setting(message.chat.id, "goodbye_text", text)
        if media:
            await set_setting(message.chat.id, "goodbye_media", media)
        return await message.reply("**✅ Goodbye message has been set!**")
    elif len(message.command) > 1:
        text = " ".join(message.command[1:])
        await set_setting(message.chat.id, "goodbye_text", text)
        return await message.reply("**✅ Goodbye message has been set!**")
    await message.reply("**❌ Please provide a message or reply to one.**")

@Client.on_message(filters.command("resetgoodbye") & filters.group)
async def reset_goodbye(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    await set_setting(message.chat.id, "goodbye_text", DEFAULT_GOODBYE)
    await set_setting(message.chat.id, "goodbye_media", None)
    await message.reply("**✅ Goodbye message has been reset to default.**")
