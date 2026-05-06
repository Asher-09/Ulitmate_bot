
import discord
from discord.ext import commands
from discord import app_commands
import json
import os

STAFF_FILE = "data/staff.json"

EMOJI_SUCCESS = "<a:tick:1501584376540954665>"
EMOJI_WRONG   = "<:wrong:1501538221530808464>"
EMOJI_DELETE  = "<:icon_delete:1501586303769378876>"
EMOJI_COLOR   = "<:color:1501586914795585697>"
EMOJI_UP      = "<:up:1501587355419545600>"

def load(p):
    try:
        with open(p) as f:
            return json.load(f)
    except:
        return {}

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
    return make_embed(ctx, f"{EMOJI_WRONG} Error", msg, 0xe74c3c)

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, ctx, emb):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=emb)
        else:
            await ctx.send(embed=emb)

    async def createrole_logic(self, ctx, name: str):
        await ctx.guild.create_role(name=name)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_SUCCESS} Role Created", f"Role **{name}** has been created.", 0x2ecc71))

    @commands.command(aliases=["cr", "rcreate"])
    @require("admin")
    async def createrole(self, ctx, *, name: str):
        await self.createrole_logic(ctx, name)

    @app_commands.command(name="createrole", description="Create a new role")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_createrole(self, interaction: discord.Interaction, name: str):
        await self.createrole_logic(interaction, name)

    async def deleterole_logic(self, ctx, role: discord.Role):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot manage a role higher than or equal to mine."))
        await role.delete()
        await self.send(ctx, make_embed(ctx, f"{EMOJI_DELETE} Role Deleted", f"Role **{role.name}** has been deleted.", 0xe67e22))

    @commands.command(aliases=["dr", "rdelete"])
    @require("admin")
    async def deleterole(self, ctx, role: discord.Role):
        await self.deleterole_logic(ctx, role)

    @app_commands.command(name="deleterole", description="Delete a role")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_deleterole(self, interaction: discord.Interaction, role: discord.Role):
        await self.deleterole_logic(interaction, role)

    async def giverole_logic(self, ctx, member: discord.Member, role: discord.Role):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot give a role higher than mine."))
        await member.add_roles(role)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_SUCCESS} Role Given", f"**{role.name}** given to {member.mention}.", 0x2ecc71))

    @commands.command(aliases=["gr", "give"])
    @require("admin")
    async def giverole(self, ctx, member: discord.Member, role: discord.Role):
        await self.giverole_logic(ctx, member, role)

    @app_commands.command(name="giverole", description="Give a role to a member")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_giverole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await self.giverole_logic(interaction, member, role)

    # ── Remove Role ──────────────────────────────────
    async def removerole_logic(self, ctx, member: discord.Member, role: discord.Role):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot remove a role higher than mine."))
        await member.remove_roles(role)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_DELETE} Role Removed", f"**{role.name}** removed from {member.mention}.", 0xe67e22))

    @commands.command(aliases=["rr", "take"])
    @require("admin")
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
        await self.removerole_logic(ctx, member, role)

    @app_commands.command(name="removerole", description="Remove a role from a member")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await self.removerole_logic(interaction, member, role)

    # ── Rename Role ──────────────────────────────────
    async def renamerole_logic(self, ctx, role: discord.Role, new_name: str):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot rename a role higher than mine."))
        old = role.name
        await role.edit(name=new_name)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_SUCCESS} Role Renamed", f"**{old}** → **{new_name}**", 0x3498db))

    @commands.command(aliases=["rn", "rrename"])
    @require("admin")
    async def renamerole(self, ctx, role: discord.Role, *, new_name: str):
        await self.renamerole_logic(ctx, role, new_name)

    @app_commands.command(name="renamerole", description="Rename a role")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_renamerole(self, interaction: discord.Interaction, role: discord.Role, new_name: str):
        await self.renamerole_logic(interaction, role, new_name)

    # ── Change Role Color ────────────────────────────
    async def rolecolor_logic(self, ctx, role: discord.Role, color: str):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot edit a role higher than mine."))
        try:
            col = int(color.strip("#"), 16)
            col = discord.Color(col)
        except:
            return await self.send(ctx, error(ctx, "Invalid color. Use hex like `#ff0000` or `ff0000`."))
        await role.edit(color=col)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_COLOR} Role Color Updated", f"Color of **{role.name}** changed to {color}.", 0x9b59b6))

    @commands.command(aliases=["rc", "rcolor"])
    @require("admin")
    async def colorrole(self, ctx, role: discord.Role, *, color: str):
        await self.rolecolor_logic(ctx, role, color)

    @app_commands.command(name="rolecolor", description="Set a role's color (hex)")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_rolecolor(self, interaction: discord.Interaction, role: discord.Role, color: str):
        await self.rolecolor_logic(interaction, role, color)

    async def roleposition_logic(self, ctx, role: discord.Role, position: int):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot move a role higher than mine."))
        if role.is_default():
            return await self.send(ctx, error(ctx, "Cannot move the @everyone role."))

        roles_sorted = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
        total = len(roles_sorted)
        if position < 1 or position > total:
            return await self.send(ctx, error(ctx, f"Position must be between 1 and {total}."))

        if position == 1:
            max_pos = max(r.position for r in ctx.guild.roles)
            new_pos = max_pos + 1
        else:
            above_role = roles_sorted[position - 2]
            new_pos = above_role.position - 1

        try:
            await role.edit(position=new_pos)
        except discord.Forbidden:
            return await self.send(ctx, error(ctx, "I lack permission to reorder roles."))
        except Exception as e:
            return await self.send(ctx, error(ctx, f"Failed: {e}"))

        await self.send(ctx, make_embed(ctx, f"{EMOJI_UP} Role Moved", f"Moved **{role.name}** to position #{position}.", 0x2ecc71))

    @commands.command(aliases=["rp", "move"])
    @require("admin")
    async def roleposition(self, ctx, role: discord.Role, position: int):
        await self.roleposition_logic(ctx, role, position)

    @app_commands.command(name="roleposition", description="Move a role to position (1=top)")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_roleposition(self, interaction: discord.Interaction, role: discord.Role, position: int):
        await self.roleposition_logic(interaction, role, position)

    async def rolehoist_logic(self, ctx, role: discord.Role, state: bool = None):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot edit a role higher than mine."))
        if state is None:
            state = not role.hoist
        await role.edit(hoist=state)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_UP} Hoist Toggled", f"**{role.name}** hoist set to **{state}**.", 0x2ecc71))

    @commands.command(aliases=["rh", "hoist"])
    @require("admin")
    async def rolehoist(self, ctx, role: discord.Role, state: bool = None):
        await self.rolehoist_logic(ctx, role, state)

    @app_commands.command(name="rolehoist", description="Toggle hoist (separate listing)")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_rolehoist(self, interaction: discord.Interaction, role: discord.Role, state: bool = None):
        await self.rolehoist_logic(interaction, role, state)

    async def rolementionable_logic(self, ctx, role: discord.Role, state: bool = None):
        if role >= ctx.guild.me.top_role:
            return await self.send(ctx, error(ctx, "I cannot edit a role higher than mine."))
        if state is None:
            state = not role.mentionable
        await role.edit(mentionable=state)
        await self.send(ctx, make_embed(ctx, f"{EMOJI_SUCCESS} Mentionable Toggled", f"**{role.name}** mentionable set to **{state}**.", 0x2ecc71))

    @commands.command(aliases=["rmen", "mentionable"])
    @require("admin")
    async def rolementionable(self, ctx, role: discord.Role, state: bool = None):
        await self.rolementionable_logic(ctx, role, state)

    @app_commands.command(name="rolementionable", description="Toggle if role can be @mentioned")
    @app_commands.default_permissions(manage_roles=True)
    async def slash_rolementionable(self, interaction: discord.Interaction, role: discord.Role, state: bool = None):
        await self.rolementionable_logic(interaction, role, state)

    async def roleinfo_logic(self, ctx, role: discord.Role):
        roles = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
        pos = roles.index(role) + 1
        embed = make_embed(ctx, f"Role Info: {role.name}", "", role.color if role.color.value != 0 else 0x95a5a6)
        embed.add_field(name="ID", value=str(role.id), inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Position", value=f"#{pos} (top is 1)", inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        await self.send(ctx, embed)

    @commands.command(aliases=["ri"])
    async def roleinfo(self, ctx, role: discord.Role):
        await self.roleinfo_logic(ctx, role)

    @app_commands.command(name="roleinfo", description="Show detailed info about a role")
    async def slash_roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        await self.roleinfo_logic(interaction, role)

    async def rolelist_logic(self, ctx):
        roles = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
        if not roles:
            return await self.send(ctx, make_embed(ctx, "Role List", "No roles.", 0x95a5a6))
        lines = []
        for idx, r in enumerate(roles):
            if r.is_default():
                line = f"**{idx+1}.** @everyone"
            else:
                line = f"**{idx+1}.** {r.mention} ({len(r.members)})"
            lines.append(line)
        full = "\n".join(lines)
        if len(full) <= 1024:
            embed = make_embed(ctx, "Role Positions", full, 0x3498db)
            embed.set_footer(text="Position 1 = highest role")
            await self.send(ctx, embed)
        else:
            embed = make_embed(ctx, "Role Positions", "List split due to size:", 0x3498db)
            chunks = [lines[i:i+20] for i in range(0, len(lines), 20)]
            for i, chunk in enumerate(chunks):
                embed.add_field(name=f"Page {i+1}", value="\n".join(chunk), inline=False)
            embed.set_footer(text="Position 1 = highest role")
            await self.send(ctx, embed)

    @commands.command(aliases=["roles", "listroles"])
    async def rolelist(self, ctx):
        await self.rolelist_logic(ctx)

    @app_commands.command(name="rolelist", description="List all roles with positions")
    async def slash_rolelist(self, interaction: discord.Interaction):
        await self.rolelist_logic(interaction)


async def setup(bot):
    if not hasattr(bot, 'owner_id'):
        import json as j
        with open("config.json") as f:
            config = j.load(f)
        bot.owner_id = config.get("owner_id")
    await bot.add_cog(Roles(bot))
