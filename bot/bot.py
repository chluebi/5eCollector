import discord
from discord.ext import commands
import time
import traceback
import sys
import asyncio

import lib.util
import lib.database as db
import lib.time_handle
import lib.resources

config = lib.util.config

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='col ', intents=intents)


async def guild_exists(id):
    row = db.Guild.get(id)
    if row is None:
        return False
    else:
        return True
    
            
async def guild_exists_check(ctx):
    return await guild_exists(ctx.guild.id)



async def user_exists(id, guild_id):
    row = db.User.get(id, guild_id)
    if row is None:
        db.User.create(id, guild_id, time.time())
        return True
    else:
        return True

async def user_exists_check(ctx):
    return await user_exists(ctx.message.author.id, ctx.guild.id)


def get_user(name, members):
    user = discord.utils.find(lambda m: m.mention == name, members)
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
    if isinstance(error, commands.errors.CheckFailure):
        pass
    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@bot.command()
@commands.check(user_exists_check)
async def test(ctx):
    await ctx.message.channel.send(':speech_left:')


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

    monster_name = monster_name.capitalize()
    monster = lib.resources.get_monster(monster_name)
    if monster is None:
        await ctx.message.channel.send(f'Monster {monster_name} not found')
        return

    db.Monster.create(monster['name'], 1, ctx.guild.id, user.id)
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
    row = db.User.get(ctx.message.author.id, ctx.guild.id)

    roll_countdown = (row[4] + config['game']['roll_cooldown']) - time.time()
    if roll_countdown > 0:
        roll_text = f'**{row[3]}** (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)'
    else:
        roll_text = '**' + str(config['game']['rolls']) + '**'

    catch_countdown = (row[6] + config['game']['catch_cooldown']) - time.time()
    if catch_countdown > 0:
        catch_text = f'**{row[5]}** (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)'
    else:
        catch_text = '**' + str(config['game']['catches']) + '**'
    desc = f'''
Score: **{row[2]}**
Rolls Remaining: {roll_text}
Catches Remaining: {catch_text}
    '''
    embed = discord.Embed(title=f'{ctx.message.author} ({ctx.guild})', description=desc)
    embed.set_thumbnail(url=ctx.message.author.avatar_url)

    monsters = ['']
    rows = db.Monster.get_by_owner(ctx.guild.id, ctx.message.author.id)
    if len(rows) > 0:
        for monster in rows:
            id, name, type, level, guild_id, owner_id = monster
            monster = lib.resources.get_monster(type)
            cr = monster['visual_cr']

            stars = ''.join(['★' for i in range(level)])
            if name == type:
                text = f'#{id} **{name}** [CR: {cr}] [{stars}] \n'
            else:
                text = f'#{id} **{name}** ({type}) [CR: {cr}] [{stars}] \n'
            
            if len(monsters[-1]) + len(text) > 1000:
                monsters.append(text)
            else:
                monsters[-1] += text

        for page in monsters:
            embed.add_field(name='Monsters', value=page, inline=False)

    await ctx.message.channel.send(embed=embed)

@bot.command(aliases=['u', 'user'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def userinfo(ctx, user_name):
    user = get_user(user_name, ctx.guild.members)

    if user is None or not await user_exists(user.id, ctx.guild.id):
        await ctx.message.channel.send(f'User {user_name} not found')
        return

    row = db.User.get(user.id, ctx.guild.id)

    if row is None:
        await ctx.message.channel.send(f'User {user_name} not found')
        return

    roll_countdown = (row[4] + config['game']['roll_cooldown']) - time.time()
    if roll_countdown > 0:
        roll_text = f'**{row[3]}** (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)'
    else:
        roll_text = '**' + str(config['game']['rolls']) + '**'

    catch_countdown = (row[6] + config['game']['catch_cooldown']) - time.time()
    if catch_countdown > 0:
        catch_text = f'**{row[5]}** (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)'
    else:
        catch_text = '**' + str(config['game']['catches']) + '**'
    desc = f'''
Score: **{row[2]}**
Rolls Remaining: {roll_text}
Catches Remaining: {catch_text}
    '''
    embed = discord.Embed(title=f'{user} ({ctx.guild})', description=desc)
    embed.set_thumbnail(url=user.avatar_url)

    monsters = ['']
    rows = db.Monster.get_by_owner(ctx.guild.id, user.id)
    if len(rows) > 0:
        for monster in rows:
            id, name, type, level, guild_id, owner_id = monster
            monster = lib.resources.get_monster(type)
            cr = monster['visual_cr']

            stars = ''.join(['★' for i in range(level)])
            if name == type:
                text = f'#{id} **{name}** [CR: {cr}] [{stars}] \n'
            else:
                text = f'#{id} **{name}** ({type}) [CR: {cr}] [{stars}] \n'
            
            if len(monsters[-1]) + len(text) > 1000:
                monsters.append(text)
            else:
                monsters[-1] += text

        for page in monsters:
            embed.add_field(name='Monsters', value=page, inline=False)

    await ctx.message.channel.send(embed=embed)


@bot.command(aliases=['ex', 'roll'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def explore(ctx):
    _, _, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get(ctx.message.author.id, ctx.guild.id)

    if rolls < 1:
        roll_countdown = (roll_timestamp + config['game']['roll_cooldown']) - time.time()
        if roll_countdown > 0:
            await ctx.send(f'You are out of rolls. (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)')
            return
        else:
            db.User.roll(ctx.message.author.id, ctx.guild.id, config['game']['rolls'], time.time())

    db.User.roll(ctx.message.author.id, ctx.guild.id, rolls-1, None)
    db.User.score(ctx.message.author.id, ctx.guild.id, score+1)

    monster = lib.resources.random_monster()
    embed = lib.resources.generate_monster_embed(monster)

    message = await ctx.send(embed=embed)

    db.FreeMonster.create(monster['name'], ctx.guild.id, ctx.message.channel.id, message.id)
    await message.add_reaction('🗨️')


@bot.event
async def on_reaction_add(reaction, user):
    ctx = await bot.get_context(reaction.message)

    if user.bot is True:
        return
    
    if reaction.emoji == '🗨️':
        row = db.User.get(user.id, ctx.guild.id)
        if row is None:
            return

        _, _, score, rolls, roll_timestamp, catches, catch_timestamp = row

        if catches < 1:
            catch_countdown = (catch_timestamp + config['game']['catch_cooldown']) - time.time()
            if catch_countdown > 0:
                await ctx.send(f'You are out of catches. (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)')
                return
            else:
                db.User.catch(user.id, ctx.guild.id, config['game']['catches'], time.time())

        db.User.catch(user.id, ctx.guild.id, catches-1, None)
        db.User.score(user.id, ctx.guild.id, score+10)

        row = db.FreeMonster.get(ctx.guild.id, ctx.message.channel.id, ctx.message.id)

        if row is None:
            return

        db.FreeMonster.remove(row[0])
        db.Monster.create(row[1], 1, ctx.guild.id, user.id)

        monster = lib.resources.get_monster(row[1])

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

        row = db.Monster.get(monster_id)
        if row is None:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found')
            return
        id, name, type, level, guild_id, owner_id = row
        monster = lib.resources.get_monster(type)

        owner = get_user_by_id(owner_id, ctx.guild.members)

        embed = lib.resources.generate_caught_monster_embed(name, monster, owner, level)
    except ValueError:
        monster= lib.resources.get_monster(monster)
        embed = lib.resources.generate_monster_embed(monster)

    await ctx.message.channel.send(embed=embed)

@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def rename(ctx, monster_id: int, name):
    row = db.Monster.get(monster_id)
    
    if row is None:
        await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
        return

    id, old_name, type, level, guild_id, owner_id = row
    if guild_id != ctx.guild.id or owner_id != ctx.message.author.id:
        await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
        return

    if len(name) > 100:
        await ctx.message.channel.send(f'The new name can not be longer than 100 characters.')

    db.Monster.rename(id, name)
    await ctx.message.channel.send(f'**{old_name}** has been successfully renamed to **{name}**')


@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def combine(ctx, monster1: int, monster2: int, monster3: int):
    monsters =  [monster1, monster2, monster3]
    data = []
    
    for monster in monsters:
        row = db.Monster.get(monster)
    
        if row is None:
            await ctx.message.channel.send(f'Monster with id {monster} not found in your collection')
            return

        id, name, type, level, guild_id, owner_id = row
        data.append(row)
        if guild_id != ctx.guild.id or owner_id != ctx.message.author.id:
            await ctx.message.channel.send(f'Monster with id {monster} not found in your collection')
            return

    if not (data[0][2] == data[1][2] == data[2][2]):
        await ctx.message.channel.send(f'The Monsters are not matching in type')
        return
    if not (data[0][3] == data[1][3] == data[2][3]):
        await ctx.message.channel.send(f'The Monsters are not matching in level')
        return

    for row in data:
        db.Monster.remove(row[0])

    db.Monster.create(data[0][1], data[0][3]+1, ctx.guild.id, ctx.message.author.id)

    stars = ''.join(['★' for i in range(data[0][3])])

    await ctx.message.channel.send(f'**{data[0][1]} [{stars}]** were combined into **{data[0][1]} [{stars}★]**')


@bot.command(aliases=['t', 'exchange'])
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def trade(ctx, given_id: int, taken_id: int):
    given_row = db.Monster.get(given_id)
    if given_row is None:
        await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
        return
    id, name, type, level, guild_id, owner_id = given_row
    if guild_id != ctx.guild.id or owner_id != ctx.message.author.id:
        await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
        return

    taken_row = db.Monster.get(taken_id)
    if taken_row is None:
        await ctx.message.channel.send(f'Monster with id {given_id} not found in your collection')
        return
    id, name, type, level, guild_id, owner_id = taken_row
    if guild_id != ctx.guild.id:
        await ctx.message.channel.send(f'Monster with id {given_id} not found on this server')
        return

    owner = get_user_by_id(owner_id, ctx.guild.members)

    def monster_full_title(name, type, level):
        cr = lib.resources.get_monster(type)['visual_cr']
        stars = ''.join(['★' for i in range(level)])
        if name != type:
            return f'**{name}** ({type}) [Cr: {cr}] [{stars}]'
        else:
            return f'**{name}** [Cr: {cr}] [{stars}]'

    title = 'Trade Offer'
    given_id, name, type, level, guild_id, owner_id = given_row
    description = f'{ctx.message.author} offers {monster_full_title(name, type, level)}'
    taken_id, name, type, level, guild_id, owner_id = taken_row
    description += f' in exchange for {monster_full_title(name, type, level)} by {owner.mention}'

    embed = discord.Embed(title=title, description=description)
    embed.set_author(name=str(ctx.message.author), icon_url=ctx.message.author.avatar_url)

    message = await ctx.message.channel.send(embed=embed)
    await message.add_reaction('✔️')

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
        db.Monster.change_owner(given_id, owner.id)
        db.Monster.change_owner(taken_id, ctx.message.author.id)
        await ctx.message.channel.send(embed=embed)


bot.run(config['discord']['token'])