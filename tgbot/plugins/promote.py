from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils.helpers import is_admin, is_owner_of_chat, get_target_user, check_bot_admin, bot_has_right, admin_has_right, is_user_in_chat
from database.helpers import save_promoted, is_promoted_by_bot, remove_promoted, remove_all_promoted
from config import Config

PROMOTE_PRIVILEGES = ChatPrivileges(
    can_manage_chat=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_manage_video_chats=True,
    can_promote_members=False,
    can_change_info=True,
    can_edit_messages=False,
    is_anonymous=False,
)

FULL_PROMOTE_PRIVILEGES = ChatPrivileges(
    can_manage_chat=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_invite_users=True,
    can_pin_messages=True,
    can_manage_video_chats=True,
    can_promote_members=True,
    can_change_info=True,
    can_edit_messages=True,
    is_anonymous=False,
)

DEMOTE_PRIVILEGES = ChatPrivileges(
    can_manage_chat=False,
    can_delete_messages=False,
    can_restrict_members=False,
    can_invite_users=False,
    can_pin_messages=False,
    can_manage_video_chats=False,
    can_promote_members=False,
    can_change_info=False,
    is_anonymous=False,
)


@Client.on_message(filters.command("promote") & filters.group)
async def promote_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin to use this command.**")
    if not await admin_has_right(client, message.chat.id, message.from_user.id, "can_promote_members"):
        return await message.reply("**❌ You don't have permission to promote members.**")
    if not await bot_has_right(client, message.chat.id, "can_promote_members"):
        return await message.reply("**❌ I don't have full admin rights to promote members.**")

    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    if not await is_user_in_chat(client, message.chat.id, target.id):
        return await message.reply("**❌ This user is not in the group.**")

    await client.promote_chat_member(message.chat.id, target.id, PROMOTE_PRIVILEGES)
    await save_promoted(message.chat.id, target.id)
    await message.reply(f"**⭐ [{target.first_name}](tg://user?id={target.id}) has been promoted.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("fullpromote") & filters.group)
async def fullpromote_cmd(client: Client, message: Message):
    # Special owner self-promote feature
    if message.from_user.id == Config.OWNER_ID:
        if not await bot_has_right(client, message.chat.id, "can_promote_members"):
            return await message.reply("**❌ I don't have full admin rights.**")
        # If owner is replying to their own message
        target = message.from_user
        if message.reply_to_message and message.reply_to_message.from_user:
            target = message.reply_to_message.from_user
            if target.id != Config.OWNER_ID:
                # Normal fullpromote for others by owner
                if not await is_owner_of_chat(client, message.chat.id, message.from_user.id):
                    return await message.reply("**❌ Only the group owner can use /fullpromote.**")
                await client.promote_chat_member(message.chat.id, target.id, FULL_PROMOTE_PRIVILEGES)
                await save_promoted(message.chat.id, target.id)
                return await message.reply(
                    f"**🌟 [{target.first_name}](tg://user?id={target.id}) has been fully promoted.**",
                    disable_web_page_preview=True)
        # Owner self-promote
        await client.promote_chat_member(message.chat.id, Config.OWNER_ID, FULL_PROMOTE_PRIVILEGES)
        return await message.reply(f"**🌟 [{target.first_name}](tg://user?id={target.id}) has been fully promoted with all rights.**",
                                   disable_web_page_preview=True)

    if not await is_owner_of_chat(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ Only the group owner can use /fullpromote.**")
    if not await bot_has_right(client, message.chat.id, "can_promote_members"):
        return await message.reply("**❌ I don't have full admin rights to promote members.**")

    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")
    if not await is_user_in_chat(client, message.chat.id, target.id):
        return await message.reply("**❌ This user is not in the group.**")

    await client.promote_chat_member(message.chat.id, target.id, FULL_PROMOTE_PRIVILEGES)
    await save_promoted(message.chat.id, target.id)
    await message.reply(f"**🌟 [{target.first_name}](tg://user?id={target.id}) has been fully promoted.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("demote") & filters.group)
async def demote_cmd(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ You must be an admin.**")
    if not await bot_has_right(client, message.chat.id, "can_promote_members"):
        return await message.reply("**❌ I don't have permission to demote members.**")

    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please reply to a user or provide a username/ID.**")

    if not await is_promoted_by_bot(message.chat.id, target.id):
        return await message.reply("**❌ This admin was not promoted by me, I can't demote them.**")

    await client.promote_chat_member(message.chat.id, target.id, DEMOTE_PRIVILEGES)
    await remove_promoted(message.chat.id, target.id)
    await message.reply(f"**📉 [{target.first_name}](tg://user?id={target.id}) has been demoted.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("demoteall") & filters.group)
async def demoteall_cmd(client: Client, message: Message):
    if not await is_owner_of_chat(client, message.chat.id, message.from_user.id):
        return await message.reply("**❌ Only the group owner can use /demoteall.**")
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Yes", callback_data="demoteall_yes"),
            InlineKeyboardButton("❌ No", callback_data="demoteall_no")
        ]
    ])
    await message.reply("**⚠️ Are you sure you want to demote all bot-promoted admins?**", reply_markup=buttons)

@Client.on_callback_query(filters.regex("^demoteall_(yes|no)$"))
async def demoteall_callback(client: Client, callback: CallbackQuery):
    if not await is_owner_of_chat(client, callback.message.chat.id, callback.from_user.id):
        return await callback.answer("❌ Owner only!", show_alert=True)
    action = callback.matches[0].group(1)
    if action == "no":
        return await callback.message.edit_text("**❌ Cancelled.**")
    admins = await client.get_chat_members(callback.message.chat.id, filter="administrators")
    me = await client.get_me()
    demoted = 0
    for admin in admins:
        if admin.user.id == me.id or admin.status == "creator":
            continue
        if await is_promoted_by_bot(callback.message.chat.id, admin.user.id):
            try:
                await client.promote_chat_member(callback.message.chat.id, admin.user.id, DEMOTE_PRIVILEGES)
                await remove_promoted(callback.message.chat.id, admin.user.id)
                demoted += 1
            except Exception:
                pass
    await callback.message.edit_text(f"**📉 Done! {demoted} bot-promoted admins have been demoted.**")


@Client.on_message(filters.command("adminlist") & filters.group)
async def adminlist_cmd(client: Client, message: Message):
    admins = await client.get_chat_members(message.chat.id, filter="administrators")
    lines = []
    i = 1
    for admin in admins:
        name = admin.user.first_name or "Unknown"
        uid = admin.user.id
        role = "👑 Owner" if admin.status == "creator" else "⭐ Admin"
        lines.append(f"{i}. {role} — [{name}](tg://user?id={uid})")
        i += 1
    text = "**👮 Admins in this group:**\n\n" + "\n".join(lines)
    await message.reply(text, disable_web_page_preview=True)
