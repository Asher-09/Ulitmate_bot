import discord
import json
import os
from discord.ext import commands
from difflib import get_close_matches

with open("config.json") as f:
    config = json.load(f)

TOKEN = config["token"]
PREFIX = config["prefix"]
OWNER_ID = config.get("owner_id")
GUILD_ID = config.get("guild_id")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Bot(commands.Bot):
    async def setup_hook(self):
        self.owner_id = OWNER_ID

        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{file[:-3]}")
                    print(f"✅ Loaded {file}")
                except Exception as e:
                    print(f"❌ Failed {file}: {e}")

        try:
            if GUILD_ID:
                guild = discord.Object(id=GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print("--------->> Synced to test guild")
            else:
                synced = await self.tree.sync()
                print(f"---------->> Slash commands synced: {len(synced)}")
        except Exception as e:
            print(f"*********** Slash sync failed: {e}")

bot = Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    application_id=config.get("application_id")
)

def error_embed(ctx, title, desc):
    embed = discord.Embed(
        title=title,
        description=desc,
        color=0xe74c3c,
        timestamp=discord.utils.utcnow()
    )
    if ctx.guild:
        embed.set_author(name=ctx.guild.name,
                         icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    return embed

@bot.event
async def on_ready():
    print(f"{bot.user} is online")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        invoked = ctx.invoked_with.lower()
        all_cmds = [cmd.qualified_name for cmd in bot.commands if not cmd.hidden]
        matches = get_close_matches(invoked, all_cmds, n=1, cutoff=0.6)
        if matches:
            cmd = bot.get_command(matches[0])
            embed = discord.Embed(
                title=f"<:hmm:1501541407045976075> Did you mean `{cmd.qualified_name}`?",
                description=f"**Syntax:** `{PREFIX}{cmd.qualified_name} {cmd.signature}`",
                color=0xe67e22,
                timestamp=discord.utils.utcnow()
            )
            if ctx.guild:
                embed.set_author(name=ctx.guild.name,
                                 icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
            example = cmd.extras.get('example', f"`{PREFIX}{cmd.qualified_name}`")
            embed.add_field(name="Example", value=example, inline=False)
            embed.set_footer(text=f"Use {PREFIX}help for all commands")
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=error_embed(ctx,
                "<:wrong:1501538221530808464> Unknown Command",
                f"`{PREFIX}{invoked}` doesn't exist.\nUse `{PREFIX}help` to see all commands."
            ))

    elif isinstance(error, commands.MissingRequiredArgument):
        cmd = ctx.command.name if ctx.command else ctx.invoked_with
        await ctx.send(embed=error_embed(ctx,
            "<:wrong:1501538221530808464> Missing Arguments",
            f"Usage: `{PREFIX}{cmd} {ctx.command.signature if ctx.command else ''}`"
        ))

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=error_embed(ctx,
            "<:wrong:1501538221530808464> Permission Denied",
            "You don't have permission to use this command."
        ))

    elif isinstance(error, commands.CheckFailure):
        await ctx.send(embed=error_embed(ctx,
            "<:wrong:1501538221530808464> Permissions",
            str(error) or "You don't have permission to use this command."
        ))

    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=error_embed(ctx,
            "<:wrong:1501538221530808464> Invalid Input",
            "Invalid argument type."
        ))

    else:
        await ctx.send(embed=error_embed(ctx,
            "<:wrong:1501538221530808464> Error",
            str(error)
        ))

@bot.command(aliases=["shutdown", "off", "die"])
async def stop(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send(embed=error_embed(ctx,
            "<:wrong:1501538221530808464> Error",
            "Only the bot owner can stop the bot."
        ))
    await ctx.send("Shutting down...")
    await bot.close()

if __name__ == "__main__":
    bot.run(TOKEN)
