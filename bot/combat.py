from re import S
import discord
from discord.ext import commands
import asyncio
import time
import random

import lib.checks
import lib.database as db
import lib.embeds
import lib.util
import lib.traits

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
    
    def __init__(self, monster_db, group):
        self.group = group

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

        self.image = self.monster['image']

    def has_trait(self, trait):
        return trait in self.monster['traits']

    def mod(self, stat):
        return (self.stats[stat] - 10) // 2

    def __str__(self):
        s = ''
        if self.action == 'attack':
            s += '⚔️ '
        if self.action == 'defend':
            s += '🛡️ '

        s += f'#{self.id} {self.name} [{self.hp}/{self.max_hp}]'

        for trait in self.monster['traits']:
            if trait in self.group.displayed_traits:
                s += self.group.displayed_traits[trait]

        if not self.alive:
            s = f'~~{s}~~'

        return s


class Group:

    def __init__(self, id, name, monsters_db):
        self.id = id
        self.name = name
        self.displayed_traits = []
        self.fighters = [Fighter(monster_db, self) for monster_db in monsters_db]
        self.traits = self.determine_traits()
        self.displayed_traits = self.determine_displayed_traits()

    def determine_traits(self):
        traits = {}
        used_types = []
        for fighter in self.fighters:
            monster = fighter.monster
            monster_name = monster['name']
            if monster_name in used_types:
                continue
            else:
                used_types.append(monster_name)

            for trait in monster['traits']:
                if trait in traits:
                    traits[trait] += 1
                else:
                    traits[trait] = 1
        return traits

    def determine_displayed_traits(self):
        displayed_traits = {}
        for trait_name, amount in self.traits.items():
            trait = lib.traits.traits[trait_name]

            if len(trait['effects']) < 1:
                displayed_traits[trait_name] = trait['emoji']
            elif trait['effects'][0]['amount'] <= amount:
                displayed_traits[trait_name] = trait['emoji']
        return displayed_traits


    def has_trait(self, trait_name, amount=0):
        if trait_name not in self.traits:
            return False

        if self.traits[trait_name] >= amount:
            return True
        else:
            return False


    def __str__(self):
        return f'#{self.id} {self.name}'

    def alive(self):
        return True in [f.alive for f in self.fighters]

    def alive_fighters(self):
        return [f for f in self.fighters if f.alive]

    def next_alive(self):
        for fighter in self.fighters[::-1]:
            if fighter.alive:
                return fighter
        return None


class Battle:
    
    def __init__(self, ctx, stat, defenders, attackers, def_user_db, att_user_db, speed=1):
        self.round = 0
        self.history = []
        self.speed = speed

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

        if len(self.attackers.alive_fighters()) > 0:
            attackers_visual = '\n'.join([str(f) for f in self.attackers.alive_fighters()])
        else:
            attackers_visual = '[empty]'
        embed.add_field(name=f'Attackers: {self.attackers}', value=attackers_visual)

        if len(self.defenders.alive_fighters()) > 0:
            defenders_visual = '\n'.join([str(f) for f in self.defenders.alive_fighters()])
        else:
            defenders_visual = '[empty]'
        embed.add_field(name=f'Defenders: {self.defenders}', value=defenders_visual)
        
        embed.set_footer(text='In Progress 🕑')
        return embed

    async def message(self, content, force=False):
        self.history.append(content)
        embed = self.start_embed()
        embed.add_field(name='Current', value=content, inline=False)

        if len(self.history) % max(1, self.speed) == 0 or force:
            await self.start_message.edit(embed=embed)
            if self.round < 10:
                await asyncio.sleep(max(1, 1/self.speed)*2)
            else:
                await asyncio.sleep(max(1, 1/self.speed))

    def kill(self, attacker, target):
        target.alive = False
    
    def damage(self, attacker, target, damage):
        target.hp -= damage

        if target.hp < 1:
            self.kill(attacker, target)

    def attack(self, attacker, target):

        attacker.action = 'attack'
        target.action = 'defend'
        
        base_attack_roll = random.randint(1, 20)
        attack_roll = base_attack_roll + attacker.mod(self.stat)
        defense_roll = target.ac + 1 - self.round

        damage = 0

        info = ''

        if attack_roll <= defense_roll:
            info = f'(⚔️{base_attack_roll}+{attacker.mod(self.stat)}) {attacker} \n 🛡️ \n **(🔰{defense_roll})** {target} '
            return info

        base_damage_roll = random.randint(1, 20) * self.round
        damage_mod = attacker.mod(self.stat) * self.round
        damage_roll = base_damage_roll + damage_mod

        info = f'**(⚔️{base_attack_roll}+{attacker.mod(self.stat)})** {attacker}  \n 🗡️ \n (🔰{defense_roll}) {target} \n Damage: **(⚔️{base_damage_roll}+{damage_mod})**'
        
        self.damage(attacker, target, damage_roll)
        return info

    
    async def run(self):
        embed = self.start_embed()

        self.start_message = await self.ctx.message.channel.send(embed=embed)

        trait_messages = {
            self.attackers.name: [],
            self.defenders.name: []
            }

        def trait_message(trait, effect=None):
            trait_data = lib.traits.traits[trait]
            message = trait_data['name'] + ' ' + trait_data['emoji'] + '\n'
            message += trait_data['description'] + '\n'
            if effect is not None:
                message += str(trait_data['effects'][effect]['amount']) + ' ' + trait_data['emoji'] + ': '
                message += trait_data['effects'][effect]['text']
            return message

        for side in [self.attackers, self.defenders]:
            if side.has_trait('hill', amount=5):
                for fighter in side.fighters:
                    if fighter.has_trait('hill'):
                        fighter.max_hp = fighter.max_hp * (1 + 0.05 * fighter.cr)
                        fighter.hp = fighter.hp * (1 + 0.05 * fighter.cr)
                trait_messages[side.name].append(trait_message('hill', effect=0))

            if side.has_trait('beast', amount=9):
                for fighter in side.fighters:
                    if fighter.has_trait('beast'):
                        for stat, amount in fighter.stats.items():
                            fighter.stats[stat] += 8
                trait_messages[side.name].append(trait_message('beast', effect=2))
            elif side.has_trait('beast', amount=6):
                for fighter in side.fighters:
                    if fighter.has_trait('beast'):
                        for stat, amount in fighter.stats.items():
                            fighter.stats[stat] += 5
                trait_messages[side.name].append(trait_message('beast', effect=1))
            elif side.has_trait('beast', amount=3):
                for fighter in side.fighters:
                    if fighter.has_trait('beast'):
                        for stat, amount in fighter.stats.items():
                            fighter.stats[stat] += 3
                trait_messages[side.name].append(trait_message('beast', effect=0))

            if side.has_trait('dragon', amount=9):
                strongest = sorted([f for f in side.fighters if f.has_trait('dragon')], key=lambda x: x.cr, reverse=True)[0]
                for stat, amount in strongest.stats.items():
                    strongest.stats[stat] += 20 + 10
                for fighter in side.fighters:
                    if fighter.has_trait('dragon'):
                        for stat, amount in fighter.stats.items():
                            fighter.stats[stat] -= 10
                trait_messages[side.name].append(trait_message('dragon', effect=2))
            elif side.has_trait('dragon', amount=6):
                strongest = sorted([f for f in side.fighters if f.has_trait('dragon')], key=lambda x: x.cr, reverse=True)[0]
                for stat, amount in strongest.stats.items():
                    strongest.stats[stat] += 10 + 5
                for fighter in side.fighters:
                    if fighter.has_trait('dragon'):
                        for stat, amount in fighter.stats.items():
                            fighter.stats[stat] -= 5
                trait_messages[side.name].append(trait_message('dragon', effect=1))
            elif side.has_trait('dragon', amount=3):
                strongest = sorted([f for f in side.fighters if f.has_trait('dragon')], key=lambda x: x.cr, reverse=True)[0]
                for stat, amount in strongest.stats.items():
                    strongest.stats[stat] += 5 + 2
                for fighter in side.fighters:
                    if fighter.has_trait('dragon'):
                        for stat, amount in fighter.stats.items():
                            fighter.stats[stat] -= 2
                trait_messages[side.name].append(trait_message('dragon', effect=0))

            if side.has_trait('arctic', amount=5):
                for s in [self.attackers, self.defenders]:
                    for fighter in s.fighters:
                        if not fighter.has_trait('arctic'):
                            for stat, amount in fighter.stats.items():
                                fighter.stats[stat] -= 5
                trait_messages[side.name].append(trait_message('arctic', effect=0))

            if side.has_trait('construct', amount=9):
                for fighter in side.fighters:
                    if fighter.has_trait('construct'):
                        fighter.ac += 7
                trait_messages[side.name].append(trait_message('construct', effect=2))
            elif side.has_trait('construct', amount=6):
                for fighter in side.fighters:
                    if fighter.has_trait('construct'):
                        fighter.ac += 4
                trait_messages[side.name].append(trait_message('construct', effect=1))
            elif side.has_trait('construct', amount=3):
                for fighter in side.fighters:
                    if fighter.has_trait('construct'):
                        fighter.ac += 2
                trait_messages[side.name].append(trait_message('construct', effect=0))

            if side.has_trait('giant', amount=9):
                for fighter in side.fighters:
                    if fighter.has_trait('giant'):
                        fighter.hp = fighter.hp * (1 + 2)
                trait_messages[side.name].append(trait_message('giant', effect=2))
            elif side.has_trait('giant', amount=6):
                for fighter in side.fighters:
                    if fighter.has_trait('giant'):
                        fighter.hp = fighter.hp * (1 + 1)
                trait_messages[side.name].append(trait_message('giant', effect=1))
            elif side.has_trait('giant', amount=3):
                for fighter in side.fighters:
                    if fighter.has_trait('giant'):
                        fighter.hp = fighter.hp * (1 + 0.5)
                trait_messages[side.name].append(trait_message('giant', effect=0))

        msg = ''
        for side_name, trait_msg in trait_messages.items():
            msg += f'**{side_name}**\n'
            for m in trait_msg:
                msg += m
                msg += '\n\n'
            msg += '\n\n'

        await self.message(msg, force=True)
        await asyncio.sleep(10)

        while True:
            self.round += 1
            await self.message(f'--- Round {self.round} ---')

            sides = [self.defenders, self.attackers]

            for side_index, side in enumerate(sides):

                def flip(num):
                    return 1 - num

                for attacker in side.alive_fighters():

                    if not attacker.alive:
                        continue

                    if side.has_trait('underdark', amount=5):
                        if attacker.has_trait('underdark'):
                            if not side.alive_fighters().index(attacker)+1 >= len(side.alive_fighters()):
                                target = side.alive_fighters()[side.alive_fighters().index(attacker)+1]
                                if attacker.hp > target.hp:
                                    attacker.max_hp += target.max_hp
                                    attacker.hp += target.max_hp
                                    for stat, value in target.stats.items():
                                        attacker.stats[stat] += value
                                    self.kill(attacker, target)
                                    emoji = lib.traits.traits['underdark']['emoji']
                                    await self.message(f'{emoji} {attacker} consumes {target} {emoji}')

                    target = sides[flip(side_index)].next_alive()
                    if target is None:
                        break

                    info = self.attack(attacker, target)
                    if len(info) > 1:
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