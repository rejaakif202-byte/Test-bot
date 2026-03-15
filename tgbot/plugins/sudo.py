from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import time

from utils.helpers import get_target_user, MUTE_PERMISSIONS, format_duration
from database.helpers import (
    gban_user, ungban_user, is_gbanned, get_gban, get_gban_list,
    gmute_user, ungmute_user, is_gmuted, get_gmute_list,
    add_sudo, remove_sudo, get_sudo_users, is_sudo_db,
    block_user, unblock_user, is_blocked,
    get_all_groups, get_all_users, total_groups, total_users,
    save_user
)
from config import Config
import datetime


# ── GBAN ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("gban"))
async def gban_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    if target.id == Config.OWNER_ID:
        return await message.reply("**❌ You can't gban the owner.**")
    if await is_gbanned(target.id):
        return await message.reply(f"**⚠️ [{target.first_name}](tg://user?id={target.id}) is already globally banned.**",
                                   disable_web_page_preview=True)
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
    await gban_user(target.id, reason)

    groups = await get_all_groups()
    banned = 0
    for grp in groups:
        try:
            await client.ban_chat_member(grp["_id"], target.id)
            banned += 1
        except Exception:
            pass

    await message.reply(
        f"**🌐🚫 [{target.first_name}](tg://user?id={target.id}) has been globally banned in {banned} groups.\nReason: {reason}**",
        disable_web_page_preview=True)


@Client.on_message(filters.command("ungban"))
async def ungban_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    if not await is_gbanned(target.id):
        return await message.reply(f"**⚠️ [{target.first_name}](tg://user?id={target.id}) is not globally banned.**",
                                   disable_web_page_preview=True)
    await ungban_user(target.id)
    groups = await get_all_groups()
    for grp in groups:
        try:
            await client.unban_chat_member(grp["_id"], target.id)
        except Exception:
            pass
    await message.reply(f"**✅ [{target.first_name}](tg://user?id={target.id}) has been globally unbanned.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("gbanlist"))
async def gbanlist_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    docs = await get_gban_list()
    if not docs:
        return await message.reply("**📋 No users are globally banned.**")
    lines = []
    for i, doc in enumerate(docs, 1):
        uid = doc["_id"]
        try:
            user = await client.get_users(uid)
            name = f"[{user.first_name}](tg://user?id={uid})"
        except Exception:
            name = f"[Unknown](tg://user?id={uid})"
        lines.append(f"**{i}. {name} - `{uid}`**")
    await message.reply("\n".join(lines), disable_web_page_preview=True)


# ── GMUTE ─────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("gmute"))
async def gmute_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    if await is_gmuted(target.id):
        return await message.reply(f"**⚠️ [{target.first_name}](tg://user?id={target.id}) is already globally muted.**",
                                   disable_web_page_preview=True)
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
    await gmute_user(target.id, reason)
    groups = await get_all_groups()
    muted = 0
    for grp in groups:
        try:
            await client.restrict_chat_member(grp["_id"], target.id, MUTE_PERMISSIONS)
            muted += 1
        except Exception:
            pass
    await message.reply(
        f"**🌐🔇 [{target.first_name}](tg://user?id={target.id}) has been globally muted in {muted} groups.\nReason: {reason}**",
        disable_web_page_preview=True)


@Client.on_message(filters.command("ungmute"))
async def ungmute_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    if not await is_gmuted(target.id):
        return await message.reply(f"**⚠️ [{target.first_name}](tg://user?id={target.id}) is not globally muted.**",
                                   disable_web_page_preview=True)
    await ungmute_user(target.id)
    from utils.helpers import UNMUTE_PERMISSIONS
    groups = await get_all_groups()
    for grp in groups:
        try:
            await client.restrict_chat_member(grp["_id"], target.id, UNMUTE_PERMISSIONS)
        except Exception:
            pass
    await message.reply(f"**✅ [{target.first_name}](tg://user?id={target.id}) has been globally unmuted.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("gmutelist"))
async def gmutelist_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    docs = await get_gmute_list()
    if not docs:
        return await message.reply("**📋 No users are globally muted.**")
    lines = []
    for i, doc in enumerate(docs, 1):
        uid = doc["_id"]
        try:
            user = await client.get_users(uid)
            name = f"[{user.first_name}](tg://user?id={uid})"
        except Exception:
            name = f"[Unknown](tg://user?id={uid})"
        lines.append(f"**{i}. {name} - `{uid}`**")
    await message.reply("\n".join(lines), disable_web_page_preview=True)


# ── SUDO ──────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("addsudo") & (filters.group | filters.private))
async def addsudo_cmd(client: Client, message: Message):
    if not Config.is_owner(message.from_user.id):
        return await message.reply("**❌ This command is for the bot owner only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    await add_sudo(target.id)
    await message.reply(f"**✅ [{target.first_name}](tg://user?id={target.id}) has been added as a sudo user.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("remsudo") & (filters.group | filters.private))
async def remsudo_cmd(client: Client, message: Message):
    if not Config.is_owner(message.from_user.id):
        return await message.reply("**❌ This command is for the bot owner only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    await remove_sudo(target.id)
    await message.reply(f"**❌ [{target.first_name}](tg://user?id={target.id}) has been removed from sudo users.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("sudolist")) & (filters.group | filters.private))
async def sudolist_cmd(client: Client, message: Message):
    sudo_ids = await get_sudo_users()
    try:
        owner = await client.get_users(Config.OWNER_ID)
        owner_name = f"[{owner.first_name}](tg://user?id={Config.OWNER_ID})"
    except Exception:
        owner_name = f"[Owner](tg://user?id={Config.OWNER_ID})"

    lines = [f"**👑 Owner**\n\n1. {owner_name}\n\n**⭐ Admin**\n"]
    i = 2
    for uid in sudo_ids:
        try:
            user = await client.get_users(uid)
            name = f"[{user.first_name}](tg://user?id={uid})"
        except Exception:
            name = f"[Unknown](tg://user?id={uid})"
        lines.append(f"{i}. {name}")
        i += 1

    if i == 2:
        lines.append("_No sudo admins added yet._")
    await message.reply("\n".join(lines), disable_web_page_preview=True)


# ── BLOCK / UNBLOCK ───────────────────────────────────────────────────────────

@Client.on_message(filters.command("block"))
async def block_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    await block_user(target.id)
    await message.reply(f"**🔒 [{target.first_name}](tg://user?id={target.id}) has been blocked from using this bot.**",
                        disable_web_page_preview=True)


@Client.on_message(filters.command("unblock"))
async def unblock_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")
    target = await get_target_user(client, message)
    if not target:
        return await message.reply("**❌ Please provide a username or user ID.**")
    await unblock_user(target.id)
    await message.reply(f"**🔓 [{target.first_name}](tg://user?id={target.id}) has been unblocked.**",
                        disable_web_page_preview=True)


# ── BROADCAST ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("broadcast"))
async def broadcast_cmd(client: Client, message: Message):
    if not Config.is_owner(message.from_user.id):
        return await message.reply("**❌ This command is for the bot owner only.**")
    if not message.reply_to_message:
        return await message.reply("**❌ Please reply to a message to broadcast.**")

    status_msg = await message.reply("**📣 Broadcast beginning...**")

    groups = await get_all_groups()
    users = await get_all_users()

    success_groups = fail_groups = success_users = fail_users = 0

    for grp in groups:
        try:
            await message.reply_to_message.copy(grp["_id"])
            success_groups += 1
        except Exception:
            fail_groups += 1
        await asyncio.sleep(0.05)

    for usr in users:
        try:
            await message.reply_to_message.copy(usr["_id"])
            success_users += 1
        except Exception:
            fail_users += 1
        await asyncio.sleep(0.05)

    await status_msg.delete()
    await message.reply(
        f"**📣 Broadcast completed\n\n"
        f"✅ Successful: {success_groups} groups, {success_users} users\n"
        f"❌ Unsuccessful: {fail_groups} groups, {fail_users} users**"
    )


# ── STATS ─────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("stats"))
async def stats_cmd(client: Client, message: Message):
    if not await is_sudo_db(message.from_user.id):
        return await message.reply("**❌ This command is for sudo users only.**")

    start_time = time.time()
    ping_msg = await message.reply("**📡 Calculating...**")
    ping = round((time.time() - start_time) * 1000, 2)

    uptime = "N/A"
    if Config.BOT_START_TIME:
        delta = datetime.datetime.utcnow() - Config.BOT_START_TIME
        uptime = format_duration(delta.total_seconds())

    groups = await total_groups()
    users = await total_users()

    text = (
        f"**🤖 Bot Statistics**\n\n"
        f"**📊 Total Groups:** `{groups}`\n"
        f"**👥 Total Users:** `{users}`\n"
        f"**📡 Ping:** `{ping}ms`\n"
        f"**⏱️ Uptime:** `{uptime}`"
    )
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])

    await ping_msg.delete()
    try:
        from plugins.start import START_IMAGE
        await message.reply_photo(START_IMAGE, caption=text, reply_markup=buttons)
    except Exception:
        await message.reply(text, reply_markup=buttons)
