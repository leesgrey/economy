import discord
from discord.ext import commands
from datetime import datetime, timezone
from helper import get_create_server, get_create_user, change_user_balance


class Income(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        print(f"{message.author.display_name} sent a message in {message.guild.name}#{message.channel.name}")

        server = get_create_server(message.guild.id, message.guild.name)
        user = get_create_user(message.author.id, message.guild.id, message.author.display_name, message.guild.name)

        if message.content.startswith("$"):
            change_user_balance(user, message.author.display_name, 1, True)
            if message.content == "$":
                embed = discord.Embed(description=f"{server.currency}{user.balance}", timestamp=datetime.now(timezone.utc))
                embed.set_author(name=f"{message.author.display_name}'s balance", icon_url=message.author.avatar)
                await message.channel.send(embed=embed)
        else:
            change_user_balance(user, message.author.display_name, 2, True)


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, reacter):
        reactee = reaction.message.author
        server = reaction.message.guild
        if reacter.id == reactee.id or reacter.bot:
            return

        print(f"{reacter.display_name} reacted to {reactee.display_name} with {reaction.emoji}")

        get_create_server(reaction.message.guild.id, reaction.message.guild.name)
        reacter_db = get_create_user(reacter.id, server.id, reacter.display_name, server.name)
        change_user_balance(reacter_db, reacter.display_name, 1, True)

        if not reactee.bot:
            reactee_db = get_create_user(reactee.id, server.id, reactee.display_name, server.name)
            change_user_balance(reactee_db, reactee.display_name, 1, True)


async def setup(bot):
	await bot.add_cog(Income(bot))