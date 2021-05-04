import discord
from discord.ext import commands

import lib.checks
import lib.database as db


class AdminCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator = True)
    @commands.command()
    async def init(self, ctx):
        if await lib.checks.guild_exists(ctx.guild.id):
            await ctx.message.channel.send('This server has already been initialized.')
            return
        
        await ctx.message.channel.send('Initializing **5eCollector** for this server...')
        db.Guild.create(ctx.guild.id)
        await ctx.message.channel.send('Initalized.')


    @commands.has_permissions(administrator = True)
    @commands.command()
    async def uninit(self, ctx):
        if not await lib.checks.guild_exists(ctx.guild.id):
            await ctx.message.channel.send('This server has not been initialized yet.')
            return
        
        await ctx.message.channel.send('Removing **5eCollector** from this server...')
        db.Guild.remove(ctx.guild.id)
        await ctx.message.channel.send('Removed.')


class CheatCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator = True)
    @commands.check(lib.checks.guild_exists_check)
    async def add_monster(self, ctx, user_name, monster_name, amount=1):
        user = lib.getters.get_user(user_name, ctx.guild.members)
        
        if user is None or not await lib.checks.user_exists(user.id, ctx.guild.id):
            await ctx.message.channel.send(f'User {user_name} not found')
            return

        monster = lib.resources.get_monster(monster_name)
        if monster is None:
            await ctx.message.channel.send(f'Monster {monster_name} not found')
            return

        owner_id = db.User.get_by_member(user.id, user.id).id
        for i in range(amount):
            db.Monster.create(monster['name'], 1, ctx.guild.id, owner_id)
        await ctx.message.channel.send(f'{user.mention} has been given {monster_name} (x{amount})')

    @commands.command()
    @commands.has_permissions(administrator = True)
    @commands.check(lib.checks.guild_exists_check)
    async def add_points(self, ctx, user_name, amount: int):
        user = lib.getters.get_user(user_name, ctx.guild.members)
        
        if user is None or not await lib.checks.user_exists(user.id, ctx.guild.id):
            await ctx.message.channel.send(f'User {user_name} not found')
            return

        user_db = db.User.get_by_member(user.id, ctx.message.author.id)

        db.User.set_score(user_db.user_id, ctx.guild.id, user_db.score + amount)
        
        await ctx.message.channel.send(f'{user.mention} score has been set from ``{user_db.score}`` to ``{user_db.score + amount}``')


def setup(bot):
    bot.add_cog(AdminCog(bot))
    bot.add_cog(CheatCog(bot))