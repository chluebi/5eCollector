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

def normalize_visual_cr(cr):
    if type(cr) is dict:
        cr = normalize_visual_cr(cr['cr'])
    
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

    data = []
    for file in os.listdir(path):
        with open(os.path.join(path, file)) as f:
            data += json.load(f)['monster']
    
    traits = {}
    monsters = {}
    for monster in data:
        try:
            cr = normalize_cr(monster['cr'])
            visual_cr = normalize_visual_cr(monster['cr'])

            name = monster['name']
            lowercase = name.lower()

            source = monster['source']

            allowed = ['beast', 'monstrosity', 'dragon', 'undead', 'demon', 'aberration', 'elemental']
            allowed += ['shapechanger', 'construct', 'devil', 'giant', 'plant', 'fey', 'elf']
            allowed += ['yuan-ti', 'yugoloth', 'goblinoid', 'orc', 'gith', 'ooze', 'dwarf', 'celestial']

            monster_traits = []

            if type(monster['type']) is dict:
                if 'type' in monster['type']:
                    if monster['type']['type'] in allowed:
                        monster_traits.append(monster['type']['type'])

                for tag in monster['type']['tags']:
                    if tag in allowed:
                        monster_traits.append(tag)
            else:
                if monster['type'] in allowed:
                    monster_traits.append(monster['type'])

            if 'environment' in monster:
                for env in monster['environment'][:3]:
                    monster_traits.append(env)

            damage_full = {
                "A": "acid",
                "B": "bludgeoner",
                "C": "cold",
                "F": "fire",
                "O": "force",
                "L": "lightning",
                "N": "necrotic",
                "P": "piercer",
                "I": "poison",
                "Y": "psychic",
                "R": "radiant",
                "S": "slasher",
                "T": "thunder",
            }

            if 'damageTags' in monster:
                for tag in monster['damageTags']:
                    monster_traits.append(damage_full[tag])


            for trait in monster_traits:
                if trait not in traits:
                    traits[trait] = 1
                else:
                    traits[trait] += 1

            monster_traits = monster_traits[:max(3, int(cr//3))]

            monsters[monster['name']] = {
                'name': monster['name'],
                'type': get_type(monster['type']),
                'traits': monster_traits,
                'cr': cr,
                'visual_cr': visual_cr,
                'hp': monster['hp']['average'],
                'ac': get_ac(monster['ac'][0]),
                'str': monster['str'],
                'dex': monster['dex'],
                'con': monster['con'],
                'int': monster['int'],
                'wis': monster['wis'],
                'cha': monster['cha'],
                'link': f'https://5e.tools/bestiary.html#{lowercase}_{source.lower()}'.replace(' ', '%20'),
                'source': source,
                'image': f'https://5e.tools/img/{source}/{name}.png'.replace(' ', '%20')
            }
        except Exception as e:
            continue

    l = sorted(list(traits.items()), key=lambda x: x[1], reverse=True)

    l = sorted([(monster['name'], monster['traits']) for _, monster in monsters.items()], key=lambda x: len(x[1]), reverse=True)
    for monster, traits in l:
        pass
    
    return monsters


monsters = load_monsters()


def random_monster():
    viable = []
    for _, monster in monsters.items():
        if monster['cr'] <= 1 or random.random() < (3/(monster['cr'])):
            viable.append(monster)

    return random.choice(viable)

def get_monster(name):
    if name in monsters:
        return monsters[name]
    else:
        return None