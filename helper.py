import discord
from datetime import datetime, timezone
from database import Server, User, Shop

async def send_simple_embed(text, channel, timestamp=True, author=None):
    embed = discord.Embed(description=text)
    if timestamp is True:
        embed.timestamp = datetime.now(timezone.utc)
    if author is not None:
        embed.set_author(name=author.display_name, icon_url=author.avatar)
    await channel.send(embed=embed)

def get_create_server(server_id, name=None):
    server = Server.select().where(Server.server_id == server_id).first()
    if server is None:
        print(f"Creating new server {name}")
        server = Server(server_id=server_id)
        server.save()
        server_shop = Shop(name=f"{name} Shop", server_id=server_id)
        server_shop.save()
    return server

def get_create_user(user_id, server_id, user_name, server_name):
    user = User.select().where((User.discord_id == user_id) & (User.server_id == server_id)).first()
    if user is None:
        print(f"Creating new user {user_name} in {server_name}")
        user = User(discord_id=user_id, server_id=server_id)
    return user

def get_shop(server_id, user_id=None):
    if user_id is None:
        return Shop.select().where((Shop.owner_id.is_null()) & (Shop.server_id == server_id)).first()
    else:
        return Shop.select().where((Shop.owner_id == user_id) & (Shop.server_id == server_id)).first()

def change_user_balance(user_db, name, change, save=False):
    print(f"\t{name}: {user_db.balance} -> {user_db.balance + change}")
    user_db.balance += change
    if save:
        user_db.save()

def has_admin(channel, user):
    if channel.permissions_for(user).administrator is True:
        return True
    return False
