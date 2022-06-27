import discord


def get_user(name, members):
    user = discord.utils.find(lambda m: m.mention == name.replace('!', ''), members)
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