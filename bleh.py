from lib2to3.pytree import Base
import discord
import json
import peewee
import decimal

MSG_BASE = decimal.Decimal(1);
BOT_MOD = decimal.Decimal(0.5);
SPAM_BONUS = decimal.Decimal(0.5);
REACTION_BONUS = decimal.Decimal(0.5);

db = peewee.SqliteDatabase('economy.db')

class BaseModel(peewee.Model):
    class Meta:
        database = db

class Server(BaseModel):
    server_id = peewee.BigIntegerField()
    currency = peewee.TextField(default=":star:")

class User(BaseModel):
    discord_id = peewee.BigIntegerField()
    server_id = peewee.ForeignKeyField(Server, Server.server_id)
    balance = peewee.DecimalField(default=0)

class Item(BaseModel):
    name = peewee.TextField()
    price = peewee.DecimalField()
    description = peewee.TextField(null=True)
    message = peewee.TextField(null=True)
    server_id = peewee.BigIntegerField()

class Ownership(BaseModel):
    owner_id = peewee.ForeignKeyField(User, User.discord_id)
    server_id = peewee.ForeignKeyField(User, User.server_id) # can prob be removed
    item_id = peewee.ForeignKeyField(Item)

db.connect()
db.create_tables([User, Item, Ownership, Server])

with open("config.json") as file:
    config = json.load(file)

intents = discord.Intents.default()
intents.message_content = True
activity = discord.Activity(type=discord.ActivityType.playing, name="god")
client = discord.Client(intents=intents, activity=activity)

@client.event
async def on_ready():
    print(f"{client.user} is online :)")

@client.event
async def on_reaction_add(reaction, user):
    if user.id == reaction.message.author.id or user.bot:
        return

    print(f"{user.display_name} reacted to {reaction.message.author.display_name} with {reaction.emoji}")
    server = Server.select().where(Server.server_id == reaction.message.guild.id).first()
    if server is None:
        print(f"Creating new server {reaction.message.guild.name}")
        server = Server(server_id=reaction.message.guild.id)
        server.save()

    reacter = User.select().where((User.discord_id == user.id) & (User.server_id == reaction.message.guild.id)).first()
    if reacter == None:
        print(f"Creating new user {user.display_name} in {reaction.message.guild.name}")
        reacter = User(discord_id=user.id, server_id=reaction.message.guild.id)
    print(f"\t{user.display_name}: {reacter.balance} -> {reacter.balance + REACTION_BONUS}")
    reacter.balance += REACTION_BONUS
    reacter.save()

    reactee = User.select().where((User.discord_id == reaction.message.author.id) & (User.server_id == reaction.message.guild.id)).first()
    if reactee == None:
        print(f"Creating new user {reaction.message.author.display_name} in {reaction.message.guild.name}")
        reactee = User(discord_id=reaction.message.author.id, server_id=reaction.message.guild.id)
    print(f"\t{reaction.message.author.display_name}: {reactee.balance} -> {reactee.balance + REACTION_BONUS}")
    reactee.balance += REACTION_BONUS
    reactee.save()
    return

@client.event
async def on_message(message):
    if message.author.bot:
        return

    server_id = message.guild.id
    user_id = message.author.id
    message_val = MSG_BASE;

    print(f"{message.author.display_name} sent a message in {message.guild.name}")

    server = Server.select().where(Server.server_id == server_id).first()
    if server is None:
        print(f"Creating new server {message.guild.name}")
        server = Server(server_id=server_id)
        server.save()

    user = User.select().where((User.discord_id == user_id) & (User.server_id == server_id)).first()
    if user is None:
        print(f"Creating new user {message.author.display_name} in {message.guild.name}")
        user = User(discord_id=user_id, server_id=server_id)

    
    if message.content.startswith('$'):
        message_val *= BOT_MOD;

    print(f"\t{message.author.display_name}: {user.balance} -> {user.balance + message_val}")
    user.balance += message_val 
    user.save()
    
    if not message.content.startswith("$"):
        return
    
    if message.content == "$":
        await message.channel.send(f"{message.author.display_name} has {server.currency}{user.balance}")
        return

    elif message.content == "$shop" or message.content == "$store":
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
            await message.channel.send("$buy_item *item*")
            return
        
        item = Item.select().where((Item.server_id == server_id) & (Item.name == item)).first()
        print(type(item.price))
        if user.balance < item.price:
            await message.channel.send(f"{item.name} costs {item.price} and u have {server.currency}{user.balance} poor lol")
        else:
            user.balance -= item.price
            user.save()
        ownership = Ownership(owner_id=message.author.id, server_id=server_id, item_id=item.id)
        ownership.save()
        await message.channel.send(f"bought {item.name} for {item.price} dollar")
    
    elif message.content.startswith("$use_item"):
        item_name = (message.content.split() + [None])[1]
        if item_name == None:
            await message.channel.send("$use_item *item*")
            return

        item = Ownership.select().join(Item).where((Ownership.owner_id == user_id) & (Item.name == item_name)).first()
        print(item)
        if item == None:
            await message.channel.send(f"you dont have {item_name} lol")
        else:
            item.delete_instance()
            await message.channel.send(f"used {item_name}")

client.run(config["TOKEN"])