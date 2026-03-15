from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from database.helpers import save_user, save_group
from utils.helpers import format_duration
import datetime

START_IMAGE = "assets/start.jpg"  # Place your start image here

def get_uptime():
    if not Config.BOT_START_TIME:
        return "Just started"
    delta = datetime.datetime.utcnow() - Config.BOT_START_TIME
    return format_duration(delta.total_seconds())


# ── START ─────────────────────────────────────────────────────────────────────

@Client.on_message(filters.command("start") & filters.private)
async def start_private(client: Client, message: Message):
    user = message.from_user
    await save_user(user.id, user.username, user.first_name)
    mention = f"**[{user.first_name}](tg://user?id={user.id})**"

    text = (
        f"**Hey There, {mention}! This is {Config.BOT_NAME}.**\n\n"
        f"**This is a powerful group management bot for managing your group with all the security.**\n\n"
        f"**Type /help to know my all commands and how to use me.**"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me in your group", url=Config.ADD_GROUP_LINK)],
        [
            InlineKeyboardButton("📢 Support Channel", url=Config.SUPPORT_CHANNEL),
            InlineKeyboardButton("👤 Creator", url=Config.CREATOR_LINK)
        ],
        [InlineKeyboardButton("📋 Commands", callback_data="help_menu")]
    ])

    try:
        await message.reply_photo(START_IMAGE, caption=text, reply_markup=buttons)
    except Exception:
        await message.reply(text, reply_markup=buttons, disable_web_page_preview=True)


@Client.on_message(filters.command("start") & filters.group)
async def start_group(client: Client, message: Message):
    await save_group(message.chat.id, message.chat.title)
    uptime = get_uptime()
    text = (
        f"**{Config.BOT_NAME} is alive again.**\n\n"
        f"**I didn't sleep since - {uptime}**"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add me", url=Config.ADD_GROUP_LINK),
            InlineKeyboardButton("📢 Support Channel", url=Config.SUPPORT_CHANNEL)
        ]
    ])
    try:
        await message.reply_photo(START_IMAGE, caption=text, reply_markup=buttons)
    except Exception:
        await message.reply(text, reply_markup=buttons, disable_web_page_preview=True)


# ── HELP ──────────────────────────────────────────────────────────────────────

ADMIN_COMMANDS = [
    "mute", "unmute", "smute", "tmute", "dmute",
    "ban", "unban", "sban", "tban", "dban",
    "warn", "unwarn", "swarn", "twarn", "dwarn", "setwarnlimit",
    "kick", "del", "purge",
    "block", "unblock",
    "blacklist", "unblacklist", "allblacklist",
    "blacklistchat", "whitelistchat", "allblacklistchats",
    "pin", "unpin", "unpinall",
    "lock", "unlock", "locktypes",
    "welcome", "setwelcome", "resetwelcome",
    "goodbye", "setgoodbye", "resetgoodbye",
    "deleditmsg", "setdelmsgtimer",
    "approve", "unapprove", "approveall", "unapproveall", "approvelist",
    "filter", "stop", "stopall", "filters",
    "addsudo", "remsudo", "sudolist",
    "gban", "ungban", "gbanlist",
    "gmute", "ungmute", "gmutelist",
    "promote", "fullpromote", "demote", "demoteall",
    "tagall", "stoptagall",
    "antiflood", "setfloodtype", "setfloodlimit",
    "broadcast", "stats", "adminlist",
]

MEMBER_COMMANDS = [
    "start", "help", "id", "info", "afk",
    "font", "gpt", "yt", "ig", "report",
]

COMMAND_HELP = {
    "mute": "**🔇 /mute** — Mute a user in the group.\nUsage: Reply to a message or use `/mute @username`",
    "unmute": "**🔊 /unmute** — Unmute a muted user.\nUsage: Reply or `/unmute @username`",
    "smute": "**🔇 /smute** — Silently mute a user (no notification).",
    "tmute": "**⏳ /tmute** — Temporarily mute. Usage: `/tmute @user 1h`\nFormats: s, m, h, d",
    "dmute": "**🗑️ /dmute** — Delete message and mute the user.",
    "ban": "**🚫 /ban** — Ban a user from the group.",
    "unban": "**✅ /unban** — Unban a user.",
    "sban": "**🚫 /sban** — Silently ban (no notification).",
    "tban": "**⏳ /tban** — Temporarily ban. Usage: `/tban @user 2d`",
    "dban": "**🗑️ /dban** — Delete message and ban the user.",
    "warn": "**⚠️ /warn** — Warn a user. Limit reached = auto ban.",
    "unwarn": "**✅ /unwarn** — Remove one warning from a user.",
    "swarn": "**⚠️ /swarn** — Silently warn a user.",
    "twarn": "**⏳ /twarn** — Temporarily warn. Usage: `/twarn @user 1h`",
    "dwarn": "**🗑️ /dwarn** — Delete message and warn the user.",
    "setwarnlimit": "**⚙️ /setwarnlimit** — Set warning limit (3-5). Button to increase.",
    "kick": "**👢 /kick** — Kick a user (they can rejoin).",
    "del": "**🗑️ /del** — Delete a replied message silently.",
    "purge": "**🧹 /purge** — Delete all messages from replied message to latest.",
    "block": "**🔒 /block** — Block a user from using the bot privately. (Sudo only)",
    "unblock": "**🔓 /unblock** — Unblock a user. (Sudo only)",
    "blacklist": "**🚫 /blacklist** — Blacklist a word/sticker/link in the group.",
    "unblacklist": "**✅ /unblacklist** — Remove a word from blacklist.",
    "allblacklist": "**📋 /allblacklist** — Show all blacklisted items.",
    "blacklistchat": "**🚫 /blacklistchat** — Bot will leave and block a group/channel. (Sudo only)",
    "whitelistchat": "**✅ /whitelistchat** — Remove a chat from blacklist. (Sudo only)",
    "allblacklistchats": "**📋 /allblacklistchats** — Show all blacklisted chats. (Sudo only)",
    "pin": "**📌 /pin** — Pin a replied message.",
    "unpin": "**📌 /unpin** — Unpin the last pinned message.",
    "unpinall": "**📌 /unpinall** — Unpin all messages (with confirmation).",
    "lock": "**🔒 /lock** — Lock a content type. Usage: `/lock text`",
    "unlock": "**🔓 /unlock** — Unlock a content type. Usage: `/unlock text`",
    "locktypes": "**📋 /locktypes** — Show all lockable types.",
    "welcome": "**👋 /welcome** — Toggle welcome message on/off.",
    "setwelcome": "**⚙️ /setwelcome** — Set a custom welcome message.",
    "resetwelcome": "**🔄 /resetwelcome** — Reset to default welcome message.",
    "goodbye": "**👋 /goodbye** — Toggle goodbye message on/off.",
    "setgoodbye": "**⚙️ /setgoodbye** — Set a custom goodbye message.",
    "resetgoodbye": "**🔄 /resetgoodbye** — Reset to default goodbye message.",
    "deleditmsg": "**✏️ /deleditmsg** — Toggle deletion of edited messages for unapproved users.",
    "setdelmsgtimer": "**⏱️ /setdelmsgtimer** — Set timer for deleting edited messages (5-30 mins).",
    "approve": "**✅ /approve** — Approve a user (bypass lock/blacklist/deleditmsg).",
    "unapprove": "**❌ /unapprove** — Remove approval from a user.",
    "approveall": "**✅ /approveall** — Approve all members (Owner only).",
    "unapproveall": "**❌ /unapproveall** — Unapprove all members (Owner only).",
    "approvelist": "**📋 /approvelist** — Show all approved users.",
    "filter": "**🔍 /filter** — Set a keyword filter with response/buttons.",
    "stop": "**⛔ /stop** — Stop a specific filter.",
    "stopall": "**⛔ /stopall** — Stop all filters (with confirmation).",
    "filters": "**📋 /filters** — Show all active filters.",
    "addsudo": "**⭐ /addsudo** — Add a sudo user. (Owner only)",
    "remsudo": "**❌ /remsudo** — Remove a sudo user. (Owner only)",
    "sudolist": "**📋 /sudolist** — Show owner and sudo users.",
    "gban": "**🌐🚫 /gban** — Globally ban a user from all groups. (Sudo only)",
    "ungban": "**✅ /ungban** — Remove a global ban. (Sudo only)",
    "gbanlist": "**📋 /gbanlist** — Show all globally banned users.",
    "gmute": "**🌐🔇 /gmute** — Globally mute a user in all groups. (Sudo only)",
    "ungmute": "**✅ /ungmute** — Remove a global mute. (Sudo only)",
    "gmutelist": "**📋 /gmutelist** — Show all globally muted users.",
    "promote": "**⭐ /promote** — Promote a user to admin.",
    "fullpromote": "**🌟 /fullpromote** — Promote with full admin rights. (Owner only)",
    "demote": "**📉 /demote** — Demote a bot-promoted admin.",
    "demoteall": "**📉 /demoteall** — Demote all bot-promoted admins. (Owner only)",
    "tagall": "**📢 /tagall** — Tag all group members.",
    "stoptagall": "**⛔ /stoptagall** — Stop an ongoing tagall.",
    "antiflood": "**🚨 /antiflood** — Toggle anti-flood protection on/off.",
    "setfloodtype": "**⚙️ /setfloodtype** — Set action for flood (ban/mute/kick/warn).",
    "setfloodlimit": "**⚙️ /setfloodlimit** — Set flood message limit (5-20).",
    "broadcast": "**📣 /broadcast** — Broadcast a message to all groups and users. (Owner only)",
    "stats": "**📊 /stats** — Show bot statistics. (Sudo only)",
    "adminlist": "**👮 /adminlist** — Show all admins in the group.",
    "start": "**🚀 /start** — Start the bot.",
    "help": "**❓ /help** — Show this help menu.",
    "id": "**🆔 /id** — Get user ID, group ID, or channel ID.",
    "info": "**ℹ️ /info** — Get detailed info about a user.",
    "afk": "**💤 /afk** — Set yourself as AFK with optional reason.",
    "font": "**🔤 /font** — Convert text to fancy fonts. Usage: `/font your text`",
    "gpt": "**🤖 /gpt** — Ask ChatGPT anything. Usage: `/gpt your question`",
    "yt": "**▶️ /yt** — Download a YouTube video. Usage: `/yt link`",
    "ig": "**📸 /ig** — Download an Instagram reel. Usage: `/ig link`",
    "report": "**🚨 /report or @admin** — Report a message to all admins.",
}

def build_help_buttons():
    all_cmds = ADMIN_COMMANDS + MEMBER_COMMANDS
    rows = []
    for i in range(0, len(all_cmds), 3):
        row = [InlineKeyboardButton(f"/{cmd}", callback_data=f"help_{cmd}") for cmd in all_cmds[i:i+3]]
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Close", callback_data="close")])
    return InlineKeyboardMarkup(rows)


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    text = "**Click on any command button to know how it works!**"
    buttons = build_help_buttons()
    try:
        await message.reply_photo(START_IMAGE, caption=text, reply_markup=buttons)
    except Exception:
        await message.reply(text, reply_markup=buttons)


@Client.on_callback_query(filters.regex(r"^help_(.+)$"))
async def help_callback(client: Client, callback: CallbackQuery):
    cmd = callback.matches[0].group(1)
    if cmd == "menu":
        text = "**Click on any command button to know how it works!**"
        buttons = build_help_buttons()
        try:
            await callback.message.edit_caption(caption=text, reply_markup=buttons)
        except Exception:
            await callback.message.edit_text(text, reply_markup=buttons)
        return

    help_text = COMMAND_HELP.get(cmd, f"**No help available for /{cmd}**")
    back_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="help_menu")]
    ])
    try:
        await callback.message.edit_caption(caption=help_text, reply_markup=back_button)
    except Exception:
        await callback.message.edit_text(help_text, reply_markup=back_button)


@Client.on_callback_query(filters.regex("^close$"))
async def close_callback(client: Client, callback: CallbackQuery):
    await callback.message.delete()
