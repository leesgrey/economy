import discord
from discord.ext import commands
from database import Ownership, Item, Shop, User
from datetime import datetime, timezone
from helper import send_simple_embed, get_shop, get_create_user, get_create_server, change_user_balance, has_admin

class Shops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def inventory(self, ctx):
        embed = discord.Embed(timestamp=datetime.now(timezone.utc))
        embed.set_author(name=f"{ctx.author.display_name}'s inventory", icon_url=ctx.author.avatar)
        inventory = Ownership.select().where((Ownership.server_id == ctx.guild.id) & (Ownership.owner_id == ctx.author.id))
        for ownership in inventory:
            item = Item.select().where(Item.id == ownership.item_id).first()
            embed.add_field(name=item.name, value=item.description, inline=False)
        await ctx.send(embed=embed)
        
    @commands.command(aliases=["store"])
    async def shop(self, ctx, name=None):
        shop_embed = discord.Embed()
        server = get_create_server(ctx.guild.id)
        if name is None:
            shop = Shop.select().where((Shop.owner_id.is_null()) & (Shop.server_id == ctx.guild.id)).first()
            shop_embed.set_author(name=shop.name, icon_url=ctx.guild.icon)
        else:
            shop = Shop.select().where((Shop.name == name) & (Shop.server_id == ctx.guild.id)).first()
            if shop is None:
                await send_simple_embed(f"Could not find shop with name \"{name}\"", ctx.channel)
                return
            owner = ctx.guild.get_member(shop.owner_id)
            shop_embed.set_author(name=shop.name, icon_url=owner.avatar)
        items = Item.select().where((Item.shop_id == shop.id))
        if len(items) == 0:
            shop_embed.description=f"No items in {shop.name} :pensive:"
            await ctx.send(embed=shop_embed)
            return
        for item in items:
            shop_embed.add_field(name=f"{server.currency}{item.price} - {item.name}", value=item.description, inline=False)
        await ctx.send(embed=shop_embed)

    @commands.hybrid_command(aliases=["add_server_item"])
    async def create_server_item(self, ctx: commands.Context, name: str, price: int, description: str = None, use_message: str = None):
        try:
            #if not has_admin(ctx.channel, ctx.author):
            #    await send_simple_embed("Only administrators can create server items - add items to your own store with `$add_item`", ctx.channel)
            shop = get_shop(ctx.guild.id)
            item = Item(name=name, price=price, description=description, message=use_message, shop_id=shop.id)
            item.save()
            await self.display_item(ctx.channel, item, shop.name, "Added new item!")
        except Exception as e:
            print(e)

    @commands.hybrid_command(aliases=["add_item"])
    async def create_item(self, ctx: commands.Context, name: str, price: int, description: str = None, use_message: str = None):
        try:
            shop = get_shop(ctx.guild.id, ctx.author.id)
            if shop is None:
                await send_simple_embed("You don't have a shop open - use `$open_shop` to start a shop!", ctx.channel)
                return
            item = Item(name=name, price=price, description=description, message=use_message, shop_id=shop.id)
            item.save()
            await self.display_item(ctx.channel, item, shop.name, "Added new item!")
        except Exception as e:
            print(e)

    @staticmethod
    async def display_item(channel, item, shop_name, header=None):
        embed = discord.Embed(title=item.name, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Shop", value=shop_name)
        embed.add_field(name="Price", value=item.price)
        embed.add_field(name="Description", value=item.description)
        embed.add_field(name="Use message", value=item.message)
        if header:
            embed.set_author(name=header)
        await channel.send(embed=embed)

    @commands.command(aliases=["buy"])
    async def buy_item(self, ctx, item_name):
        try:
            user = get_create_user(ctx.author.id, ctx.guild.id, ctx.author.display_name, ctx.guild.name)
            server = get_create_server(ctx.guild.id)
            item = Item.select().join(Shop).where((Item.name == item_name) & (Shop.server_id == ctx.guild.id)).first()
            if user.balance < item.price:
                await send_simple_embed(f"Insufficient balance ({user.balance})", ctx.channel, author=ctx.author)
                return
            ownership = Ownership(owner_id=ctx.author.id, server_id=ctx.guild.id, item_id=item.id)
            ownership.save()
            print(f"{ctx.author.display_name} bought {item_name} in {ctx.guild.name} for {item.price}")
            change_user_balance(user, ctx.author.display_name, -1 * item.price, True)
            await send_simple_embed(f"Bought {item_name} for {server.currency}{item.price}", ctx.channel, author=ctx.author)
        except Exception as e:
            print(e)

    @commands.command()
    async def use_item(self, ctx, item_name):
        try:
            ownership = Ownership.select().join(Item).where((Ownership.owner_id == ctx.author.id) & (Item.name == item_name)).first()
            if ownership == None:
                await ctx.send(f"you dont have {item_name} lol")
                return
            item = Item.select().where(Item.id == ownership.item_id).first()
            # ownership.delete_instance()
            if item.message:
                await ctx.send(item.message)
            else:
                await ctx.send(f"used {item_name}")
        except Exception as e:
            print(e)

    @commands.command(aliases=["open_store"])
    async def open_shop(self, ctx, name=None):
        try:
            shop = Shop.select().where(Shop.owner_id == ctx.author.id)
            if shop.exists():     
                await send_simple_embed(f"You already have shop \"{name}\" - users can only have one shop at a time.", ctx.channel)
                return   
            new_shop = Shop(name=name if name is not None else f"{ctx.author.display_name}'s Shop", server_id=ctx.guild.id, owner_id=ctx.author.id)
            new_shop.save()
            await send_simple_embed(f"Created new shop \"{new_shop.name}\"", ctx.channel, author=ctx.author)
        except Exception as e:
            print(e)

    @commands.command(aliases=["rename_store"])
    async def rename_shop(self, ctx, name):
        shop = Shop.select().where(Shop.owner_id == ctx.author.id)
        if not shop.exists():
            await send_simple_embed("You don't have a shop open - use `$open_shop` to start a shop!", ctx.channel)
            return
        shop.name = name
        await send_simple_embed(f"Renamed shop to \"{name}\"", ctx.channel, author=ctx.author)
    
    @commands.command(aliases=["store_directory"])
    async def shop_directory(self, ctx):
        try:
            embed = discord.Embed(title=f"{ctx.guild.name} Shop Directory")
            shops = Shop.select().where(Shop.server_id == ctx.guild.id)
            for shop in shops:
                print(f"name: {shop.name}")
                print(f"owner_id: {shop.owner_id}")
                if shop.owner_id is None:
                    val = f"The {ctx.guild.name} server shop"
                else:
                    owner = ctx.guild.get_member(shop.owner_id)
                    val = f"{owner.display_name}'s shop"
                embed.add_field(name=shop.name, value=val, inline=False)
            embed.set_thumbnail(url=ctx.guild.icon)
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
    
    @commands.command()
    async def give_all(self, ctx, item_name):
        try:
            item = Item.select().join(Shop).where((Item.name == item_name) & (Shop.server_id == ctx.guild.id)).first()
            #scopes = [ctx.author.id]
            #if has_admin(ctx.channel, ctx.author):
            #    scopes.append(None)
            if item is None:
                await send_simple_embed(f"Cannot find item \"{item_name}\"", ctx.channel)
                return
            #if item.owner_id not in scopes:
            #    await send_simple_embed(f"Cannot give item \"{item_name}\"", ctx.channel)
            #    return
            for member in list(filter(lambda member: not member.bot, ctx.guild.members)):
                user = get_create_user(member.id, ctx.guild.id, member.display_name, ctx.guild.name)
                new_ownership = Ownership(owner_id = user.discord_id, server_id=ctx.guild.id, item_id=item.id)
                new_ownership.save()
        except Exception as e:
            print(e)
        

async def setup(bot):
	await bot.add_cog(Shops(bot))