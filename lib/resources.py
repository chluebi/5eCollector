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

            monster_traits = []

            damage_full = {
                "A": "acid",
                "B": "crusher",
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
                "T": "thunder"
            }

            if 'damageTags' in monster:
                if 'B' in monster['damageTags']:
                    monster_traits.append(damage_full['B'])
                elif 'S' in monster['damageTags']:
                    monster_traits.append(damage_full['S'])
                else:
                    monster_traits.append(damage_full['P'])
            else:
                monster_traits.append('pacifist')

                
            allowed = ['beast', 'monstrosity', 'dragon', 'undead', 'demon', 'aberration', 'elemental']
            allowed += ['shapechanger', 'construct', 'devil', 'giant', 'plant', 'fey', 'elf']
            allowed += ['yuan-ti', 'yugoloth', 'goblinoid', 'orc', 'gith', 'ooze', 'dwarf', 'celestial']

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

            if 'damageTags' in monster:
                for tag in monster['damageTags']:
                    if tag not in ['B', 'P', 'S']:
                        monster_traits.append(damage_full[tag])

            if 'environment' in monster:
                for env in monster['environment'][:int(max(3, cr**(2/5) // 1))]:
                    monster_traits.append(env)

            monster_traits = monster_traits[:int(max(3, 3*cr**(3/4)//1))]

            if 'spellcasting' in monster:
                if 'type' in monster:
                    if 'type' in monster['type']:
                        if monster['type']['type'] in ['humanoid']:
                            if 'tags' in monster['type']:
                                if 'any race' in monster['type']['tags']:
                                    monster_traits.append('spellcaster')
                    elif monster['type'] in ['undead']:
                        monster_traits.append('spellcaster')

            for trait in monster_traits:
                if trait not in traits:
                    traits[trait] = 1
                else:
                    traits[trait] += 1

            

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

    traits = sorted(list(traits.items()), key=lambda x: x[1], reverse=True)
    for trait, amount in traits:
        pass
        #print(trait, amount)

    l = sorted([(monster['name'], monster['traits']) for _, monster in monsters.items()], key=lambda x: len(x[1]), reverse=True)
    for monster, monster_traits in l:
        pass
        #print(monster, monster_traits)
    
    return monsters, traits


monsters, traits = load_monsters()

import lib.traits

for trait, amount in traits:
    lib.traits.traits[trait]['amount'] = amount


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
        for monster, data in monsters.items():
            if monster.lower() == name.lower() or data['name'].lower() == name.lower():
                return data
        return None