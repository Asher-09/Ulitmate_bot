import discord
from discord.ext import commands
import json

with open("./config.json") as f:
    config = json.load(f)

PREFIX = config["prefix"]

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _base_embed(self, title: str, color: discord.Color = discord.Color.gold()) -> discord.Embed:
        embed = discord.Embed(title=title, color=color)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return embed

    def home_embed(self, ctx: commands.Context) -> discord.Embed:
        """Main help page."""
        guild = ctx.guild
        owner = guild.owner.mention if guild.owner else "Unknown"
        member_count = guild.member_count

        embed = self._base_embed("🏠 Help Center")
        embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)

        embed.description = (
            f"**Server Owner : ** {owner}\n"
            f"**Total Members : ** {member_count}\n"
            f"**Prefix :** {PREFIX}"
        )

        cog_names = [name for name, cog in self.bot.cogs.items() if cog.get_commands()]
        if cog_names:
            category_list = "\n".join(f"🔹 **{name}**" for name in cog_names)

            if len(category_list) <= 1024:
                embed.add_field(name="📁 Categories", value=category_list, inline=False)
            else:
                parts = []
                current = ""
                for name in cog_names:
                    line = f"🔹 **{name}**\n"
                    if len(current) + len(line) > 1024:
                        parts.append(current.strip())
                        current = line
                    else:
                        current += line
                if current:
                    parts.append(current.strip())

                for i, part in enumerate(parts):
                    field_name = "📁 Categories" if i == 0 else "📁 Categories (cont.)"
                    embed.add_field(name=field_name, value=part, inline=False)
        else:
            embed.add_field(name="📁 Categories", value="No commands found.", inline=False)

        embed.set_footer(text="Use the dropdown to navigate")
        return embed

    def cog_embed(self, cog_name: str) -> discord.Embed:
        cog = self.bot.get_cog(cog_name)
        if not cog:
            return None

        embed = self._base_embed(f"📁 {cog_name} Commands", discord.Color.blue())
        embed.set_author(name="Command Details", icon_url=self.bot.user.display_avatar.url)

        command_lines = []
        for cmd in cog.get_commands():
            if cmd.hidden:
                continue
            syntax = f"**`{PREFIX}{cmd.qualified_name} {cmd.signature}`**"
            example = cmd.extras.get('example', f"`{PREFIX}{cmd.qualified_name}`")
            command_lines.append(f"{syntax}\n↳ Example: {example}")

        if not command_lines:
            embed.description = "No public commands in this category."
            return embed

        full = "\n".join(command_lines)
        if len(full) <= 1024:
            embed.add_field(name="Commands", value=full, inline=False)
        else:
            parts = []
            current = ""
            for line in command_lines:
                if len(current) + len(line) + 1 > 1024:
                    parts.append(current.strip())
                    current = line
                else:
                    if current:
                        current += "\n"
                    current += line
            if current:
                parts.append(current.strip())

            for i, part in enumerate(parts):
                field_name = "Commands" if i == 0 else "Commands (cont.)"
                embed.add_field(name=field_name, value=part, inline=False)

        embed.set_footer(text="Use the dropdown to go back")
        return embed

    # ═══════════════ dropdown ═══════════════
    class HelpDropdown(discord.ui.Select):
        def __init__(self, bot, parent_view):
            self.bot = bot
            self.parent_view = parent_view

            options = [discord.SelectOption(label="🏠 Home", value="Home", description="Main help page")]
            for name, cog in bot.cogs.items():
                if cog.get_commands():
                    options.append(discord.SelectOption(label=name, value=name, description=f"Browse {name} commands"))
            super().__init__(placeholder="Navigate categories...", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            value = self.values[0]
            if value == "Home":
                embed = self.parent_view.cog.home_embed(interaction)
            else:
                embed = self.parent_view.cog.cog_embed(value)
            await interaction.response.edit_message(embed=embed, view=self.parent_view)

    class HelpView(discord.ui.View):
        def __init__(self, bot, cog):
            super().__init__(timeout=180)
            self.cog = cog
            self.add_item(cog.HelpDropdown(bot, self))

    # ═══════════════ help command ═══════════════
    @commands.command(name="help")
    async def help_command(self, ctx, *, query: str = None):
        """Browse all commands or get details for a specific one."""
        if query:
            cmd = self.bot.get_command(query.lower())
            if cmd and not cmd.hidden:
                embed = discord.Embed(
                    title=f"❓ {cmd.qualified_name}",
                    description=f"**Syntax:** `{PREFIX}{cmd.qualified_name} {cmd.signature}`",
                    color=discord.Color.green()
                )
                example = cmd.extras.get('example', f"`{PREFIX}{cmd.qualified_name}`")
                embed.add_field(name="Example", value=example, inline=False)
                await ctx.send(embed=embed)
                return
            else:
                await ctx.send(f" <:wrong:1501538221530808464> Command not found. Use `{PREFIX}help` to browse all commands.")
                return

        # General help
        embed = self.home_embed(ctx)
        view = self.HelpView(self.bot, self)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Help(bot))
