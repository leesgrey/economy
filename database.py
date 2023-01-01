import peewee
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
    balance = peewee.BigIntegerField(default=0)

class Shop(BaseModel):
    name = peewee.TextField()
    server_id = peewee.ForeignKeyField(Server, Server.server_id)
    owner_id = peewee.ForeignKeyField(User, User.discord_id, null=True)

class Item(BaseModel):
    name = peewee.TextField()
    price = peewee.BigIntegerField()
    description = peewee.TextField(null=True)
    message = peewee.TextField(null=True)
    shop_id = peewee.ForeignKeyField(Shop, Shop.id)

class Ownership(BaseModel):
    owner_id = peewee.ForeignKeyField(User, User.discord_id)
    server_id = peewee.ForeignKeyField(User, User.server_id)
    item_id = peewee.ForeignKeyField(Item)

def setup_database():
    db.connect()
    db.create_tables([User, Item, Ownership, Server, Shop])