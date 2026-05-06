import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
import asyncio
from datetime import datetime
def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except:
        return {}

def save(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(d, f, indent=4)

STAFF_FILE = "data/staff.json"

def get_staff():
    return load(STAFF_FILE)

def is_bot_owner(bot, user_id):
    return user_id == bot.owner_id

def get_level(bot, user_id):
    staff = get_staff()
    if is_bot_owner(bot, user_id):
        return "bot_owner"
    if str(user_id) in staff.get("owners", []):
        return "owner"
    if str(user_id) in staff.get("admins", []):
        return "admin"
    if str(user_id) in staff.get("mods", []):
        return "mod"
    return "user"

def require(level):
    """Checks the permission of the mofo"""
    async def predicate(ctx):
        if isinstance(ctx, discord.Interaction):
            user = ctx.user
        else:
            user = ctx.author
        user_level = get_level(ctx.bot, user.id)
        levels = {"bot_owner": 4, "owner": 3, "admin": 2, "mod": 1, "user": 0}
        if levels.get(user_level, 0) >= levels.get(level, 0):
            return True
        raise commands.CheckFailure(message=f"Only **{level}** permissions can use this command.")
    return commands.check(predicate)

def make_embed(ctx, title, desc, color):
    user = ctx.user if isinstance(ctx, discord.Interaction) else ctx.author
    guild = ctx.guild
    embed = discord.Embed(
        title=title,
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    embed.set_author(
        name=guild.name,
        icon_url=guild.icon.url if guild.icon else None
    )
    embed.set_footer(
        text=f"Action by {user}",
        icon_url=user.display_avatar.url
    )
    return embed

def error(ctx, msg):
    return make_embed(ctx, "❌ Error", msg, 0xe74c3c)

# ═══════════════ TIME PARSER ═══════════════
def parse_time(t):
    unit = t[-1]
    try:
        val = int(t[:-1])
    except:
        return 0
    return {"s": val, "m": val*60, "h": val*3600, "d": val*86400}.get(unit, 0)

# ═══════════════ MODERATION COG ═══════════════
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_mutes.start()
        self.snipe_data = {}
        self.edit_snipe_data = {}

    def cog_unload(self):
        self.check_mutes.cancel()

    # ---------- helpers ----------
    def can_target(self, actor, target):
        if actor == target:
            return False
        if target.top_role >= actor.top_role:
            return False
        return True

    async def send(self, ctx, emb):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=emb)
        else:
            await ctx.send(embed=emb)

    # ═══════════ SNIPE / EDITSNIPE LISTENERS ═══════════
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        self.snipe_data[message.channel.id] = {
            "author": message.author,
            "content": message.content,
            "timestamp": message.created_at,
            "attachments": [att.url for att in message.attachments]
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return
        self.edit_snipe_data[before.channel.id] = {
            "author": before.author,
            "old_content": before.content,
            "new_content": after.content,
            "timestamp": before.created_at
        }

    # ═══════════ SNIPE / EDITSNIPE COMMANDS ═══════════
    async def snipe_logic(self, ctx, channel: discord.TextChannel = None):
        chan = channel or ctx.channel
        data = self.snipe_data.get(chan.id)
        if not data:
            return await self.send(ctx, error(ctx, "Nothing to snipe here."))
        embed = make_embed(ctx, "📸 Snipe", "", 0x3498db)
        embed.add_field(name="Author", value=data["author"].mention)
        embed.add_field(name="Message", value=data["content"] or "**[No text / Embed]**")
        if data["attachments"]:
            embed.add_field(name="Attachments", value="\n".join(data["attachments"]), inline=False)
        embed.set_footer(text=f"Deleted at {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        await self.send(ctx, embed)

    @commands.command(aliases=["sn", "s"])
    @require("mod")
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        await self.snipe_logic(ctx, channel)

    @app_commands.command(name="snipe")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_snipe(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await self.snipe_logic(interaction, channel)

    async def editsnipe_logic(self, ctx, channel: discord.TextChannel = None):
        chan = channel or ctx.channel
        data = self.edit_snipe_data.get(chan.id)
        if not data:
            return await self.send(ctx, error(ctx, "Nothing to editsnipe here."))
        embed = make_embed(ctx, "✏️ Edit Snipe", "", 0x2ecc71)
        embed.add_field(name="Author", value=data["author"].mention)
        embed.add_field(name="Before", value=data["old_content"] or "**[No text]**")
        embed.add_field(name="After", value=data["new_content"] or "**[No text]**")
        embed.set_footer(text=f"Edited at {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        await self.send(ctx, embed)

    @commands.command(aliases=["es"])
    @require("mod")
    async def editsnipe(self, ctx, channel: discord.TextChannel = None):
        await self.editsnipe_logic(ctx, channel)

    @app_commands.command(name="editsnipe")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_editsnipe(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await self.editsnipe_logic(interaction, channel)

    # ═══════════ PURGE (admin+) ═══════════
    async def purge_logic(self, ctx, amount: int = 0, mode: str = "all", user: discord.Member = None):
        if amount <= 0: amount = 100
        if amount > 500: return await self.send(ctx, error(ctx, "Max 500 messages."))

        def check(msg):
            if mode == "user" and user: return msg.author == user
            elif mode == "bots": return msg.author.bot
            elif mode == "embeds": return bool(msg.embeds)
            elif mode == "mentions": return bool(msg.mentions)
            elif mode == "attachments": return bool(msg.attachments)
            elif mode == "text": return not msg.attachments and not msg.embeds and not msg.mentions
            else: return True

        deleted = await ctx.channel.purge(limit=amount, check=check)
        await asyncio.sleep(1)
        await self.send(ctx, make_embed(ctx, "🧹 Purged", f"Deleted {len(deleted)} messages.", 0x2ecc71))

    @commands.command(aliases=["clear", "clean", "prune"])
    @require("admin")
    async def purge(self, ctx, amount_or_mode: str = "all", amount: int = 0, user: discord.Member = None):
        if amount_or_mode.isdigit():
            mode = "all"
            count = int(amount_or_mode)
        else:
            mode = amount_or_mode.lower()
            count = amount if amount > 0 else 100
        await self.purge_logic(ctx, count, mode=mode, user=user)

    @app_commands.command(name="purge")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_purge(self, interaction: discord.Interaction, amount: int = None, mode: str = None, user: discord.Member = None):
        if amount is None: amount = 100
        if mode is None: mode = "all"
        await self.purge_logic(interaction, amount, mode=mode, user=user)

    # ═══════════ SLOWMODE (admin+) ═══════════
    async def slowmode_logic(self, ctx, seconds: int):
        if seconds < 0: return await self.send(ctx, error(ctx, "Seconds cannot be negative."))
        await ctx.channel.edit(slowmode_delay=seconds)
        msg = "disabled" if seconds == 0 else f"set to {seconds}s"
        await self.send(ctx, make_embed(ctx, "🐢 Slowmode", f"Slowmode {msg}.", 0xf1c40f))

    @commands.command(aliases=["sm"])
    @require("admin")
    async def slowmode(self, ctx, seconds: int):
        await self.slowmode_logic(ctx, seconds)

    @app_commands.command(name="slowmode")
    @app_commands.default_permissions(manage_channels=True)
    async def slash_slowmode(self, interaction: discord.Interaction, seconds: int):
        await self.slowmode_logic(interaction, seconds)

    # ═══════════ LOCK / UNLOCK (admin+) ═══════════
    async def lock_logic(self, ctx, channel: discord.TextChannel = None):
        chan = channel or ctx.channel
        await chan.set_permissions(ctx.guild.default_role, send_messages=False)
        await self.send(ctx, make_embed(ctx, "🔒 Locked", f"{chan.mention} is now locked.", 0xe67e22))

    async def unlock_logic(self, ctx, channel: discord.TextChannel = None):
        chan = channel or ctx.channel
        await chan.set_permissions(ctx.guild.default_role, send_messages=True)
        await self.send(ctx, make_embed(ctx, "🔓 Unlocked", f"{chan.mention} unlocked.", 0x2ecc71))

    @commands.command()
    @require("admin")
    async def lock(self, ctx, channel: discord.TextChannel = None):
        await self.lock_logic(ctx, channel)

    @commands.command()
    @require("admin")
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        await self.unlock_logic(ctx, channel)

    @app_commands.command(name="lock")
    @app_commands.default_permissions(manage_channels=True)
    async def slash_lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await self.lock_logic(interaction, channel)

    @app_commands.command(name="unlock")
    @app_commands.default_permissions(manage_channels=True)
    async def slash_unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        await self.unlock_logic(interaction, channel)

    # ═══════════ WARN SYSTEM (mod+) ═══════════
    async def warn_logic(self, ctx, member: discord.Member, reason: str = "No reason"):
        if not self.can_target(ctx.author, member):
            return await self.send(ctx, error(ctx, "You cannot warn this user."))
        data = load("data/warns.json")
        uid = str(member.id)
        if uid not in data: data[uid] = []
        data[uid].append({
            "moderator": ctx.author.id,
            "reason": reason,
            "timestamp": int(time.time())
        })
        save("data/warns.json", data)
        await self.send(ctx, make_embed(ctx, "⚠️ Warned", f"{member.mention} warned.\nReason: {reason}", 0xf39c12))

    @commands.command(aliases=["w"])
    @require("mod")
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await self.warn_logic(ctx, member, reason)

    @app_commands.command(name="warn")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await self.warn_logic(interaction, member, reason)

    async def warnings_logic(self, ctx, member: discord.Member):
        data = load("data/warns.json")
        warns = data.get(str(member.id), [])
        if not warns:
            return await self.send(ctx, make_embed(ctx, "📋 Warnings", f"{member.mention} has none.", 0x2ecc71))
        desc = ""
        for i, w in enumerate(warns, 1):
            mod = self.bot.get_user(w["moderator"])
            mod_name = mod.mention if mod else "Unknown"
            desc += f"**{i}.** By {mod_name} on <t:{w['timestamp']}:f>\n**Reason:** {w['reason']}\n"
        await self.send(ctx, make_embed(ctx, f"📋 {member.display_name} Warnings", desc, 0xf1c40f))

    @commands.command(aliases=["ws"])
    @require("mod")
    async def warnings(self, ctx, member: discord.Member):
        await self.warnings_logic(ctx, member)

    @app_commands.command(name="warnings")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_warnings(self, interaction: discord.Interaction, member: discord.Member):
        await self.warnings_logic(interaction, member)

    async def clearwarns_logic(self, ctx, member: discord.Member):
        data = load("data/warns.json")
        uid = str(member.id)
        if uid in data:
            del data[uid]
            save("data/warns.json", data)
            await self.send(ctx, make_embed(ctx, "🧹 Cleared", f"Warnings for {member.mention} cleared.", 0x2ecc71))
        else:
            await self.send(ctx, make_embed(ctx, "ℹ️ None", "No warnings to clear.", 0x95a5a6))

    @commands.command(aliases=["cw"])
    @require("admin")
    async def clearwarns(self, ctx, member: discord.Member):
        await self.clearwarns_logic(ctx, member)

    @app_commands.command(name="clearwarns")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        await self.clearwarns_logic(interaction, member)

    # ═══════════ NICKNAME (mod+) ═══════════
    async def nick_logic(self, ctx, member: discord.Member, *, nick: str = None):
        if nick and len(nick) > 32: return await self.send(ctx, error(ctx, "Nickname ≤32 characters."))
        await member.edit(nick=nick)
        if nick:
            await self.send(ctx, make_embed(ctx, "🏷️ Nickname Changed", f"{member.mention} → `{nick}`", 0x3498db))
        else:
            await self.send(ctx, make_embed(ctx, "🏷️ Nickname Reset", f"Reset {member.mention}'s nickname.", 0x3498db))

    @commands.command(aliases=["nick"])
    @require("mod")
    async def nickname(self, ctx, member: discord.Member, *, nick: str = None):
        await self.nick_logic(ctx, member, nick=nick)

    @app_commands.command(name="nickname")
    @app_commands.default_permissions(manage_nicknames=True)
    async def slash_nickname(self, interaction: discord.Interaction, member: discord.Member, nick: str = None):
        await self.nick_logic(interaction, member, nick=nick)

    # ═══════════ SAY (admin+) ═══════════
    async def say_logic(self, ctx, channel: discord.TextChannel, *, text: str):
        await channel.send(text)
        await self.send(ctx, make_embed(ctx, "💬 Sent", f"Message sent to {channel.mention}.", 0x2ecc71))

    @commands.command(aliases=["echo"])
    @require("admin")
    async def say(self, ctx, channel: discord.TextChannel, *, text: str):
        await self.say_logic(ctx, channel, text=text)

    @app_commands.command(name="say")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_say(self, interaction: discord.Interaction, channel: discord.TextChannel, text: str):
        await self.say_logic(interaction, channel, text=text)

    # ═══════════ MUTE / UNMUTE (mod+) ═══════════
    async def mute_logic(self, ctx, member: discord.Member, duration: str, reason: str = "No reason"):
        if not self.can_target(ctx.author, member):
            return await self.send(ctx, error(ctx, "Cannot mute this user."))
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="Muted")
        if not role:
            role = await guild.create_role(name="Muted")
            for ch in guild.channels:
                await ch.set_permissions(role, send_messages=False, add_reactions=False)
        await member.add_roles(role)
        seconds = parse_time(duration)
        expiry = int(time.time()) + seconds if seconds > 0 else 0
        mutes = load("data/mutes.json")
        mutes[str(member.id)] = {"end": expiry, "guild": guild.id}
        save("data/mutes.json", mutes)
        await self.send(ctx, make_embed(ctx, "🔇 Muted",
            f"{member.mention} muted\nDuration: {duration}\nReason: {reason}", 0xf39c12))

    @commands.command(aliases=["m"])
    @require("mod")
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason: str = "No reason"):
        await self.mute_logic(ctx, member, duration, reason)

    @app_commands.command(name="mute")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_mute(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason"):
        await self.mute_logic(interaction, member, duration, reason)

    async def unmute_logic(self, ctx, member: discord.Member):
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="Muted")
        if not role: return await self.send(ctx, error(ctx, "Muted role doesn't exist."))
        await member.remove_roles(role)
        mutes = load("data/mutes.json")
        mutes.pop(str(member.id), None)
        save("data/mutes.json", mutes)
        await self.send(ctx, make_embed(ctx, "🔊 Unmuted", f"{member.mention} unmuted.", 0x2ecc71))

    @commands.command(aliases=["um"])
    @require("mod")
    async def unmute(self, ctx, member: discord.Member):
        await self.unmute_logic(ctx, member)

    @app_commands.command(name="unmute")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_unmute(self, interaction: discord.Interaction, member: discord.Member):
        await self.unmute_logic(interaction, member)

    # ═══════════ KICK (admin+) ═══════════
    async def kick_logic(self, ctx, member: discord.Member, reason: str = "No reason"):
        if not self.can_target(ctx.author, member):
            return await self.send(ctx, error(ctx, "Cannot kick this user."))
        await member.kick(reason=reason)
        await self.send(ctx, make_embed(ctx, "👢 Kicked", f"{member.mention} kicked.\nReason: {reason}", 0xe67e22))

    @commands.command(aliases=["k"])
    @require("admin")
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await self.kick_logic(ctx, member, reason)

    @app_commands.command(name="kick")
    @app_commands.default_permissions(kick_members=True)
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await self.kick_logic(interaction, member, reason)

    # ═══════════ BAN (admin+) ═══════════
    async def ban_logic(self, ctx, member: discord.Member, reason: str = "No reason"):
        if not self.can_target(ctx.author, member):
            return await self.send(ctx, error(ctx, "Cannot ban this user."))
        await member.ban(reason=reason)
        await self.send(ctx, make_embed(ctx, "🔨 Banned", f"{member.mention} banned.\nReason: {reason}", 0xc0392b))

    @commands.command(aliases=["b"])
    @require("admin")
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await self.ban_logic(ctx, member, reason)

    @app_commands.command(name="ban")
    @app_commands.default_permissions(ban_members=True)
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await self.ban_logic(interaction, member, reason)

    # ═══════════ JAIL / UNJAIL (admin+) ═══════════
    async def jail_logic(self, ctx, member: discord.Member, reason: str = "No reason"):
        if not self.can_target(ctx.author, member):
            return await self.send(ctx, error(ctx, "Cannot jail this user."))
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name="Jailed")
        if not role: role = await guild.create_role(name="Jailed")
        jail_data = load("data/jail.json")
        uid = str(member.id)
        jail_data[uid] = {
            "roles": [r.id for r in member.roles if r != guild.default_role],
            "channel": None
        }
        await member.edit(roles=[role])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        ch = await guild.create_text_channel(f"jail-{member.name}", overwrites=overwrites)
        jail_data[uid]["channel"] = ch.id
        save("data/jail.json", jail_data)
        await ch.send(f"{member.mention} jailed.\nReason: {reason}")
        await self.send(ctx, make_embed(ctx, "🔒 Jailed", f"{member.mention} jailed.\nCell: {ch.mention}", 0x2c3e50))

    @commands.command(aliases=["j"])
    @require("admin")
    async def jail(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await self.jail_logic(ctx, member, reason)

    @app_commands.command(name="jail")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_jail(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
        await self.jail_logic(interaction, member, reason)

    async def unjail_logic(self, ctx, member: discord.Member):
        guild = ctx.guild
        jail_data = load("data/jail.json")
        uid = str(member.id)
        if uid not in jail_data: return await self.send(ctx, error(ctx, "User not jailed."))
        info = jail_data[uid]
        roles = [guild.get_role(r) for r in info["roles"] if guild.get_role(r)]
        await member.edit(roles=roles)
        ch_id = info.get("channel")
        if ch_id:
            ch = guild.get_channel(ch_id)
            if ch:
                try: await ch.delete()
                except: pass
        del jail_data[uid]
        save("data/jail.json", jail_data)
        await self.send(ctx, make_embed(ctx, "🔓 Unjailed", f"{member.mention} released.", 0x2ecc71))

    @commands.command(aliases=["uj"])
    @require("admin")
    async def unjail(self, ctx, member: discord.Member):
        await self.unjail_logic(ctx, member)

    @app_commands.command(name="unjail")
    @app_commands.default_permissions(moderate_members=True)
    async def slash_unjail(self, interaction: discord.Interaction, member: discord.Member):
        await self.unjail_logic(interaction, member)

    # ═══════════ AUTO UNMUTE LOOP ═══════════
    @tasks.loop(seconds=30)
    async def check_mutes(self):
        mutes = load("data/mutes.json")
        if not mutes: return
        now = int(time.time())
        changed = False
        for uid_str, info in list(mutes.items()):
            if info["end"] <= now:
                guild = self.bot.get_guild(info["guild"])
                if guild:
                    member = guild.get_member(int(uid_str))
                    role = discord.utils.get(guild.roles, name="Muted")
                    if member and role:
                        try: await member.remove_roles(role)
                        except: pass
                del mutes[uid_str]
                changed = True
        if changed: save("data/mutes.json", mutes)

    @check_mutes.before_loop
    async def before_check_mutes(self):
        await self.bot.wait_until_ready()

    # ═══════════ STAFF MANAGEMENT (owner+) ═══════════
    async def add_staff_logic(self, ctx, role_type: str, user: discord.Member):
        staff = get_staff()
        if role_type not in ["owners", "admins", "mods"]:
            return await self.send(ctx, error(ctx, "Invalid role type."))
        uid = str(user.id)
        if uid in staff.get(role_type, []):
            return await self.send(ctx, error(ctx, f"{user.mention} is already a {role_type[:-1]}."))
        if role_type == "owners" and not is_bot_owner(self.bot, ctx.author.id):
            return await self.send(ctx, error(ctx, "Only the bot owner can manage owners."))
        staff.setdefault(role_type, []).append(uid)
        save(STAFF_FILE, staff)
        await self.send(ctx, make_embed(ctx, "✅ Added", f"{user.mention} added as **{role_type[:-1]}**.", 0x2ecc71))

    async def remove_staff_logic(self, ctx, role_type: str, user: discord.Member):
        staff = get_staff()
        if role_type not in ["owners", "admins", "mods"]:
            return await self.send(ctx, error(ctx, "Invalid role type."))
        uid = str(user.id)
        if uid not in staff.get(role_type, []):
            return await self.send(ctx, error(ctx, f"{user.mention} is not a {role_type[:-1]}."))
        if role_type == "owners" and not is_bot_owner(self.bot, ctx.author.id):
            return await self.send(ctx, error(ctx, "Only the bot owner can manage owners."))
        staff[role_type].remove(uid)
        save(STAFF_FILE, staff)
        await self.send(ctx, make_embed(ctx, "✅ Removed", f"{user.mention} removed from **{role_type[:-1]}**.", 0xe67e22))

    @commands.command(aliases=["ao"])
    @require("bot_owner")
    async def addowner(self, ctx, user: discord.Member): await self.add_staff_logic(ctx, "owners", user)
    @commands.command(aliases=["ro"])
    @require("bot_owner")
    async def removeowner(self, ctx, user: discord.Member): await self.remove_staff_logic(ctx, "owners", user)
    @commands.command(aliases=["aa"])
    @require("owner")
    async def addadmin(self, ctx, user: discord.Member): await self.add_staff_logic(ctx, "admins", user)
    @commands.command(aliases=["ra"])
    @require("owner")
    async def removeadmin(self, ctx, user: discord.Member): await self.remove_staff_logic(ctx, "admins", user)
    @commands.command(aliases=["am"])
    @require("admin")
    async def addmod(self, ctx, user: discord.Member): await self.add_staff_logic(ctx, "mods", user)
    @commands.command(aliases=["rm"])
    @require("admin")
    async def removemod(self, ctx, user: discord.Member): await self.remove_staff_logic(ctx, "mods", user)

    # Slash equivalents for staff management
    @app_commands.command(name="addowner")
    @app_commands.default_permissions(administrator=True)
    async def slash_addowner(self, interaction: discord.Interaction, user: discord.Member): await self.add_staff_logic(interaction, "owners", user)
    @app_commands.command(name="removeowner")
    @app_commands.default_permissions(administrator=True)
    async def slash_removeowner(self, interaction: discord.Interaction, user: discord.Member): await self.remove_staff_logic(interaction, "owners", user)
    @app_commands.command(name="addadmin")
    @app_commands.default_permissions(administrator=True)
    async def slash_addadmin(self, interaction: discord.Interaction, user: discord.Member): await self.add_staff_logic(interaction, "admins", user)
    @app_commands.command(name="removeadmin")
    @app_commands.default_permissions(administrator=True)
    async def slash_removeadmin(self, interaction: discord.Interaction, user: discord.Member): await self.remove_staff_logic(interaction, "admins", user)
    @app_commands.command(name="addmod")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_addmod(self, interaction: discord.Interaction, user: discord.Member): await self.add_staff_logic(interaction, "mods", user)
    @app_commands.command(name="removemod")
    @app_commands.default_permissions(manage_messages=True)
    async def slash_removemod(self, interaction: discord.Interaction, user: discord.Member): await self.remove_staff_logic(interaction, "mods", user)


# ═══════════════ SETUP ═══════════════
async def setup(bot):
    if not hasattr(bot, 'owner_id'):
        import json as j
        with open("config.json") as f:
            config = j.load(f)
        bot.owner_id = config.get("owner_id")
    await bot.add_cog(Moderation(bot))
