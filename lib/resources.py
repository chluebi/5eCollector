import os
import json
import random
import math
import discord

import lib.util

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
        get_type(typus['type'])
    else:
        return typus

def load_monsters():
    path = lib.util.config['resources_path']
    with open(path + '/data/bestiary/bestiary-mm.json') as f:
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

def generate_monster_embed(monster):
    title = monster['name'] + ' CR: ' + monster['visual_cr']
    description = monster['type']
    embed = discord.Embed(title=title, description=description, url=monster['link'])

    for stat in ['str', 'wis', 'con', 'int', 'wis', 'dex']:
        modifier = (monster[stat] - 10) // 2
        if modifier > 0:
            value = f'{monster[stat]} (+{modifier})'
        else:
            value = f'{monster[stat]} ({modifier})'
        embed.add_field(name=stat.upper(), value=value, inline=True)
    embed.set_image(url=monster['image'])

    return embed

def generate_caught_monster_embed(name, monster, owner, level):
    stars = ''.join(['★' for i in range(level)])
    title = name + ' CR: ' + monster['visual_cr'] + f' [{stars}]'
    description = monster['type']
    if name != monster['name']:
        description = monster['name'] + ', ' + description
    embed = discord.Embed(title=title, description=description, url=monster['link'])

    for stat in ['str', 'wis', 'con', 'int', 'wis', 'dex']:
        monster[stat] = monster[stat] + level * 3
        modifier = (monster[stat] - 10) // 2
        if modifier > 0:
            value = f'{monster[stat]} (+{modifier})'
        else:
            value = f'{monster[stat]} ({modifier})'
        embed.add_field(name=stat.upper(), value=value, inline=True)
    embed.set_image(url=monster['image'])

    embed.set_author(name=str(owner), icon_url=owner.avatar_url)

    return embed