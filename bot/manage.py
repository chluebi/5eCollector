import discord
from discord.ext import commands
import asyncio
import time

import lib.checks
import lib.database as db
import lib.embeds
import lib.util


class UserCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def me(self, ctx, action='view', *options):
        user = ctx.message.author

        if action in ['monsters', 'monster']:
            await lib.embeds.user_monsters(ctx, user, options)
            return
        elif action in ['groups', 'group']:
            await lib.embeds.user_groups(ctx, user, options)
            return

        await lib.embeds.user_info(user, ctx)

    @commands.command(aliases=['user'])
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def userinfo(self, ctx, user: discord.ext.commands.MemberConverter, action='view', *options):
        
        if action in ['monsters', 'monster']:
            await lib.embeds.user_monsters(ctx, user, options)
            return
        elif action in ['groups', 'group']:
            await lib.embeds.user_groups(ctx, user, options)
            return

        await lib.embeds.user_info(user, ctx)

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def resetme(self, ctx):
        db.User.remove(ctx.message.author.id, ctx.guild.id)
        await ctx.message.channel.send('All your data on this server has been deleted')

    @commands.group(name='monsters')
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def monsters_main_command(self, ctx):
        pass
    
class MonsterCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['monster'])
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def view(self, ctx, monster):
        try:
            monster_id = int(monster)

            monster_db = db.Monster.get(monster_id)
            if monster_db is None:
                await ctx.message.channel.send(f'Monster with id {monster_id} not found')
                return
            if monster_db.guild_id != ctx.guild.id:
                await ctx.message.channel.send(f'Monster with id {monster_id} not found on this guild')
                return
            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = row
            monster = lib.resources.get_monster(monster_db.type)

            user_db = db.User.get(monster_db.owner_id)
            owner = lib.getters.get_user_by_id(user_db.user_id, ctx.guild.members)

            chosen_db = db.Chosen.get_by_monster(monster_db.id)
            chosen = chosen_db is not None
            hp = chosen_db.hp if chosen else 0

            embed = lib.embeds.generate_caught_monster_embed(monster_db.name, monster, owner, monster_db.level, monster_db.exhausted_timestamp, chosen=chosen, hp=hp)
        except ValueError:
            monster= lib.resources.get_monster(monster)
            embed = lib.embeds.generate_monster_embed(monster)

        await ctx.message.channel.send(embed=embed)

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def rename(self, ctx, monster_id: int, name):
        monster_db = db.Monster.get(monster_id)
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)[0]
        
        if monster_db is None:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
            return

        #id, old_name, type, level, exhausted_timestamp, guild_id, owner_id = row
        if monster_db.guild_id != ctx.guild.id or monster_db.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
            return

        if len(name) > 100:
            await ctx.message.channel.send(f'The new name can not be longer than 100 characters.')

        db.Monster.rename(id, name)
        await ctx.message.channel.send(f'**{monster_db.name}** has been successfully renamed to **{name}**')

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def combine(self, ctx, monster1: int, monster2: int, monster3: int):
        monsters =  [monster1, monster2, monster3]
        data = []
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        
        for monster in monsters:
            monster_db = db.Monster.get(monster)
        
            if monster_db is None:
                await ctx.message.channel.send(f'Monster with id {monster} not found in your collection')
                return

            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = row
            data.append(monster_db)
            if monster_db.guild_id != ctx.guild.id or monster_db.owner_id != user_id:
                await ctx.message.channel.send(f'Monster with id {monster} not found in your collection')
                return

        if not (data[0].type == data[1].type == data[2].type):
            await ctx.message.channel.send(f'The Monsters are not matching in type')
            return
        if not (data[0].level == data[1].level == data[2].level):
            await ctx.message.channel.send(f'The Monsters are not matching in level')
            return

        for m in data:
            db.Monster.remove(m.id)

        owner_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        db.Monster.create(data[0].type, data[0].level+1, ctx.guild.id, owner_id)

        stars = ''.join(['★' for i in range(data[0].level)])

        await ctx.message.channel.send(f'**{data[0].type} [{stars}]** were combined into **{data[0].type} [{stars}★]**')


    @commands.command(aliases=['gift'])
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def give(self, ctx, receiver: discord.ext.commands.MemberConverter, given_id: int):
        if receiver is None:
            await ctx.message.channel.send('User not found')
            return
        receiver_db = db.User.get_by_member(ctx.guild.id, receiver.id)
        if receiver_db is None:
            await ctx.message.channel.send('User not found')
            return

        given = db.Monster.get(given_id)
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        if given is None:
            await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
            return
        if given.guild_id != ctx.guild.id or given.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
            return

        title = 'Gift Offer'
        description = f'{ctx.message.author} offers {lib.embeds.monster_full_title(given.id, given.name, given.type, given.level, given.exhausted_timestamp)}'
        description += f' to {receiver.mention}'

        embed = discord.Embed(title=title, description=description)
        embed.set_author(name=str(ctx.message.author), icon_url=ctx.message.author.avatar_url)

        message = await ctx.message.channel.send(embed=embed)
        await message.add_reaction('✔️')

        def check(reaction, user):
            return user.id == receiver_db.user_id and reaction.message.id == message.id and str(reaction.emoji) == '✔️'

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.message.remove_reaction('✔️', ctx.me)
            title = 'Gift Offer Declined'
            embed.set_footer(text=title)
            await message.edit(embed=embed)
        else:
            given = db.Monster.get(given_id)
            user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
            if given is None:
                title = f'Huh? The monster has disappeared! The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return
            if given.guild_id != ctx.guild.id or given.owner_id != user_id:
                title = f'The monster has meanwhile changed owners. The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return

            title = 'Gift Offer Accepted'
            embed.set_footer(text=title)
            await message.edit(embed=embed)

            db.Monster.change_owner(given_id, receiver_db.id)


    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def release(self, ctx, given_id: int):

        given = db.Monster.get(given_id)
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        if given is None:
            await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
            return
        if given.guild_id != ctx.guild.id or given.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
            return

        title = 'Released Monster'
        description = f'{ctx.message.author} has released {lib.embeds.monster_full_title(given.id, given.name, given.type, given.level, given.exhausted_timestamp)}'
        description += f'\n React to this message to capture it for yourself.'

        embed = discord.Embed(title=title, description=description)
        embed.set_author(name=str(ctx.message.author), icon_url=ctx.message.author.avatar_url)

        message = await ctx.message.channel.send(embed=embed)
        await message.add_reaction('✔️')

        def check(reaction, user):
            return reaction.message.id == message.id and str(reaction.emoji) == '✔️' and not user.bot

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.message.remove_reaction('✔️', ctx.me)
            title = 'Monster has escaped'
            embed.set_footer(text=title)
            await message.edit(embed=embed)

            db.Monster.remove(given_id)
        else:
            given = db.Monster.get(given_id)
            user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
            if given is None:
                title = f'Huh? The monster has disappeared! The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return
            if given.guild_id != ctx.guild.id or given.owner_id != user_id:
                title = f'The monster has meanwhile changed owners. The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return

            user_db = db.User.get_by_member(ctx.guild.id, user.id)

            title = f'Monster has been captured by {user}'
            embed.set_footer(text=title)
            await message.edit(embed=embed)

            db.Monster.change_owner(given_id, user_db.id)


    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def trade(self, ctx, given_id: int, taken_id: int):
        given = db.Monster.get(given_id)
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        if given is None:
            await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
            return
        # id, name, type, level, exhausted_timestamp, guild_id, owner_id = given_row
        if given.guild_id != ctx.guild.id or given.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
            return

        taken = db.Monster.get(taken_id)
        if taken is None:
            await ctx.message.channel.send(f'Monster with id {taken_id} not found in your collection')
            return
        #id, name, type, level, exhausted_timestamp, guild_id, owner_id = taken_row
        if taken.guild_id != ctx.guild.id:
            await ctx.message.channel.send(f'Monster with id {taken_id} not found on this server')
            return

        owner_id = db.User.get(taken.owner_id).user_id
        owner = lib.getters.get_user_by_id(owner_id, ctx.guild.members)

        title = 'Trade Offer'
        # given_id, name, type, level, exhausted_timestamp, guild_id, owner_id = given_row
        description = f'{ctx.message.author} offers {lib.embeds.monster_full_title(given.id, given.name, given.type, given.level, given.exhausted_timestamp)}'
        #taken_id, name, type, level, exhausted_timestamp, guild_id, owner_id = taken_row
        description += f' in exchange for {lib.embeds.monster_full_title(taken.id, taken.name, taken.type, taken.level, taken.exhausted_timestamp)} by {owner.mention}'

        embed = discord.Embed(title=title, description=description)
        embed.set_author(name=str(ctx.message.author), icon_url=ctx.message.author.avatar_url)

        message = await ctx.message.channel.send(embed=embed)
        await message.add_reaction('✔️')

        owner_id = db.User.get(taken.owner_id).user_id
        def check(reaction, user):
            return user.id == owner_id and reaction.message.id == message.id and str(reaction.emoji) == '✔️'

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.message.remove_reaction('✔️', ctx.me)
            title = 'Trade Offer Declined'
            embed.set_footer(text=title)
            await message.edit(embed=embed)
        else:
            given = db.Monster.get(given_id)
            user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
            if given is None:
                title = f'Huh? The monster ``{given.id}`` has disappeared! The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return
            if given.guild_id != ctx.guild.id or given.owner_id != user_id:
                title = f'The monster  ``{given.id}`` has meanwhile changed owners. The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return

            taken = db.Monster.get(taken_id)
            owner_id = db.User.get(taken.owner_id).id
            if taken is None:
                title = f'Huh? The monster ``{taken.id}`` has disappeared! The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return
            if taken.guild_id != ctx.guild.id or taken.owner_id != owner_id:
                title = f'The monster  ``{taken.id}`` has meanwhile changed owners. The Exchange is cancelled.'
                embed.set_footer(text=title)
                await message.edit(embed=embed)
                return

            title = 'Trade Offer Accepted'
            embed.set_footer(text=title)
            await message.edit(embed=embed)

            owner_id = db.User.get_by_member(ctx.guild.id, owner.id).id
            db.Monster.change_owner(given_id, owner_id)

            owner_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
            db.Monster.change_owner(taken_id, owner_id)



class GroupCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='group')
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def group_main_command(self, ctx):
        pass


    @group_main_command.command()
    async def view(self, ctx, group_id: int):

        if not await lib.checks.group_exists(ctx, group_id):
            return

        group_db = db.Group.get(group_id)

        group_monsters_db = db.GroupMonster.get_by_group(group_id)

        await lib.embeds.group_embed(ctx, group_db, group_monsters_db)


    @group_main_command.command()
    async def add(self, ctx, group_id: int, monster_id: int):

        if not await lib.checks.group_allowed(ctx, group_id):
            return

        group_db = db.Group.get(group_id)

        monster = db.Monster.get(monster_id)
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        if monster is None:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
            return
        if monster.guild_id != ctx.guild.id or monster.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
            return

        group_monster = db.GroupMonster.get(monster_id, group_id)
        if group_monster is not None:
            await ctx.message.channel.send(f'This Monster is already in this group.')
            return

        group_monsters_db = db.GroupMonster.get_by_group(group_id)
        index = len(group_monsters_db)

        db.GroupMonster.create(monster_id, group_id, index)

        await ctx.message.channel.send(f'Monster ``{monster.name}`` added to group ``{group_db.name}``.')
        

    @group_main_command.command()
    async def remove(self, ctx, group_id: int, monster_id: int):

        if not await lib.checks.group_allowed(ctx, group_id):
            return

        group_db = db.Group.get(group_id)

        group_monster = db.GroupMonster.get(monster_id, group_id)
        if group_monster is None:
            await ctx.message.channel.send(f'Monster not found in this group.')
            return

        monster = db.Monster.get(monster_id)

        db.GroupMonster.remove(monster_id, group_id)

        group_monsters_db = db.GroupMonster.get_by_group(group_id)
        for i, m in enumerate(group_monsters_db):
            db.GroupMonster.change_index(m.monster_id, m.group_id, i)

        await ctx.message.channel.send(f'Monster ``{monster.name}`` removed from group ``{group_db.name}``.')


    @group_main_command.group(name='change')
    async def change(self, ctx):
        pass

    @change.command()
    async def name(self, ctx, id: int, new_name):

        if len(new_name) > 100:
            await ctx.message.channel.send(f'The group name can\'t be longer than 100 characters.')
            return

        if not await lib.checks.group_allowed(ctx, id):
            return

        db.Group.change_name(id, new_name)

        await ctx.message.channel.send('Name successfully changed.')

    @change.command()
    async def description(self, ctx, id: int, new_description):

        if len(new_description) > 500:
            await ctx.message.channel.send(f'The group description can\'t be longer than 500 characters.')
            return

        if not await lib.checks.group_allowed(ctx, id):
            return

        db.Group.change_description(id, new_description)

        await ctx.message.channel.send('Description successfully changed.')

    @change.command()
    async def favorite(self, ctx, id: int):

        if not await lib.checks.group_allowed(ctx, id):
            return

        group_db = db.Group.get(id)

        if group_db.favorite:
            favorite = True
        else:
            favorite = False

        favorite = not favorite

        db.Group.change_favorite(id, favorite)

        if favorite:
            await ctx.message.channel.send('Group has been favorited.')
        else:
            await ctx.message.channel.send('Group has been unfavorited.')

    @group_main_command.command()
    async def create(self, ctx, name, description=''):

        if len(name) > 100:
            await ctx.message.channel.send(f'The group name can\'t be longer than 100 characters.')
            return

        if len(description) > 500:
            await ctx.message.channel.send(f'The group description can\'t be longer than 500 characters.')
            return

        user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)

        db.Group.create(ctx.guild.id, user_db.id, name, description)

        await ctx.message.channel.send(f'Group ``{name}`` successfully created.')


    @group_main_command.command()
    async def delete(self, ctx, id: int):

        if not await lib.checks.group_allowed(ctx, id):
            return

        db.Group.remove(id)
        await ctx.message.channel.send(f'Group successfully deleted.')



def setup(bot):
    bot.add_cog(UserCog(bot))
    bot.add_cog(MonsterCog(bot))
    bot.add_cog(GroupCog(bot))