import discord
from discord.ext import commands
import time
import traceback
import sys
import asyncio
import random
import logging

import lib.util
import lib.database as db
import lib.time_handle
import lib.resources

config = lib.util.config

logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='col ', intents=intents)
bot.remove_command('help')


async def guild_exists(id):
    row = db.Guild.get(id)
    if row is None:
        return False
    else:
        return True
    
            
async def guild_exists_check(ctx):
    return await guild_exists(ctx.guild.id)



async def user_exists(id, guild_id):
    row = db.User.get_by_member(guild_id, id)
    if row is None:
        db.User.create(id, guild_id, time.time())
        return True
    else:
        return True

async def user_exists_check(ctx):
    return await user_exists(ctx.message.author.id, ctx.guild.id)


def get_user(name, members):
    user = discord.utils.find(lambda m: m.mention == name.replace('!', ''), members)
    if user is not None:
        return user
    user = discord.utils.find(lambda m: m.display_name == name, members)
    if user is not None:
        return user
    user = discord.utils.find(lambda m: m.name == name, members)
    if user is not None:
        return user
    user = discord.utils.find(lambda m: str(m) == name, members)
    if user is not None:
        return user

    try:
        user = discord.utils.find(lambda m: m.id == int(name), members)
    except:
        pass
    if user is not None:
        return user

    return None

def get_user_by_id(id, members):
    user = discord.utils.find(lambda m: m.id == int(id), members)
    if user is not None:
        return user

    return None

async def user_info(user, ctx):
    if user is None or not await user_exists(user.id, ctx.guild.id):
        await ctx.message.channel.send(f'User not found')
        return

    user_db = db.User.get_by_member(ctx.guild.id, user.id)

    if user_db is None:
        await ctx.message.channel.send(f'User not found')
        return

    roll_countdown = (user_db.roll_timestamp + config['game']['roll_cooldown']) - time.time()
    if roll_countdown > 0:
        roll_text = f'**{user_db.rolls}** (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)'
    else:
        roll_text = '**' + str(config['game']['rolls']) + '**'

    catch_countdown = (user_db.catch_timestamp + config['game']['catch_cooldown']) - time.time()
    if catch_countdown > 0:
        catch_text = f'**{user_db.catches}** (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)'
    else:
        catch_text = '**' + str(config['game']['catches']) + '**'
    desc = f'''
Score: **{user_db.score}**
Rolls Remaining: {roll_text}
Catches Remaining: {catch_text}
    '''
    embed = discord.Embed(title=f'{user} ({ctx.guild})', description=desc)
    embed.set_thumbnail(url=user.avatar_url)

    chosen = db.Chosen.get_by_owner(ctx.guild.id, user_db.id)
    if chosen is not None:
        monster = db.Monster.get(chosen.monster_id)

        text = lib.resources.monster_full_title(monster.id, monster.name, monster.type, monster.level, monster.exhausted_timestamp)

        delta = (time.time() - chosen.created_timestamp)
        glory = int((delta/(3600*24))**2 // (1/10))
        if glory > 0:
            glory += 1

        text += f' [Glory: {glory}] [HP: {chosen.hp}]'
            
        embed.add_field(name='Chosen', value=text)

    monsters = ['']
    monsters_db = db.Monster.get_by_owner(ctx.guild.id, user_db.id)
    monsters_db.sort(key=lambda x: x.id)
    if len(monsters_db) > 0:
        for monster_db in monsters_db:
            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster
            monster = lib.resources.get_monster(monster_db.type)

            text = lib.resources.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp) + '\n'
            
            if len(monsters[-1]) + len(text) > 1000:
                monsters.append(text)
            else:
                monsters[-1] += text

        for page in monsters:
            embed.add_field(name='Monsters', value=page, inline=False)

    await ctx.message.channel.send(embed=embed)


@bot.event
async def on_ready():
    print('------------------')
    print(f'bot ready {bot.user.name}')
    print('------------------')

@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    error_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.message.channel.send('It seems like this bot has not been initialized on this server, an admin has to run ``col init`` first.')
        logging.warning(error_message)
    else:
        message = f'An error has occured: ```{error}```'
        await ctx.message.channel.send(message)
        logging.error(error_message)


@bot.command()
async def help(ctx):
    await ctx.message.channel.send(f'Help can be found here: https://chluebi.github.io/5eCollector/')


@commands.has_permissions(administrator = True)
@bot.command()
async def init(ctx):
    if await guild_exists(ctx.guild.id):
        await ctx.message.channel.send('This server has already been initialized.')
        return
    
    await ctx.message.channel.send('Initializing **5eCollector** for this server...')
    db.Guild.create(ctx.guild.id)
    await ctx.message.channel.send('Initalized.')


@commands.has_permissions(administrator = True)
@bot.command()
async def uninit(ctx):
    if not await guild_exists(ctx.guild.id):
        await ctx.message.channel.send('This server has not been initialized yet.')
        return
    
    await ctx.message.channel.send('Removing **5eCollector** from this server...')
    db.Guild.remove(ctx.guild.id)
    await ctx.message.channel.send('Removed.')


@bot.command()
@commands.has_permissions(administrator = True)
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def give(ctx, user_name, monster_name):
    user = get_user(user_name, ctx.guild.members)
    
    if user is None or not await user_exists(user.id, ctx.guild.id):
        await ctx.message.channel.send(f'User {user_name} not found')
        return

    monster = lib.resources.get_monster(monster_name)
    if monster is None:
        await ctx.message.channel.send(f'Monster {monster_name} not found')
        return

    owner_id = db.User.get_by_member(ctx.guild.id, user.id).id
    db.Monster.create(monster['name'], 1, ctx.guild.id, owner_id)
    await ctx.message.channel.send(f'{user.mention} has been given {monster_name}')
    


@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def resetme(ctx):
    db.User.remove(ctx.message.author.id, ctx.guild.id)
    await ctx.message.channel.send('All your data on this server has been deleted')


@bot.command(aliases=['m'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def me(ctx):
    user = ctx.message.author
    await user_info(user, ctx)

@bot.command(aliases=['u', 'user'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def userinfo(ctx, user_name):
    user = get_user(user_name, ctx.guild.members)

    await user_info(user, ctx)


@bot.command(aliases=['ex', 'roll'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def explore(ctx):
    #id, user_id, _, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
    user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)

    if user_db.rolls < 1:
        roll_countdown = (user_db.roll_timestamp + config['game']['roll_cooldown']) - time.time()
        if roll_countdown > 0:
            await ctx.send(f'You are out of rolls. (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)')
            return
        else:
            db.User.roll(ctx.message.author.id, ctx.guild.id, config['game']['rolls']-1, time.time())
    else:
        db.User.roll(ctx.message.author.id, ctx.guild.id, user_db.rolls-1, None)

    db.User.set_score(ctx.message.author.id, ctx.guild.id, user_db.score+1)

    monster = lib.resources.random_monster()
    embed = lib.resources.generate_monster_embed(monster)

    message = await ctx.send(embed=embed)

    db.FreeMonster.create(monster['name'], ctx.guild.id, ctx.message.channel.id, message.id)
    await message.add_reaction('🗨️')


@bot.event
async def on_raw_reaction_add(payload):
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    user = guild.get_member(payload.user_id)


    ctx = await bot.get_context(message)

    if user.bot is True:
        return
    
    if payload.emoji.name == '🗨️':
        user_db = db.User.get_by_member(ctx.guild.id, user.id)
        if user_db is None:
            return

        #id, user_id, _, score, rolls, roll_timestamp, catches, catch_timestamp = row

        if user_db.catches < 1:
            catch_countdown = (user_db.catch_timestamp + config['game']['catch_cooldown']) - time.time()
            if catch_countdown > 0:
                await ctx.send(f'You are out of catches. (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)')
                return
            else:
                db.User.catch(user.id, ctx.guild.id, config['game']['catches']-1, time.time())
        else:
            db.User.catch(user.id, ctx.guild.id, user_db.catches-1, None)
        db.User.set_score(user.id, ctx.guild.id, user_db.score+10)

        free_monster_db = db.FreeMonster.get(ctx.guild.id, ctx.message.channel.id, ctx.message.id)

        if free_monster_db is None:
            return

        db.FreeMonster.remove(free_monster_db.id)
        owner_id = db.User.get_by_member(ctx.guild.id, user.id).id
        db.Monster.create(free_monster_db.type, 1, ctx.guild.id, owner_id)

        monster = lib.resources.get_monster(free_monster_db.type)

        embed = lib.resources.generate_monster_embed(monster)

        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_footer(text=f'claimed by {user}')
        await ctx.message.edit(embed=embed)
        await ctx.message.remove_reaction('🗨️', ctx.me)


@bot.command(aliases=['monster'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def view(ctx, monster):
    try:
        monster_id = int(monster)

        monster_db = db.Monster.get(monster_id)
        if monster_db is None:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found')
            return
        #id, name, type, level, exhausted_timestamp, guild_id, owner_id = row
        monster = lib.resources.get_monster(monster_db.type)

        user_db = db.User.get(monster_db.owner_id)
        owner = get_user_by_id(user_db.user_id, ctx.guild.members)

        chosen_db = db.Chosen.get_by_monster(monster_db.id)
        chosen = chosen_db is not None
        hp = chosen.type if chosen else 0

        embed = lib.resources.generate_caught_monster_embed(monster_db.name, monster, owner, monster_db.level, monster_db.exhausted_timestamp, chosen=chosen, hp=hp)
    except ValueError:
        monster= lib.resources.get_monster(monster)
        embed = lib.resources.generate_monster_embed(monster)

    await ctx.message.channel.send(embed=embed)

@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def rename(ctx, monster_id: int, name):
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


@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def combine(ctx, monster1: int, monster2: int, monster3: int):
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
    db.Monster.create(data[0].level, data[0].level+1, ctx.guild.id, owner_id)

    stars = ''.join(['★' for i in range(data[0][3])])

    await ctx.message.channel.send(f'**{data[0][1]} [{stars}]** were combined into **{data[0][1]} [{stars}★]**')


@bot.command(aliases=['t', 'exchange'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def trade(ctx, given_id: int, taken_id: int):
    given_row = db.Monster.get(given_id)
    user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
    if given_row is None:
        await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
        return
    id, name, type, level, exhausted_timestamp, guild_id, owner_id = given_row
    if guild_id != ctx.guild.id or owner_id != user_id:
        await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
        return

    taken_row = db.Monster.get(taken_id)
    if taken_row is None:
        await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
        return
    id, name, type, level, exhausted_timestamp, guild_id, owner_id = taken_row
    if guild_id != ctx.guild.id:
        await ctx.message.channel.send(f'Monster with id {given_id} not found on this server')
        return

    owner_id = db.User.get(owner_id)[1]
    owner = get_user_by_id(owner_id, ctx.guild.members)

    title = 'Trade Offer'
    given_id, name, type, level, exhausted_timestamp, guild_id, owner_id = given_row
    description = f'{ctx.message.author} offers {lib.resources.monster_full_title(id, name, type, level, exhausted_timestamp)}'
    taken_id, name, type, level, exhausted_timestamp, guild_id, owner_id = taken_row
    description += f' in exchange for {lib.resources.monster_full_title(id, name, type, level, exhausted_timestamp)} by {owner.mention}'

    embed = discord.Embed(title=title, description=description)
    embed.set_author(name=str(ctx.message.author), icon_url=ctx.message.author.avatar_url)

    message = await ctx.message.channel.send(embed=embed)
    await message.add_reaction('✔️')

    owner_id = db.User.get(owner_id)[1]
    def check(reaction, user):
        return user.id == owner_id and reaction.message.id == message.id and str(reaction.emoji) == '✔️'

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await ctx.message.remove_reaction('✔️', ctx.me)
        title = 'Trade Offer Declined'
        embed = discord.Embed(title=title, url=message.jump_url)
        await ctx.message.channel.send(embed=embed)
    else:
        title = 'Trade Offer Accepted'
        embed = discord.Embed(title=title, url=message.jump_url)

        owner_id = db.User.get_by_member(ctx.guild.id, owner.id).id
        db.Monster.change_owner(given_id, owner_id)

        owner_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        db.Monster.change_owner(taken_id, owner_id)

        await ctx.message.channel.send(embed=embed)


@bot.command(aliases=['choose', 'chose'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def chosen(ctx, monster_id: int):
    user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id

    monster_db = db.Monster.get(monster_id)
    if monster_db is None:
        await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
        return
    #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster_row
    if monster_db.guild_id != ctx.guild.id or monster_db.owner_id != user_id:
        await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
        return

    owner_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
    chosen_db = db.Chosen.get_by_owner(ctx.guild.id, owner_id)
    if chosen_db is not None:
        #id, hp, guild_id, owner_id, old_monster_id, created_timestamp = row

        delta = (time.time() - chosen_db.created_timestamp)
        glory = int((delta/(3600*24))**2 // (1/10))
        if glory > 0:
            glory += 1

        user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
        #id, user_id, _, score, rolls, roll_timestamp, catches, catch_timestamp = row
        db.User.set_score(ctx.message.author.id, ctx.guild.id, user_db.score+glory)

        await ctx.message.channel.send(f'You have gained {glory} glory with your chosen.')

        db.Chosen.remove_by_owner(user_db.id)

        db.Monster.exhaust(chosen_db.monster_id, time.time()+(3600*24))

        if monster_id == chosen_db.monster_id:
            return

    if time.time() < monster_db.exhausted_timestamp:
        delta = monster_db.exhausted_timestamp - time.time()
        await ctx.message.channel.send(f'The chosen monster is exhausted and will be ready in {lib.time_handle.seconds_to_text(delta)}')
        return

    monster = lib.resources.get_monster(monster_db.type)
    hp = monster['hp']

    db.Chosen.create(hp, ctx.guild.id, owner_id, monster_db.id, time.time())
    await ctx.message.channel.send(f'#{monster_db.id} **{monster_db.name}** ascended to become {ctx.message.author.mention}\'s Chosen')


@bot.command(aliases=['raid', 'a'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def attack(ctx, target, monster_id, stat):

    target = get_user(target, ctx.guild.members)
    user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id

    if target is None:
        await ctx.message.channel.send(f'User *{target}* not found.')
        return

    async def send_message():
        await ctx.message.channel.send('\n'.join(messages))


    def attack_monster(boss_db, attacker_db):
        #chosen_id, hp, guild_id, owner_id, monster_id, created_timestamp = boss_row

        boss_monster_db = db.Monster.get(boss_db.monster_id)
        #id, boss_name, type, boss_level, exhausted_timestamp, guild_id, owner_id = boss_monster_row
        boss_monster = lib.resources.get_monster(boss_monster_db.type)

        #attacker_id, attacker_name, type, attacker_level, exhausted_timestamp, guild_id, owner_id = attacker_row
        attacker_monster = lib.resources.get_monster(boss_monster_db.type)

        def modifier(m, s, l):
            return (m[s] + 3 * (l-1) - 10) // 2


        messages = []

        db.Monster.exhaust(attacker_db.id, time.time()+(3600))

        defense_roll = random.randint(1, 20) 
        attack_roll = random.randint(1, 20)

        if attack_roll + modifier(attacker_monster, stat, attacker_db.level) > defense_roll + modifier(boss_monster, stat, boss_monster_db.level):
            messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) overpowers **{boss_monster_db.name}** ({defense_roll}+{modifier(boss_monster, stat, boss_monster_db.level)})')
        else:
            messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) does not manage to attack **{boss_monster_db.name}** ({defense_roll}+{modifier(boss_monster, stat, boss_monster_db.level)})')
            return messages

        defense_roll = boss_monster['ac']

        if attack_roll + modifier(attacker_monster, stat, attacker_db.level) > defense_roll:
            messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) manages to land a hit on **{boss_monster_db.name}** (AC: {defense_roll})')
        else:
            messages.append(f'**{boss_monster_db.name}** (AC: {defense_roll}) manages to deflect **{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)})')
            return messages

        messages.append(f'**{attacker_db.name}** deals **{attack_roll} + {modifier(attacker_monster, stat, attacker_db.level)}** to **{boss_monster_db.name}**')
        
        damage = attack_roll + modifier(attacker_monster, stat, attacker_db.level)

        if boss_db.hp - (damage) < 1:
            messages.append(f'**{boss_monster_db.name}** has been defeated')
            db.Chosen.remove(boss_db.id)

            delta = (time.time() - boss_db.created_timestamp)
            glory = int((delta/(3600*24))**2 // (1/10))
            if glory > 0:
                glory += 1

            user_db = db.User.get_by_member(ctx.guild.id, target.id)
            #id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, target.id)
            db.User.set_score(user_db.user_id, user_db.guild_id, user_db.score+glory)
            messages.append(f'{target.mention} has gained {glory} points from Glory.')
        else:
            db.Chosen.damage(boss_db.id, boss_db.hp - damage)

            delta = (time.time() - boss_db.created_timestamp)
            glory = int((delta/(3600*24))**2 // (1/10))
            if glory > 0:
                glory += 1
            
            glory = int(min(glory/10, int(glory/40*(attack_roll + modifier(attacker_monster, stat, attacker_db.level)))))

            user_db = db.User.get_by_member(ctx.guild.id, target.id)
            #id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, target.id)
            db.User.set_score(user_id, user_db.guild_id, user_db.score-glory)
            
            user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
            # id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
            db.User.set_score(ctx.message.author.id, ctx.guild.id, user_db.score+glory)
            messages.append(f'{ctx.message.author.mention} has stolen {glory} points by attacking {target}.')

        return messages

    stat = stat.lower()
    if stat not in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        await ctx.message.channel.send(f'Stat *{stat}* is not a valid stat.')
        return

    target_id = db.User.get_by_member(ctx.guild.id, target.id).id
    boss_db = db.Chosen.get_by_owner(ctx.guild.id, target_id)
    if boss_db is None:
        await ctx.message.channel.send(f'User does not have a Chosen at the moment')
        return

    if monster_id == 'all':
        attackers = []
        rows = db.Monster.get_by_owner(ctx.guild.id, user_id)
        for monster_db in rows:
            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster
            if time.time() < monster_db.exhausted_timestamp:
                continue
            
            attackers.append(monster_db.id)

        if len(attackers) < 1:
            await ctx.message.channel.send('All of your monsters are exhausted at the moment.')
            return

        messages = []
        for monster_id in attackers:
            monster_id = int(monster_id)
            attacker_db = db.Monster.get(monster_id)

            if attacker_db is None:
                await ctx.message.channel.send(f'Monster with id *{monster_id}* not found in your collection')
                return

            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = attacker_row
            if attacker_db.guild_id != ctx.guild.id or attacker_db.owner_id != user_id:
                await ctx.message.channel.send(f'Monster with id *{monster_id}* not found in your collection')
                return

            if time.time() < attacker_db.exhausted_timestamp:
                delta = attacker_db.exhausted_timestamp - time.time()
                await ctx.message.channel.send(f'The chosen monster is exhausted and will be ready in {lib.time_handle.seconds_to_text(delta)}')
                return

            messages.append('')
            messages += attack_monster(boss_db, attacker_db)

        formatted_message = ['']
        for m in messages:
            if len(formatted_message[-1]) + len(m) > 1800:
                formatted_message.append(m)
            else:
                formatted_message[-1] += m + '\n'

        for m in formatted_message:
            await ctx.message.channel.send(m)
    else:
        monster_id = int(monster_id)
        attacker_db = db.Monster.get(monster_id)

        if attacker_db is None:
            await ctx.message.channel.send(f'Monster with id *{monster_id}* not found in your collection')
            return
        #id, name, type, level, exhausted_timestamp, guild_id, owner_id = attacker_row
        if attacker_db.guild_id != ctx.guild.id or attacker_db.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id *{monster_id}* not found in your collection')
            return

        if time.time() < attacker_db.exhausted_timestamp:
            delta = attacker_db.exhausted_timestamp - time.time()
            await ctx.message.channel.send(f'The chosen monster is exhausted and will be ready in {lib.time_handle.seconds_to_text(delta)}')
            return

        messages = attack_monster(boss_db, attacker_db)

        await send_message()


@bot.command(aliases=['stat', 'ranking'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def stats(ctx, category):

    ranking = []
    ranking_title = ''

    if category == 'points':

        ranking_title = '**Ranking by Points**'
        rows = db.User.get_by_guild(ctx.guild.id)
        
        for user_db in rows:
            #user_db_id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = row
            user = ctx.guild.get_member(user_db.user_id)
            if user is not None:
                ranking.append((user_db.score, f'{user} ({user_db.score})'))

    elif category == 'glory':
        ranking_title = '**Ranking by Glory**'
        rows = db.Chosen.get_by_guild(ctx.guild.id)

        for chosen_db in rows:
            #id, hp, guild_id, owner_id, monster_id, created_timestamp = row
            user = ctx.guild.get_member(db.User.get(chosen_db.owner_id).user_id)

            monster_db = db.Monster.get(chosen_db.monster_id)
            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster_row

            text = lib.resources.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp)

            delta = (time.time() - chosen_db.created_timestamp)
            glory = int((delta/(3600*24))**2 // (1/10))
            if glory > 0:
                glory += 1

            text += f' [Glory: {glory}] [HP: {chosen_db.hp}]'
            text = f'{user}\'s ' + text

            ranking.append((glory, text))
    elif category == 'monster':
        ranking_title = '**Ranking by Monsters**'
        rows = db.User.get_by_guild(ctx.guild.id)

        for user_db in rows:
            #user_db_id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = row
            monster_rows = db.Monster.get_by_owner(user_db.guild_id, user_db.id)
            user = ctx.guild.get_member(user_db.user_id)
            ranking.append((len(monster_rows), f'{user} ({len(monster_rows)})'))
    else:
        return

    ranking = sorted(ranking, key=lambda x: x[0], reverse=True)

    message = ['']
    for i, (_, rank) in enumerate(ranking, 1):
        if len(message[-1]) + len(rank) > 1800:
            message.append(rank)
        else:
            message[-1] += f'#{i} ' + rank + '\n'


    message = [f'```{m}```' for m in message]

    message[-1] = f'{ranking_title}\n' + message[-1]

    for m in message:
        await ctx.message.channel.send(m)



bot.run(config['discord']['token'])