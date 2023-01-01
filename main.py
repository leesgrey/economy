import discord
from discord.ext import commands
import json
from database import setup_database
import asyncio

with open("config.json") as file:
    config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)

setup_database()

@bot.event
async def on_ready():
    print(f"{bot.user} is online :)")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="god")
    )

async def load_extensions():
    for cog_file in ["Income", "Admin", "Shops"]:
        try:
            await bot.load_extension(f"cogs.{cog_file}")
            print(f"Loaded extension {cog_file}")
        except (commands.ExtensionNotFound, commands.ExtensionAlreadyLoaded, commands.NoEntryPointError, commands.ExtensionFailed) as e:
            print(f"Could not load extension {cog_file} - {e}")

async def main():
    await load_extensions()
    async with bot:
        await bot.start(config["TOKEN"])

asyncio.run(main(), debug=True)
