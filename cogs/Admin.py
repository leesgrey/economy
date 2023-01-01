from discord.ext import commands
from helper import send_simple_embed, get_create_server, has_admin

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def set_currency(self, ctx, icon):
        try:
            if not has_admin(ctx.channel, ctx.author):
                await send_simple_embed("no admin get roled", ctx.channel)
                return
            server = get_create_server(ctx.guild.id, ctx.guild.name)
            server.currency = icon
            server.save()
            await send_simple_embed(f"Set server currency to {icon}", ctx.channel)
        except Exception as e:
            print(e)

    @commands.command()
    async def sync(self, ctx):
        if ctx.author.id == 233678479458172930:
            try:
                print([command.name for command in ctx.bot.tree.get_commands()])
                await ctx.bot.tree.sync(guild=ctx.guild)
                print("Synced slash commands (may take up to an hour to appear)")
            except Exception as e:
                print(e)
    
async def setup(bot):
	await bot.add_cog(Admin(bot))