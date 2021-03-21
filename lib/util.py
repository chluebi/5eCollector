import json

def parse_config():
    with open('config.json') as f:
        data = json.load(f)
    return data

config = parse_config()