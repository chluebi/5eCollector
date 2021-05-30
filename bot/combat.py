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
    async def chosen(self, ctx, group_id: int):
        user_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id

        group_db = db.Group.get(group_id)
        if group_db is None:
            await ctx.message.channel.send(f'Group with id {group_id} not found in your collection')
            return
        if group_db.guild_id != ctx.guild.id or group_db.owner_id != user_id:
            await ctx.message.channel.send(f'Group with id {group_id} not found in your collection')
            return

        group_monsters_db = db.GroupMonster.get_by_group(group_id)
        if len(group_monsters_db) > 10:
            await ctx.message.channel.send(f'This Group has more than 10 members which means it can\'t become chosen.')
            return
            
        owner_id = db.User.get_by_member(ctx.guild.id, ctx.message.author.id).id
        chosen_db = db.Chosen.get_by_owner(ctx.guild.id, owner_id)
        if chosen_db is not None:
            
            glory = lib.util.get_glory(chosen_db.created_timestamp)

            user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)

            await ctx.message.channel.send(f'You have gained {glory} glory with your chosen.')

            db.Chosen.remove_by_owner(user_db.id)

            if group_id == chosen_db.group_id:
                return

        db.Chosen.create(ctx.guild.id, owner_id, group_db.id, time.time())
        await ctx.message.channel.send(f'``{group_db.name}``#``{group_db.id}`` ascended to become {ctx.message.author.mention}\'s Chosen')


class Fighter:
    
    def __init__(self, monster_db):
        self.alive = True
        self.action = None

        self.monster_db = monster_db
        self.monster = lib.resources.get_monster(self.monster_db.type)
        if self.monster is None:
            raise Exception(f'Monster of type {self.monster_db.type} not found')
        self.level = self.monster_db.level

        self.id = self.monster_db.id
        self.name = self.monster_db.name
        self.type = self.monster_db.type

        self.cr = self.monster['cr']
        self.hp = lib.util.get_hp(self.monster['hp'], self.level)
        self.max_hp = self.hp
        self.ac = lib.util.get_ac(self.monster['ac'], self.level)

        self.stats = {
                    'str': lib.util.get_stat(self.monster, 'str', self.level),
                    'dex': lib.util.get_stat(self.monster, 'dex', self.level),
                    'con': lib.util.get_stat(self.monster, 'con', self.level),
                    'int': lib.util.get_stat(self.monster, 'int', self.level),
                    'wis': lib.util.get_stat(self.monster, 'wis', self.level),
                    'cha': lib.util.get_stat(self.monster, 'cha', self.level)
                    }

        self.mods = {key: lib.util.get_modifier(self.monster, key, self.level) for key, value in self.stats.items()}

        self.image = self.monster['image']

    def __str__(self):
        s = ''
        if self.action == 'attack':
            s += '🗡️ '
        if self.action == 'defend':
            s += '🛡️ '

        s += f'#{self.id} {self.name} [{self.hp}/{self.max_hp}]'
        if not self.alive:
            s += ' 💀'

        return s


class Group:

    def __init__(self, id, name, monsters_db):
        self.id = id
        self.name = name
        self.fighters = [Fighter(monster_db) for monster_db in monsters_db]

    def __str__(self):
        return f'#{self.id} {self.name}'

    def alive(self):
        return True in [f.alive for f in self.fighters]

    def next_alive(self):
        for fighter in self.fighters[::-1]:
            if fighter.alive:
                return fighter
        return None


class Battle:
    
    def __init__(self, ctx, stat, defenders, attackers, def_user_db, att_user_db):
        self.round = 0
        self.history = []

        self.stat = stat
        self.ctx = ctx

        self.defenders = defenders
        self.attackers = attackers

        self.def_user_db = def_user_db
        self.att_user_db = att_user_db

    def start_embed(self):
        title = 'Battle'
        description = f'**{self.defenders}** vs **{self.attackers}**'
        embed = discord.Embed(title=title, description=description)

        value = f'AC reduced by **{self.round-1}**\n'
        value += f'Damage Multiplier: **{self.round}**' 
        embed.add_field(name=f'Round {self.round}', value=value, inline=False)

        embed.add_field(name=f'Attackers: {self.attackers}', value='\n'.join([str(f) for f in self.attackers.fighters]))
        embed.add_field(name=f'Defenders: {self.defenders}', value='\n'.join([str(f) for f in self.defenders.fighters]))
        
        embed.set_footer(text='In Progress 🕑')
        return embed

    async def message(self, content):
        self.history.append(content)
        embed = self.start_embed()
        embed.add_field(name='Current', value=content, inline=False)
        await self.start_message.edit(embed=embed)
        await asyncio.sleep(1.5)
    
    def damage(self, attacker, target, damage):
        target.hp -= damage

        if target.hp < 1:
            target.alive = False

    def attack(self, attacker, target):

        attacker.action = 'attack'
        target.action = 'defend'
        
        base_attack_roll = random.randint(1, 20)
        attack_roll = base_attack_roll + attacker.mods[self.stat]
        defense_roll = target.ac + 1 - self.round

        damage = 0

        info = ''

        if attack_roll <= defense_roll:
            info = f'(⚔️{base_attack_roll}+{attacker.mods[self.stat]}) {attacker} \n 🛡️ \n **(🔰{defense_roll})** {target} '
            return info

        base_damage_roll = random.randint(1, 20) * self.round
        damage_mod = attacker.mods[self.stat] * self.round
        damage_roll = base_damage_roll + damage_mod

        info = f'**(⚔️{base_attack_roll}+{attacker.mods[self.stat]})** {attacker}  \n 🗡️ \n (🔰{defense_roll}) {target} \n Damage: **(⚔️{base_damage_roll}+{damage_mod})**'
        
        self.damage(attacker, target, damage_roll)
        return info

    
    async def run(self):
        embed = self.start_embed()

        self.start_message = await self.ctx.message.channel.send(embed=embed)

        while True:
            self.round += 1
            await self.message(f'--- Round {self.round} ---')

            for defender in self.defenders.fighters:

                if not defender.alive:
                    continue

                target = self.attackers.next_alive()
                if target is None:
                    break

                info = self.attack(defender, target)
                await self.message(info)

                defender.action = None
                target.action = None


            for attacker in self.attackers.fighters:

                if not attacker.alive:
                    continue

                target = self.defenders.next_alive()
                if target is None:
                    break

                info = self.attack(attacker, target)
                await self.message(info)

                attacker.action = None
                target.action = None

            if not self.attackers.alive() or not self.defenders.alive():
                break
        
        if not self.defenders.alive():
            self.history.append('The attackers have won!')
        else:
            self.history.append('The chosen defenders have won!')

        title = 'Battle'
        description = f'**{self.defenders}** vs **{self.attackers}**'
        embed = discord.Embed(title=title, description=description)

        embed.add_field(name=self.defenders, value='\n'.join([str(f) for f in self.defenders.fighters]))
        embed.add_field(name=self.attackers, value='\n'.join([str(f) for f in self.attackers.fighters]))

        embed.set_footer(text='Finished, React for Full Summary')

        await self.start_message.edit(embed=embed)

        return not self.defenders.alive()



class CombatCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def ex_attack(self, ctx, target, group_id, stat):

        target = lib.getters.get_user(target, ctx.guild.members)
        user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)

        if target is None:
            await ctx.message.channel.send(f'User *{target}* not found.')
            return

        if user_db.attacks < 1:
            attack_countdown = (user_db.attack_timestamp + config['game']['combat']['attack_cooldown']) - time.time()
            if attack_countdown > 0:
                await ctx.send(f'You are out of attacks. (Resets in **{lib.time_handle.seconds_to_text(attack_countdown)}**)')
                return
            else:
                db.User.attack(ctx.message.author.id, ctx.guild.id, config['game']['combat']['attacks']-1, time.time())
        else:
            if user_db.attacks == config['game']['combat']['attacks']:
                db.User.attack(ctx.message.author.id, ctx.guild.id, user_db.attacks-1, time.time())
            else:
                db.User.attack(ctx.message.author.id, ctx.guild.id, user_db.attacks-1, None)


        stat = stat.lower()
        if stat not in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
            await ctx.message.channel.send(f'Stat *{stat}* is not a valid stat.')
            return

        target_db = db.User.get_by_member(ctx.guild.id, target.id)
        chosen_db = db.Chosen.get_by_owner(ctx.guild.id, target_db.id)
        if chosen_db is None:
            await ctx.message.channel.send(f'User does not have a Chosen group at the moment')
            return

        group_db = db.Group.get(chosen_db.group_id)
        group_monsters_db = db.GroupMonster.get_by_group(chosen_db.group_id)
        monsters_db = [db.Monster.get(m.monster_id) for m in sorted(group_monsters_db, key=lambda x: x.group_index)]
        defenders = Group(group_db.id, group_db.name, monsters_db)


        group_monsters_db = db.GroupMonster.get_by_group(group_id)

        if len(group_monsters_db) < 1:
            await ctx.message.channel.send(f'No monsters in group with group-id ``{group_id}`` found.')
            return

        if len(group_monsters_db) > 10:
            await ctx.message.channel.send(f'Only Groups of up to ``10`` monsters may attack.')
            return

        group_db = db.Group.get(group_id)
        group_monsters_db = db.GroupMonster.get_by_group(group_id)
        monsters_db = [db.Monster.get(m.monster_id) for m in sorted(group_monsters_db, key=lambda x: x.group_index)]
        attackers = Group(group_db.id, group_db.name, monsters_db)

        battle = Battle(ctx, stat, defenders, attackers, user_db, target_db)


        attack_win = await battle.run()

        if attack_win:
            db.Chosen.remove(chosen_db.id)
            #db.Monster.exhaust(boss_db.monster_id, time.time()+config['game']['combat']['chosen_exhaust_cooldown'])

            glory = lib.util.get_glory(chosen_db.created_timestamp)

        await battle.start_message.add_reaction('✔️')
        def check(reaction, user):
            return not user.bot and reaction.message.id == battle.start_message.id and str(reaction.emoji) == '✔️'

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.message.remove_reaction('✔️', ctx.me)
        else:
            summary_msg =''
            formatted_message = ['']
            for m in battle.history:
                if len(formatted_message[-1]) + len(m) > 1800:
                    formatted_message.append(m)
                else:
                    formatted_message[-1] += m + '\n'

            messages = []
            for m in formatted_message:
                messages.append(await ctx.message.channel.send(m))


    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def attack(self, ctx, target, group_id, stat):

        target = lib.getters.get_user(target, ctx.guild.members)
        user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)
        user_id = user_db.id

        if target is None:
            await ctx.message.channel.send(f'User *{target}* not found.')
            return

        if user_db.attacks < 1:
            attack_countdown = (user_db.attack_timestamp + config['game']['combat']['attack_cooldown']) - time.time()
            if attack_countdown > 0:
                await ctx.send(f'You are out of attacks. (Resets in **{lib.time_handle.seconds_to_text(attack_countdown)}**)')
                return
            else:
                db.User.attack(ctx.message.author.id, ctx.guild.id, config['game']['combat']['attacks']-1, time.time())
        else:
            if user_db.attacks == config['game']['combat']['attacks']:
                db.User.attack(ctx.message.author.id, ctx.guild.id, user_db.attacks-1, time.time())
            else:
                db.User.attack(ctx.message.author.id, ctx.guild.id, user_db.attacks-1, None)

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

            summary_msg += f'\n Full Summary: {messages[0].jump_url}'
            await summary_message.edit(content=summary_msg)

def setup(bot):
    bot.add_cog(ChosenCog(bot))
    bot.add_cog(CombatCog(bot))