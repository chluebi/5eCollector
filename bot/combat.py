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

    @commands.command(aliases=['choose', 'chose'])
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
        hp = monster['hp']

        db.Chosen.create(hp, ctx.guild.id, owner_id, monster_db.id, time.time())
        await ctx.message.channel.send(f'#{monster_db.id} **{monster_db.name}** ascended to become {ctx.message.author.mention}\'s Chosen')


class CombatCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['raid', 'a'])
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def attack(self, ctx, target, monster_id, stat):

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
                return messages

            defense_roll = boss_monster['ac']

            if attack_roll + modifier(attacker_monster, stat, attacker_db.level) > defense_roll:
                messages.append(f'**{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)}) manages to land a hit on **{boss_monster_db.name}** (AC: {defense_roll})')
            else:
                messages.append(f'**{boss_monster_db.name}** (AC: {defense_roll}) manages to deflect **{attacker_db.name}** ({attack_roll}+{modifier(attacker_monster, stat, attacker_db.level)})')
                return messages

            messages.append(f'**{attacker_db.name}** deals **{attack_roll} + {modifier(attacker_monster, stat, attacker_db.level)}** to **{boss_monster_db.name}**')
            
            damage = attack_roll + modifier(attacker_monster, stat, attacker_db.level)

            if boss_db.hp - (damage) < 1:
                messages.append(f'**{boss_monster_db.name}** has been defeated')
                db.Chosen.remove(boss_db.id)
                db.Monster.exhaust(boss_db.monster_id, time.time()+config['game']['combat']['chosen_exhaust_cooldown'])

                glory = lib.util.get_glory(boss_db.created_timestamp)

                user_db = db.User.get_by_member(ctx.guild.id, target.id)
                #id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, target.id)
                db.User.set_score(user_db.user_id, user_db.guild_id, user_db.score+glory)
                messages.append(f'{target.mention} has gained {glory} points from Glory.')
            else:
                db.Chosen.damage(boss_db.id, boss_db.hp - damage)

                glory = lib.util.get_glory(boss_db.created_timestamp)
                
                glory = int(min(glory/10, int(glory/40*(attack_roll + modifier(attacker_monster, stat, attacker_db.level)))))

                user_db = db.User.get_by_member(ctx.guild.id, target.id)
                #id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, target.id)
                db.User.set_score(user_id, user_db.guild_id, user_db.score-glory)
                
                user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
                # id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
                db.User.set_score(ctx.message.author.id, ctx.guild.id, user_db.score+glory)
                messages.append(f'{ctx.message.author.mention} has stolen {glory} points by attacking {target}.')

            return messages

        stat = stat.lower()
        if stat not in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
            await ctx.message.channel.send(f'Stat *{stat}* is not a valid stat.')
            return

        target_id = db.User.get_by_member(ctx.guild.id, target.id).id
        boss_db = db.Chosen.get_by_owner(ctx.guild.id, target_id)
        if boss_db is None:
            await ctx.message.channel.send(f'User does not have a Chosen at the moment')
            return

        if monster_id == 'all':
            attackers = []
            rows = db.Monster.get_by_owner(ctx.guild.id, user_id)
            for monster_db in rows:
                #id, name, type, level, exhausted_timestamp, guild_id, owner_id = monster
                if time.time() < monster_db.exhausted_timestamp:
                    continue
                
                attackers.append(monster_db.id)

            if len(attackers) < 1:
                await ctx.message.channel.send('All of your monsters are exhausted at the moment.')
                return

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
                messages += attack_monster(boss_db, attacker_db)

            formatted_message = ['']
            for m in messages:
                if len(formatted_message[-1]) + len(m) > 1800:
                    formatted_message.append(m)
                else:
                    formatted_message[-1] += m + '\n'

            for m in formatted_message:
                await ctx.message.channel.send(m)
        else:
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

            messages = attack_monster(boss_db, attacker_db)

            await send_message()

def setup(bot):
    bot.add_cog(ChosenCog(bot))
    bot.add_cog(CombatCog(bot))