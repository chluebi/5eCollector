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
import lib.checks
import lib.getters
import lib.embeds

config = lib.util.config

logging.basicConfig(handlers=[logging.FileHandler('bot.log', 'a', encoding='utf-8')], format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='col ', intents=intents)
bot.remove_command('help')



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
        message = f'An error has occurred: ```{error}```'
        await ctx.message.channel.send(message)
        logging.error(error_message)


@bot.command()
async def help(ctx):
    await ctx.message.channel.send(f'Help can be found here: https://chluebi.github.io/5eCollector/')

initial_extensions = [
    'bot.admin',
    'bot.combat',
    'bot.manage',
    'bot.rolling',
]


for extension in initial_extensions:
    bot.load_extension(extension)


bot.run(config['discord']['token'])