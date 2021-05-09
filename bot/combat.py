import discord
from discord.ext import commands
import asyncio
import time
import random

import lib.checks
import lib.database as db
import lib.embeds
import lib.util

config = lib.util.config

class ChosenCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def chosen(self, ctx, monster_id: int):
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id

        monster_db = db.Monster.get(monster_id)
        if monster_db is None:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
            return
        #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster_row
        if monster_db.guild_id != ctx.guild.id or monster_db.owner_id != user_id:
            await ctx.message.channel.send(f'Monster with id {monster_id} not found in your collection')
            return

        owner_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        chosen_db = db.Chosen.get_by_owner(ctx.guild.id, owner_id)
        if chosen_db is not None:
            #id, hp, guild_id, owner_id, old_monster_id, created_timestamp = row
            
            glory = lib.util.get_glory(chosen_db.created_timestamp)

            user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
            #id, user_id, _, score, rolls, roll_timestamp, catches, catch_timestamp = row
            db.User.set_score(ctx.message.author.id, ctx.guild.id, user_db.score+glory)

            await ctx.message.channel.send(f'You have gained {glory} glory with your chosen.')

            db.Chosen.remove_by_owner(user_db.id)

            db.Monster.exhaust(chosen_db.monster_id, time.time()+config['game']['combat']['chosen_exhaust_cooldown'])

            if monster_id == chosen_db.monster_id:
                return

        if time.time() < monster_db.exhausted_timestamp:
            delta = monster_db.exhausted_timestamp - time.time()
            await ctx.message.channel.send(f'The chosen monster is exhausted and will be ready in {lib.time_handle.seconds_to_text(delta)}')
            return

        monster = lib.resources.get_monster(monster_db.type)
        hp = lib.util.get_hp(monster['hp'], monster_db.level)

        db.Chosen.create(hp, ctx.guild.id, owner_id, monster_db.id, time.time())
        await ctx.message.channel.send(f'#{monster_db.id} **{monster_db.name}** ascended to become {ctx.message.author.mention}\'s Chosen')


class CombatCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def attack(self, ctx, target, group_id, stat):

        target = lib.getters.get_user(target, ctx.guild.members)
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id

        if target is None:
            await ctx.message.channel.send(f'User *{target}* not found.')
            return

        async def send_message():
            await ctx.message.channel.send('\n'.join(messages))


        def attack_monster(boss_db, attacker_db):
            #chosen_id, hp, guild_id, owner_id, monster_id, created_timestamp = boss_row

            boss_monster_db = db.Monster.get(boss_db.monster_id)
            #id, boss_name, type, boss_level, exhausted_timestamp, guild_id, owner_id = boss_monster_row
            boss_monster = lib.resources.get_monster(boss_monster_db.type)

            #attacker_id, attacker_name, type, attacker_level, exhausted_timestamp, guild_id, owner_id = attacker_row
            attacker_monster = lib.resources.get_monster(attacker_db.type)

            modifier = lib.util.get_modifier

            messages = []

            db.Monster.exhaust(attacker_db.id, time.time()+config['game']['combat']['exhaust_cooldown'])

            defense_roll = random.randint(1, 20) 
            attack_roll = random.randint(1, 20)

            if attack_roll + modifier(attacker_monster, stat, attacker_db.level) > defense_roll + modifier(boss_monster, stat, boss_monster_db.level):
                messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) overpowers **{boss_monster_db.name}** ({defense_roll}+{modifier(boss_monster, stat, boss_monster_db.level)})')
            else:
                messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) does not manage to attack **{boss_monster_db.name}** ({defense_roll}+{modifier(boss_monster, stat, boss_monster_db.level)})')
                return messages, 0

            defense_roll = lib.util.get_ac(boss_monster['ac'], boss_monster_db.level)

            if attack_roll + modifier(attacker_monster, stat, attacker_db.level) > defense_roll:
                messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) manages to land a hit on **{boss_monster_db.name}** (AC: {defense_roll})')
            else:
                messages.append(f'**{boss_monster_db.name}** (AC: {defense_roll}) manages to deflect **{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)})')
                return messages, 0

            messages.append(f'**{attacker_db.name}** deals **{attack_roll} + {modifier(attacker_monster, stat, attacker_db.level)}** to **{boss_monster_db.name}**')
            
            damage = attack_roll + modifier(attacker_monster, stat, attacker_db.level)
            return messages, damage



        stat = stat.lower()
        if stat not in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
            await ctx.message.channel.send(f'Stat *{stat}* is not a valid stat.')
            return

        target_id = db.User.get_by_member(ctx.guild.id, target.id).id
        boss_db = db.Chosen.get_by_owner(ctx.guild.id, target_id)
        if boss_db is None:
            await ctx.message.channel.send(f'User does not have a Chosen at the moment')
            return

        if group_id == 'all':
            await ctx.message.channel.send('You cannot attack with all monsters, you may only attack with groups of only up to 10 monsters.')
            return

        group_monsters_db = db.GroupMonster.get_by_group(group_id)

        if len(group_monsters_db) < 1:
            await ctx.message.channel.send(f'No monsters in group with group-id ``{group_id}`` found.')
            return

        if len(group_monsters_db) > 10:
            await ctx.message.channel.send(f'Only Groups of up to ``10`` monsters may attack.')
            return

        monsters_db = []
        for group_monster_db in group_monsters_db:
            monsters_db.append(db.Monster.get(group_monster_db.monster_id))

        attackers = []
        for monster_db in monsters_db:
            if time.time() < monster_db.exhausted_timestamp:
                continue
            
            attackers.append(monster_db.id)

        if len(attackers) < 1:
            await ctx.message.channel.send('All of the monsters in this group are exhausted at the moment.')
            return

        damage = 0
        messages = []
        for monster_id in attackers:
            monster_id = int(monster_id)
            attacker_db = db.Monster.get(monster_id)

            if attacker_db is None:
                await ctx.message.channel.send(f'Monster with id *{monster_id}* not found in your collection')
                return

            #id, name, type, level, exhausted_timestamp, guild_id, owner_id = attacker_row
            if attacker_db.guild_id != ctx.guild.id or attacker_db.owner_id != user_id:
                await ctx.message.channel.send(f'Monster with id *{monster_id}* not found in your collection')
                return

            if time.time() < attacker_db.exhausted_timestamp:
                delta = attacker_db.exhausted_timestamp - time.time()
                await ctx.message.channel.send(f'The chosen monster is exhausted and will be ready in {lib.time_handle.seconds_to_text(delta)}')
                return

            messages.append('')
            m, d = attack_monster(boss_db, attacker_db)
            messages += m
            damage += d

        boss_monster_db = db.Monster.get(boss_db.monster_id)

        damage_msg = f'{boss_monster_db.name} takes a total of {damage} damage.'
        messages.append(damage_msg)
        if boss_db.hp - (damage) < 1:
            db.Chosen.remove(boss_db.id)
            db.Monster.exhaust(boss_db.monster_id, time.time()+config['game']['combat']['chosen_exhaust_cooldown'])

            glory = lib.util.get_glory(boss_db.created_timestamp)
            defeated_msg = f'\n **{boss_monster_db.name}** has been defeated with {glory} glory.'
            messages.append(defeated_msg)
        else:
            defeated_msg = ''
            db.Chosen.damage(boss_db.id, boss_db.hp - damage)

        summary_msg = f'{damage_msg}{defeated_msg}\n\nReact to this message if you want to see the entire summary of the Battle.'
        summary_message = await ctx.message.channel.send(summary_msg)

        await summary_message.add_reaction('✔️')
        def check(reaction, user):
            return not user.bot and reaction.message.id == summary_message.id and str(reaction.emoji) == '✔️'

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.message.remove_reaction('✔️', ctx.me)
        else:
            formatted_message = ['']
            for m in messages:
                if len(formatted_message[-1]) + len(m) > 1800:
                    formatted_message.append(m)
                else:
                    formatted_message[-1] += m + '\n'

            messages = []
            for m in formatted_message:
                messages.append(await ctx.message.channel.send(m))

            summary_msg += '\n Full Summary: {messages[0].jump_url}'
            await summary_message.edit(content=summary_msg)

def setup(bot):
    bot.add_cog(ChosenCog(bot))
    bot.add_cog(CombatCog(bot))