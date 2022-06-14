import json
import time

def parse_config():
    with open('config.json') as f:
        data = json.load(f)
    return data

config = parse_config()


def get_glory(created_timestamp):
    delta = (time.time() - created_timestamp)
    glory = int((delta/(3600*24)) * 10)
    if glory > 0:
        glory += 1
    return glory

def get_stat(monster, stat, level):
    return (monster[stat] + 3 * (level-1))

def get_modifier(monster, stat, level):
    return (get_stat(monster, stat, level) - 10) // 2

def get_hp(base_hp, level):
    return int(base_hp * (level/2 + 1/2))

def get_ac(base_ac, level):
    return base_ac + (level-1)