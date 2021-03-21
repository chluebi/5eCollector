import os
import json
import random

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
            'cr': cr,
            'visual_cr': monster['cr'],
            'link': f'https://5e.tools/bestiary.html#{lowercase}_mm'.replace(' ', '%20'),
            'image': f'https://5e.tools/img/MM/{name}.png'.replace(' ', '%20')
        }

    return monsters


monsters = load_monsters()

def random_monster(max_cr):
    viable = []
    for name, monster in monsters.items():
        if monster['cr'] <= max_cr or random.random() < 0.1:
            viable.append(monster)

    return random.choice(viable)