import discord
from discord.ext import commands
import time
import traceback
import sys

import lib.util
import lib.database as db
import lib.time_handle
import lib.resources

config = lib.util.config

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='col ')


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
        db.User.create(id, guild_id)
        return True
    else:
        return True

async def user_exists_check(ctx):
    return await user_exists(ctx.message.author.id, ctx.guild.id)

@bot.event
async def on_ready():
    print('------------------')
    print(f'bot ready {bot.user.name}')
    print('------------------')

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
@commands.check(user_exists_check)
async def resetme(ctx):
    db.User.remove(ctx.message.author.id, ctx.guild.id)
    await ctx.message.channel.send('All your data has been deleted')


@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def info(ctx, aliases=['info']):
    row = db.User.get(ctx.message.author.id, ctx.guild.id)
    print(row)

    explore_countdown = (row[4] + config['game']['roll_cooldown']) - time.time()
    explore_countdown_text = '(Resets in **{lib.timehandle.seconds_to_text(explore_countdown)}**)' if explore_countdown > 0 else ''
    catch_countdown = (row[6] + config['game']['catch_cooldown']) - time.time()
    catches_countdown_text = '(Resets in **{lib.timehandle.seconds_to_text(catch_countdown)}**)' if catch_countdown > 0 else ''
    msg = f'''
**{ctx.message.author}** ({ctx.guild})
Level: **{row[2]}**
Explores Remaining: **{row[3]}** {explore_countdown_text}
Catches Remaining: **{row[5]}** {catches_countdown_text}
    '''
    await ctx.message.channel.send(msg)


@bot.command()
@commands.check(guild_exists_check)
@commands.check(user_exists_check)
async def explore(ctx, aliases=['ex']):
    _, _, level, rolls, roll_cooldown, catches, catch_cooldown = db.User.get(ctx.message.author.id, ctx.guild.id)

    monster = lib.resources.random_monster(level)
    print(monster)

    embed = discord.Embed(title=monster['name'], url=monster['link'])
    embed.set_image(url=monster['image'])
    message = await ctx.send(embed=embed)

    db.FreeMonster.create(monster['name'], ctx.guild.id, ctx.message.channel.id, message.id)
    await message.add_reaction('🗨️')

@bot.event
async def on_reaction_add(reaction, user):
    ctx = await bot.get_context(reaction.message)

    if user.bot is True:
        return
    
    if reaction.emoji == '🗨️':
        row = db.FreeMonster.get(ctx.guild.id, ctx.message.channel.id, ctx.message.id)

        if row is None:
            return

        db.FreeMonster.remove(row[0])
        db.Monster.create(row[1], ctx.guild.id, user.id)

        await ctx.message.channel.send(f'**{user}** claimed **{row[1]}**')
        await ctx.message.add_reaction('❎')


bot.run(config['discord']['token'])