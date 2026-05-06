import discord
from discord.ext import commands

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def server(self, ctx):
        g = ctx.guild
        await ctx.send(f"{g.name} | {g.member_count}")

    @commands.command()
    async def members(self, ctx):
        await ctx.send(ctx.guild.member_count)

    @commands.command()
    async def boosts(self, ctx):
        await ctx.send(ctx.guild.premium_subscription_count)

    @commands.command()
    async def rolesnumber(self, ctx):
        await ctx.send(len(ctx.guild.roles))

    @commands.command()
    async def channels(self, ctx):
        await ctx.send(len(ctx.guild.channels))

    @commands.command()
    async def vcs(self, ctx):
        await ctx.send(len([c for c in ctx.guild.channels if isinstance(c, discord.VoiceChannel)]))

async def setup(bot):
    await bot.add_cog(Server(bot))
