import discord
import json
import peewee

db = peewee.SqliteDatabase('economy.db')

class User(peewee.Model):
    discord_id = peewee.BigIntegerField()
    balance = peewee.BigIntegerField(default=0)

    class Meta:
        database = db

with open("config.json") as file:
    config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

db.connect()
db.create_tables([User])

@client.event
async def on_ready():
    print(f"hey im {client.user}")
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.playing, name="god")
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith("$"):
        return
    
    # check user in db
    user = User.select().where(User.discord_id == message.author.id).first()
    if user is None:
        user = User(discord_id=message.author.id)
        user.save()

    if message.content.startswith("$work"):
        user.balance += 1
        user.save()
    
    await message.channel.send(f"u have {user.balance} dollars lol")

client.run(config["TOKEN"])