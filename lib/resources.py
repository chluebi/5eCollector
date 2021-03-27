import os
import json
import random
import math
import time
import discord

import lib.util
import lib.time_handle

config = lib.util.config

def normalize_cr(cr):
    if type(cr) is dict:
        cr = normalize_cr(cr['cr'])
    elif not '/' in cr:
        cr = float(cr)
    else:
        cr_list = cr.split('/')
        cr = float(int(cr_list[0])/int(cr_list[1]))
    return cr

def get_type(typus):
    if type(typus) is dict:
        return get_type(typus['type'])
    else:
        return typus

def get_ac(ac):
    if type(ac) is dict:
        return get_ac(ac['ac'])
    else:
        return ac

def load_monsters():
    path = lib.util.config['resources_path']
    with open(path) as f:
        data = json.load(f)['monster']

    monsters = {}
    for monster in data:
        cr = normalize_cr(monster['cr'])

        name = monster['name']
        lowercase = name.lower()

        monsters[monster['name']] = {
            'name': monster['name'],
            'type': get_type(monster['type']),
            'cr': cr,
            'visual_cr': monster['cr'],
            'hp': monster['hp']['average'],
            'ac': get_ac(monster['ac'][0]),
            'str': monster['str'],
            'dex': monster['dex'],
            'con': monster['con'],
            'int': monster['int'],
            'wis': monster['wis'],
            'cha': monster['cha'],
            'link': f'https://5e.tools/bestiary.html#{lowercase}_mm'.replace(' ', '%20'),
            'image': f'https://5e.tools/img/MM/{name}.png'.replace(' ', '%20')
        }

    return monsters


monsters = load_monsters()

def random_monster():
    viable = []
    for name, monster in monsters.items():
        if monster['cr'] <= 1 or random.random() < (3/(monster['cr'])):
            viable.append(monster)

    return random.choice(viable)

def get_monster(name):
    if name in monsters:
        return monsters[name]
    else:
        return None

def monster_full_title(id, name, type, level, exhausted_timestamp):
    cr = get_monster(type)['visual_cr']
    stars = ''.join(['★' for i in range(level)])
    if name != type:
        text = f'**{name}** ({type}) [Cr: {cr}] [{stars}]'
    else:
        text = f'**{name}** [Cr: {cr}] [{stars}]'

    if exhausted_timestamp > time.time():
        text += ' 😴'

    text = f'#{id} ' + text

    return text

def generate_monster_embed(monster):
    title = monster['name'] + ' CR: ' + monster['visual_cr']
    description = monster['type']
    embed = discord.Embed(title=title, description=description, url=monster['link'])

    for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        modifier = (monster[stat] - 10) // 2
        if modifier > 0:
            value = f'{monster[stat]} (+{modifier})'
        else:
            value = f'{monster[stat]} ({modifier})'
        embed.add_field(name=stat.upper(), value=value, inline=True)
    embed.set_image(url=monster['image'])

    return embed

def generate_caught_monster_embed(name, monster, owner, level, exhausted_timestamp, chosen=False, hp=0):
    stars = ''.join(['★' for i in range(level)])
    title = name + ' [CR: ' + monster['visual_cr'] + f'] [{stars}]'
    if chosen:
        title = f'[CHOSEN] [HP: {hp}] ' + title
    description = monster['type']
    if name != monster['name']:
        description = monster['name'] + ', ' + description
    embed = discord.Embed(title=title, description=description, url=monster['link'])

    if exhausted_timestamp > time.time():
        delta = exhausted_timestamp - time.time()
        value = f'Ready in {lib.time_handle.seconds_to_text(delta)}'
        embed.add_field(name='Exhausted 😴', value=value, inline=False)

    embed.add_field(name='Armor Class', value=monster['ac'], inline=False)

    for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        monster_stat = monster[stat] + level * 3
        modifier = (monster_stat - 10) // 2
        if modifier > 0:
            value = f'{monster_stat} (+{modifier})'
        else:
            value = f'{monster_stat} ({modifier})'
        embed.add_field(name=stat.upper(), value=value, inline=True)
    embed.set_image(url=monster['image'])

    embed.set_author(name=str(owner), icon_url=owner.avatar_url)

    return embed