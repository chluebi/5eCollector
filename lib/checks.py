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
    if not await guild_exists(guild_id):
        return False
    row = db.User.get_by_member(guild_id, id)
    if row is None:
        db.User.create(id, guild_id, time.time())
        return True
    else:
        return True

async def user_exists_check(ctx):
    return await user_exists(ctx.message.author.id, ctx.guild.id)


async def group_exists(ctx, group_id):
    group_db = db.Group.get(group_id)
    if group_db is None:
        await ctx.message.channel.send(f'Group with id ``{group_id}`` not found.')
        return False
    else:
        return True


async def group_allowed(ctx, group_id):
    group_db = db.Group.get(group_id)
    if group_db is None:
        await ctx.message.channel.send(f'Group with id ``{group_id}`` not found.')
        return False

    user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
    if group_db.owner_id != user_db.id:
        await ctx.message.channel.send(f'This Group does not belong to you.')
        return False

    return True