import time

import lib.database as db

async def guild_exists(id):
    row = db.Guild.get(id)
    if row is None:
        return False
    else:
        return True
    
            
async def guild_exists_check(ctx):
    return await guild_exists(ctx.guild.id)



async def user_exists(id, guild_id):
    row = db.User.get_by_member(guild_id, id)
    if row is None:
        db.User.create(id, guild_id, time.time())
        return True
    else:
        return True

async def user_exists_check(ctx):
    return await user_exists(ctx.message.author.id, ctx.guild.id)