from email import message
import discord
import json
import peewee

db = peewee.SqliteDatabase('economy.db')

class User(peewee.Model):
    discord_id = peewee.BigIntegerField()
    server_id = peewee.BigIntegerField()
    balance = peewee.BigIntegerField(default=0)

    class Meta:
        primary_key = peewee.CompositeKey('discord_id', 'server_id')
        database = db

class Item(peewee.Model):
    name = peewee.TextField()
    price = peewee.BigIntegerField()
    description = peewee.TextField(null=True)
    message = peewee.TextField(null=True)
    server_id = peewee.BigIntegerField()

    class Meta:
        database = db

with open("config.json") as file:
    config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
activity = discord.Activity(type=discord.ActivityType.playing, name="god")
client = discord.Client(intents=intents, activity=activity)

db.connect()
db.create_tables([User, Item])

@client.event
async def on_ready():
    print(f"hey im {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if not message.content.startswith('$'):
        return

    # check user in db
    user = User.select().where(User.discord_id == message.author.id and User.server_id == message.guild.id).first()
    if user is None:
        user = User(discord_id=message.author.id, server_id=message.guild.id)
        user.save()
    
    if message.content == "$":
        await message.channel.send(f"u have {user.balance} dollars lol")

    elif message.content == "$items":
        for item in Item.select().where(Item.server_id == message.guild.id):
            await message.channel.send(f"{item.name}: {item.price}")
        return

    elif message.content.startswith("$work"):
        user.balance += 1
        user.save()

    elif message.content.startswith("$create_item"):
        name, price, description, use_message = (message.content.split() + [None] * 4)[1:5]
        if name == None or price == None < 2:
            await message.channel.send("$create_item *name* *price*")
            return

        item = Item(name=name, server_id=message.guild.id, price=price, description=description, use_message=use_message)
        item.save()
        await message.channel.send(f"created item {name} with price {price}")
        return
    

client.run(config["TOKEN"])