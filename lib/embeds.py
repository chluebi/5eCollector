
import discord
import time

import lib.database as db
import lib.checks
import lib.resources
import lib.getters

config = lib.util.config

async def user_info(user, ctx):
    if user is None or not await lib.checks.user_exists(user.id, ctx.guild.id):
        await ctx.message.channel.send(f'User not found')
        return

    user_db = db.User.get_by_member(ctx.guild.id, user.id)

    if user_db is None:
        await ctx.message.channel.send(f'User not found')
        return

    roll_countdown = (user_db.roll_timestamp + config['game']['rolling']['roll_cooldown']) - time.time()
    if roll_countdown > 0:
        roll_text = f'**{user_db.rolls}** (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)'
    else:
        roll_text = '**' + str(config['game']['rolling']['rolls']) + '**'

    catch_countdown = (user_db.catch_timestamp + config['game']['rolling']['catch_cooldown']) - time.time()
    if catch_countdown > 0:
        catch_text = f'**{user_db.catches}** (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)'
    else:
        catch_text = '**' + str(config['game']['rolling']['catches']) + '**'
    desc = f'''
Score: **{user_db.score}**
Rolls Remaining: {roll_text}
Catches Remaining: {catch_text}
    '''
    embed = discord.Embed(title=f'{user} ({ctx.guild})', description=desc)
    embed.set_thumbnail(url=user.avatar_url)

    chosen = db.Chosen.get_by_owner(ctx.guild.id, user_db.id)
    if chosen is not None:
        monster = db.Monster.get(chosen.monster_id)

        text = monster_full_title(monster.id, monster.name, monster.type, monster.level, monster.exhausted_timestamp)

        glory = lib.util.get_glory(chosen.created_timestamp)

        text += f' [Glory: {glory}] [HP: {chosen.hp}]'
            
        embed.add_field(name='Chosen', value=text)

    

    groups = []
    groups_db = db.Group.get_by_owner(ctx.guild.id, user_db.id)

    if len(groups_db) > 0:
        for group_db in groups_db:
            if not group_db.favorite:
                continue
            group_monsters_db = db.GroupMonster.get_by_group(group_db.id)
            if len(group_monsters_db) < 1:
                continue
            groups.append([group_db, []])
            for group_monster_db in group_monsters_db:
                monster_db = db.Monster.get(group_monster_db.monster_id)
                monster = lib.resources.get_monster(monster_db.type)

                text = monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp) + '\n'

                groups[-1][1].append(text)


    fields = []
    for group_db, monsters in groups:
        title = f'Group: #{group_db.id} {group_db.name}'
        fields.append([title, ''])
        for monster in monsters:
            if len(fields[-1][1]) + len(monster) > 1000:
                fields.append([title, ''])

            fields[-1][1] += monster

    embeds = [embed]

    for name, value in fields:
        title = f'Group: #{group_db.id} {group_db.name}'
        if len(embed.fields) > 3:
            embed = discord.Embed(title=f'Continuation Groups of {user}', description=f'page {len(embeds) + 1}')
            
        embed.add_field(name=name, value=value, inline=False)

    for e in embeds:
        await ctx.message.channel.send(embed=e)

async def user_monsters(ctx, user, sort, reverse):
    user_db = db.User.get_by_member(ctx.guild.id, user.id)

    monsters = []
    monsters_db = db.Monster.get_by_owner(ctx.guild.id, user_db.id)

    title = f'Monsters of {str(user)} (sorted by {sort})'
    reverse = False if reverse != '+' else True

    if sort in ['id']:
        monsters_db.sort(key=lambda x: x.id, reverse=reverse)
    elif sort in ['level', 'hp', 'ac', 'str', 'dex', 'con', 'int', 'wis', 'cha']:
        if sort in ['level']:
            monsters_db.sort(key=lambda x: x.id, reverse=reverse)
        elif sort in ['hp']:
            def get_hp(monster_db):
                monster = lib.resources.get_monster(monster_db.type)
                hp = lib.util.get_hp(monster['hp'], monster_db.level)
                return hp
            monsters_db.sort(key=get_hp, reverse=reverse)
        elif sort in ['ac']:
            def get_ac(monster_db):
                monster = lib.resources.get_monster(monster_db.type)
                ac = lib.util.get_ac(monster['ac'], monster_db.level)
                return ac
            monsters_db.sort(key=get_ac, reverse=reverse)
        else:
            def get_stat(monster_db):
                monster = lib.resources.get_monster(monster_db.type)
                stat = lib.util.get_stat(monster, sort, monster_db.level)
                return stat
            monsters_db.sort(key=get_stat, reverse=reverse) 
    else:
        monsters_db.sort(key=lambda x: x.name, reverse=not reverse)
        title = f'Monsters of {str(user)} (sorted alphabetically)'

    for monster_db in monsters_db:
        text = monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp) + '\n'
        monsters.append(text)

    fields = ['']
    for monster in monsters:
        if len(fields[-1]) + len(monster) > 1000:
            fields.append('')
        fields[-1] += monster

    embed = discord.Embed(title=title)

    
    chosen = db.Chosen.get_by_owner(ctx.guild.id, user_db.id)
    if chosen is not None:
        monster = db.Monster.get(chosen.monster_id)

        text = monster_full_title(monster.id, monster.name, monster.type, monster.level, monster.exhausted_timestamp)

        glory = lib.util.get_glory(chosen.created_timestamp)

        text += f' [Glory: {glory}] [HP: {chosen.hp}]'
            
        embed.add_field(name='Chosen', value=text)

    embeds = [embed]

    for i, field in enumerate(fields, 1):
        if len(embed.fields) > 3:
            embeds.append(discord.Embed(title=f'Monsters of {str(user)}', description=f'page {len(embeds) + 1}'))
        embeds[-1].add_field(name=f'Section {i}', value=field, inline=False)

    for embed in embeds:
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_footer(text=f'Monsters of {user}')

    for e in embeds:
        await ctx.message.channel.send(embed=e)


async def group_embed(ctx, group_db, group_monsters_db):
    if group_db.favorite:
        title = f'Group: #{group_db.id} {group_db.name} [Favorite]' 
    else:
        title = f'Group: #{group_db.id} {group_db.name}'
    embed = discord.Embed(title=title, description=group_db.description)

    if len(group_monsters_db) > 0:
        monster_db = db.Monster.get(group_monsters_db[0].monster_id)
        first_monster = lib.resources.get_monster(monster_db.type)
    
    owner = db.User.get(group_db.owner_id)
    user = lib.getters.get_user_by_id(owner.user_id, ctx.guild.members)

    embeds = [embed]
    
    if len(group_monsters_db) > 0:
        monsters = ['']
        for group_monster_db in group_monsters_db:
            monster_db = db.Monster.get(group_monster_db.monster_id)

            text = monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp) + '\n'

            if len(monsters[-1]) + len(text) > 1000:
                monsters.append(text)
            else:
                monsters[-1] += text

        for i, page in enumerate(monsters):
            if len(embed.fields) > 3:
                embed = discord.Embed(title=f'Continuation Monsters of {group_db.name}', description=f'page {len(embeds) + 1}')
                embeds.append(embed)

            if len(monsters) > 1:
                embed.add_field(name=f'Monsters [{len(monsters)}] (Part #{i})', value=page, inline=False)
            else:
                embed.add_field(name=f'Monsters [{len(monsters)}]', value=page, inline=False)

    for embed in embeds:
        if len(group_monsters_db) > 0:
            embed.set_thumbnail(url=first_monster['image'])
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_footer(text=f'Group {group_db.name} by {user}')

    for e in embeds:
        await ctx.message.channel.send(embed=e)


def group_full_title(group_db, group_monsters_db):
    if group_db.favorite == 't':
        return f'#{group_db.id} **{group_db.name}** [len(group_monsters_db) Monsters] [Favorite]'
    else:
        return f'#{group_db.id} **{group_db.name}** [len(group_monsters_db) Monsters]'

                                
def monster_full_title(id, name, type, level, exhausted_timestamp):
    cr = lib.resources.get_monster(type)['visual_cr']
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

    embed.add_field(name='Armor Class', value=monster['ac'], inline=False)
    embed.add_field(name='HP (max hp)', value=monster['hp'], inline=False)

    for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        modifier = lib.util.get_modifier(monster, stat, 1)
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

    embed.add_field(name='Armor Class', value=lib.util.get_ac(monster['ac'], level), inline=False)
    embed.add_field(name='HP (max hp)', value=lib.util.get_hp(monster['hp'], level), inline=False)

    for stat in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
        monster_stat = lib.util.get_stat(monster, stat, level)
        modifier = lib.util.get_modifier(monster, stat, level)
        if modifier > 0:
            value = f'{monster_stat} (+{modifier})'
        else:
            value = f'{monster_stat} ({modifier})'
        embed.add_field(name=stat.upper(), value=value, inline=True)
    embed.set_thumbnail(url=monster['image'])

    embed.set_author(name=str(owner), icon_url=owner.avatar_url)

    return embed