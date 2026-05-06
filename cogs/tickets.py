import discord
from discord.ext import commands
import io

class Close(discord.ui.View):
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red)
    async def close(self, i, b):
        msgs = [m async for m in i.channel.history(limit=200)]
        text = "\n".join([f"{m.author}: {m.content}" for m in msgs])

        try:
            await i.user.send(file=discord.File(io.BytesIO(text.encode()), "ticket.txt"))
        except:
            pass

        await i.channel.delete()

class TicketView(discord.ui.View):
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
    async def create(self, i, b):

        existing = discord.utils.get(i.guild.text_channels, name=f"ticket-{i.user.id}")
        if existing:
            return await i.response.send_message("Already open", ephemeral=True)

        overwrites = {
            i.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            i.user: discord.PermissionOverwrite(read_messages=True),
            i.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        ch = await i.guild.create_text_channel(
            f"ticket-{i.user.id}",
            overwrites=overwrites
        )

        await ch.send("Support will respond", view=Close())
        await i.response.send_message("Created", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ticketpanel(self, ctx):
        await ctx.send("Tickets", view=TicketView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))
