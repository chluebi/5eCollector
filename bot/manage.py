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
    async def me(self, ctx):
        user = ctx.message.author
        await lib.embeds.user_info(user, ctx)

    @commands.command(aliases=['user'])
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def userinfo(self, ctx, user_name):
        user = lib.getters.get_user(user_name, ctx.guild.members)
        await lib.embeds.user_info(user, ctx)

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def resetme(self, ctx):
        db.User.remove(ctx.message.author.id, ctx.guild.id)
        await ctx.message.channel.send('All your data on this server has been deleted')

    
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


    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def give(self, ctx, receiver, given_id: int):
        receiver = lib.getters.get_user(receiver, ctx.guild.members)
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
            return reaction.message.id == message.id and str(reaction.emoji) == '✔️'

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

            title = f'Monster has been captured by {user.mention}'
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

class StatsCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def stats(self, ctx, category, start=1, l=10, order='+'):

        ranking = []
        ranking_title = ''

        if category in ['points']:

            ranking_title = '**Ranking by Points**'
            rows = db.User.get_by_guild(ctx.guild.id)
            
            for user_db in rows:
                #user_db_id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = row
                user = ctx.guild.get_member(user_db.user_id)
                if user is not None:
                    ranking.append((user_db.score, f'{user} ({user_db.score})'))

        elif category in ['glory']:
            ranking_title = '**Ranking by Glory**'
            rows = db.Chosen.get_by_guild(ctx.guild.id)

            for chosen_db in rows:
                #id, hp, guild_id, owner_id, monster_id, created_timestamp = row
                user = ctx.guild.get_member(db.User.get(chosen_db.owner_id).user_id)

                monster_db = db.Monster.get(chosen_db.monster_id)
                #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster_row

                text = lib.embeds.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp)

                glory = lib.util.get_glory(chosen_db.created_timestamp)

                text += f' **[Glory: {glory}]** [HP: {chosen_db.hp}]'
                text = f'{user}\'s ' + text

                ranking.append((glory, text))

        elif category in ['monster', 'monsters']:
            ranking_title = '**Ranking by Monsters**'
            rows = db.User.get_by_guild(ctx.guild.id)

            for user_db in rows:
                #user_db_id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = row
                monster_rows = db.Monster.get_by_owner(user_db.guild_id, user_db.id)
                user = ctx.guild.get_member(user_db.user_id)
                ranking.append((len(monster_rows), f'{user} ({len(monster_rows)})'))

        elif category in ['level', 'hp', 'ac', 'str', 'dex', 'con', 'int', 'wis', 'cha']:
            ranking_title = f'**Ranking by {category.capitalize()}**'
            monsters = db.Monster.get_by_guild(ctx.guild.id)

            if category in ['level']:
                for monster_db in monsters:
    
                    user_db = db.User.get(monster_db.owner_id)
                    user = lib.getters.get_user_by_id(user_db.user_id, ctx.guild.members)

                    text = lib.embeds.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp)
                    
                    text += f' **[Level: {monster_db.level}]**'
                    text = f'{user}\'s ' + text

                    ranking.append((monster_db.level, text))
            else:
                
                for monster_db in monsters:
                    monster = lib.resources.get_monster(monster_db.type)

                    user_db = db.User.get(monster_db.owner_id)
                    user = lib.getters.get_user_by_id(user_db.user_id, ctx.guild.members)

                    text = lib.embeds.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp)
                    
                    if category in ['hp']:
                        stat = lib.util.get_hp(monster['hp'], monster_db.level)
                    elif category in ['ac']:
                        stat = lib.util.get_ac(monster['ac'], monster_db.level)
                    elif category in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                        stat = lib.util.get_stat(monster, category, monster_db.level)

                    text += f' **[{category.capitalize()}: {stat}]**'
                    text = f'{user}\'s ' + text

                    ranking.append((stat, text))
        else:
            return

        ranking = sorted(ranking, key=lambda x: x[0], reverse=True)
        leaderboard = list(enumerate(ranking, 1))

        l = min(l, 100)
        start = start - 1
        total = len(leaderboard)
        end = min(l, len(leaderboard[::-1][start:]))

        end = start + end
        
        if order in ['-']:
            leaderboard = leaderboard[::-1]

        leaderboard = leaderboard[start:end]
        if order in ['-']:
            end, start = start+1, end-1
        
        ranking_subtitle = f'From #{leaderboard[0][0]} to #{leaderboard[-1][0]} [Total: {total}]'

        message = ['']

        for i, (_, rank) in leaderboard:
            if len(message[-1]) + len(rank) > 1800:
                message.append(f'**#{i}** ' + rank + '\n')
            else:
                message[-1] += f'**#{i}** ' + rank + '\n'


        message = [f'{m}' for m in message]


        message[0] =  f'{ranking_title}\n' + f'{ranking_subtitle}\n' + message[0]

        for m in message:
            await ctx.message.channel.send(m)

def setup(bot):
    bot.add_cog(UserCog(bot))
    bot.add_cog(MonsterCog(bot))
    bot.add_cog(StatsCog(bot))