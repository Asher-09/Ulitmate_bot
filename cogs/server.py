import discord
from discord.ext import commands
from discord import app_commands

EMOJI_SUCCESS = "<a:tick:1501584376540954665>"
EMOJI_WRONG   = "<:wrong:1501538221530808464>"
EMOJI_FILE    = "<:file:1501584520107786391>"
EMOJI_UP      = "<:up:1501587355419545600>"
EMOJI_LOCK    = "<:lock:1501586295099494532>"

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
        text=f"Requested by {user}",
        icon_url=user.display_avatar.url
    )
    return embed

def error_embed(ctx, msg):
    return make_embed(ctx, f"{EMOJI_WRONG} Error", msg, 0xe74c3c)

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, ctx, emb):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.send_message(embed=emb)
        else:
            await ctx.send(embed=emb)

    async def serverinfo_logic(self, ctx):
        guild = ctx.guild
        embed = make_embed(ctx, f"{EMOJI_LOCK} Server Information", "", 0x3498db)

        owner = guild.owner.mention if guild.owner else "Unknown"
        total_members = guild.member_count
        humans = sum(1 for m in guild.members if not m.bot)
        bots = total_members - humans
        boost_tier = guild.premium_tier
        boost_count = guild.premium_subscription_count
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles_count = len(guild.roles)
        created = discord.utils.format_dt(guild.created_at, style="F")

        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Members", value=f"Total: {total_members}\nHumans: {humans}\nBots: {bots}", inline=True)
        embed.add_field(name="Boost", value=f"Level {boost_tier} ({boost_count} boosts)", inline=True)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}", inline=True)
        embed.add_field(name="Roles", value=str(roles_count), inline=True)
        embed.add_field(name="Created", value=created, inline=False)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await self.send(ctx, embed)

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx):
        await self.serverinfo_logic(ctx)

    @app_commands.command(name="serverinfo", description="Show detailed server information")
    async def slash_serverinfo(self, interaction: discord.Interaction):
        await self.serverinfo_logic(interaction)

    async def userinfo_logic(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        embed = make_embed(ctx, f"{EMOJI_FILE} User Information", "", member.color if member.color.value else 0x95a5a6)
        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="Username", value=f"{member.mention} ({member})", inline=False)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Account created", value=discord.utils.format_dt(member.created_at, style="F"), inline=True)
        embed.add_field(name="Joined server", value=discord.utils.format_dt(member.joined_at, style="F"), inline=True)

        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_list = ", ".join(roles) if roles else "None"
        embed.add_field(name="Roles", value=roles_list, inline=False)

        await self.send(ctx, embed)

    @commands.command(aliases=["ui"])
    async def userinfo(self, ctx, member: discord.Member = None):
        await self.userinfo_logic(ctx, member)

    @app_commands.command(name="userinfo", description="Show detailed user information")
    async def slash_userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        await self.userinfo_logic(interaction, member)

    async def avatar_logic(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        embed = make_embed(ctx, f"{EMOJI_FILE} Avatar", f"{member.mention}'s avatar", member.color if member.color.value else 0x3498db)
        embed.set_image(url=member.display_avatar.url)
        await self.send(ctx, embed)

    @commands.command(aliases=["av"])
    async def avatar(self, ctx, member: discord.Member = None):
        await self.avatar_logic(ctx, member)

    @app_commands.command(name="avatar", description="Display a user's avatar")
    async def slash_avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        await self.avatar_logic(interaction, member)

    async def banner_logic(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        user = await self.bot.fetch_user(member.id)
        if user.banner is None:
            return await self.send(ctx, error_embed(ctx, f"{member.display_name} has no banner set."))
        embed = make_embed(ctx, f"{EMOJI_FILE} Banner", f"{member.mention}'s banner", 0x9b59b6)
        embed.set_image(url=user.banner.url)
        await self.send(ctx, embed)

    @commands.command()
    async def banner(self, ctx, member: discord.Member = None):
        await self.banner_logic(ctx, member)

    @app_commands.command(name="banner", description="Display a user's profile banner")
    async def slash_banner(self, interaction: discord.Interaction, member: discord.Member = None):
        await self.banner_logic(interaction, member)

    async def servericon_logic(self, ctx):
        if not ctx.guild.icon:
            return await self.send(ctx, error_embed(ctx, "This server has no icon."))
        embed = make_embed(ctx, f"{EMOJI_FILE} Server Icon", "", 0x3498db)
        embed.set_image(url=ctx.guild.icon.url)
        await self.send(ctx, embed)

    @commands.command()
    async def servericon(self, ctx):
        await self.servericon_logic(ctx)

    @app_commands.command(name="servericon", description="Show the server's icon")
    async def slash_servericon(self, interaction: discord.Interaction):
        await self.servericon_logic(interaction)

    async def members_logic(self, ctx):
        total = ctx.guild.member_count
        humans = sum(1 for m in ctx.guild.members if not m.bot)
        bots = total - humans
        embed = make_embed(ctx, f"{EMOJI_SUCCESS} Members", f"Total: {total}\nHumans: {humans}\nBots: {bots}", 0x2ecc71)
        await self.send(ctx, embed)

    @commands.command()
    async def members(self, ctx):
        await self.members_logic(ctx)

    @app_commands.command(name="members", description="Show member counts")
    async def slash_members(self, interaction: discord.Interaction):
        await self.members_logic(interaction)

    async def boosts_logic(self, ctx):
        level = ctx.guild.premium_tier
        count = ctx.guild.premium_subscription_count
        embed = make_embed(ctx, f"{EMOJI_UP} Server Boosts", f"Level {level} ({count} boosts)", 0xf1c40f)
        await self.send(ctx, embed)

    @commands.command()
    async def boosts(self, ctx):
        await self.boosts_logic(ctx)

    @app_commands.command(name="boosts", description="Show boost level and count")
    async def slash_boosts(self, interaction: discord.Interaction):
        await self.boosts_logic(interaction)

    async def rolesnumber_logic(self, ctx):
        count = len(ctx.guild.roles)
        embed = make_embed(ctx, f"{EMOJI_SUCCESS} Roles", f"This server has **{count}** roles.", 0x3498db)
        await self.send(ctx, embed)

    @commands.command()
    async def rolesnumber(self, ctx):
        await self.rolesnumber_logic(ctx)

    @app_commands.command(name="rolesnumber", description="Show total number of roles")
    async def slash_rolesnumber(self, interaction: discord.Interaction):
        await self.rolesnumber_logic(interaction)

    async def channels_logic(self, ctx):
        text = len(ctx.guild.text_channels)
        voice = len(ctx.guild.voice_channels)
        embed = make_embed(ctx, f"{EMOJI_LOCK} Channels", f"Text: {text}\nVoice: {voice}", 0x2c3e50)
        await self.send(ctx, embed)

    @commands.command()
    async def channels(self, ctx):
        await self.channels_logic(ctx)

    @app_commands.command(name="channels", description="Show number of text and voice channels")
    async def slash_channels(self, interaction: discord.Interaction):
        await self.channels_logic(interaction)

    async def vcs_logic(self, ctx):
        count = len(ctx.guild.voice_channels)
        embed = make_embed(ctx, f"{EMOJI_UP} Voice Channels", str(count), 0x3498db)
        await self.send(ctx, embed)

    @commands.command()
    async def vcs(self, ctx):
        await self.vcs_logic(ctx)

    @app_commands.command(name="vcs", description="Show number of voice channels")
    async def slash_vcs(self, interaction: discord.Interaction):
        await self.vcs_logic(interaction)


async def setup(bot):
    await bot.add_cog(Server(bot))
