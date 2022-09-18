import discord
import json
import peewee

db = peewee.SqliteDatabase('economy.db')

class BaseModel(peewee.Model):
    class Meta:
        database = db

class User(BaseModel):
    discord_id = peewee.BigIntegerField()
    server_id = peewee.BigIntegerField()
    balance = peewee.BigIntegerField(default=0)

class Item(BaseModel):
    name = peewee.TextField()
    price = peewee.BigIntegerField()
    description = peewee.TextField(null=True)
    message = peewee.TextField(null=True)
    server_id = peewee.BigIntegerField()

class Ownership(BaseModel):
    owner_id = peewee.ForeignKeyField(User, User.discord_id)
    server_id = peewee.ForeignKeyField(User, User.server_id) # can prob be removed
    item_id = peewee.ForeignKeyField(Item)

db.connect()
db.create_tables([User, Item, Ownership])

with open("config.json") as file:
    config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
activity = discord.Activity(type=discord.ActivityType.playing, name="god")
client = discord.Client(intents=intents, activity=activity)

@client.event
async def on_ready():
    print(f"hey im {client.user}")

@client.event
async def on_reaction_add(reaction, user):
    if user.id == reaction.message.author.id or user.bot or reaction.message.author.bot:
        return

    print(f"{user.display_name} reacted to {reaction.message.author.display_name} with {reaction.emoji}")

    reacter = User.select().where((User.discord_id == user.id) & (User.server_id == reaction.message.guild.id)).first()
    reacter.balance += 1
    reacter.save()

    reactee = User.select().where((User.discord_id == reaction.message.author.id) & (User.server_id == reaction.message.guild.id)).first()
    reactee.balance += 1
    reactee.save()
    return

@client.event
async def on_message(message):
    server_id = message.guild.id
    user_id = message.author.id

    user = User.select().where((User.discord_id == user_id) & (User.server_id == server_id)).first()
    if user is None:
        print(f"creating new user {message.author.display_name}")
        user = User(discord_id=user_id, server_id=server_id)
    user.balance += 1
    print(f"incrementing {message.author.display_name}'s balance to {user.balance}")
    user.save()
    
    if not message.content.startswith('$'):
        return
    
    if message.content == "$":
        await message.channel.send(f"{message.author.display_name} has {user.balance} dollars")
        return

    elif message.content == "$shop":
        items_msg = ""
        for item in Item.select().where(Item.server_id == server_id):
            items_msg += f"{item.name}: {item.price}\n"
        await message.channel.send(items_msg)
        return

    elif message.content == "$inventory":
        for ownership in Ownership.select().where((Ownership.server_id == server_id) & (Ownership.owner_id == message.author.id)):
            item = Item.select().where(Item.id == ownership.item_id).first()
            await message.channel.send(f"{item.name}")
        return

    elif message.content.startswith("$create_item"):
        name, price, description, use_message = (message.content.split() + [None] * 4)[1:5]
        if name == None or price == None:
            await message.channel.send("$create_item *name* *price*")
            return

        item = Item(name=name, server_id=server_id, price=price, description=description, use_message=use_message)
        item.save()
        await message.channel.send(f"created item {name} with price {price}")
        return
    
    elif message.content.startswith("$buy_item"):
        item = (message.content.split() + [None])[1]
        if item == None:
            await message.channel.send("$create_item *item*")
            return
        
        item = Item.select().where((Item.server_id == server_id) and (Item.name == item)).first()
        ownership = Ownership(owner_id=message.author.id, server_id=server_id, item_id=item.id)
        ownership.save()
        await message.channel.send(f"bought {item.name} for {item.price} dollar")

client.run(config["TOKEN"])