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

    def adjacent(self, monster):
        adj = []
        if monster not in self.alive_fighters():
            return adj

        ind = self.alive_fighters().index(monster)
        if ind != 0:
            adj.append(self.alive_fighters()[ind-1])
        if ind != len(self.alive_fighters()) - 1:
            adj.append(self.alive_fighters()[ind+1])

        return adj


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
        embed.add_field(name=f'Round {self.round}⏲️', value=value, inline=False)

        if len(self.attackers.alive_fighters()) > 0:
            attackers_visual = '\n'.join([str(f) if f.action is None else f'**{f}**' for f in self.attackers.alive_fighters() ])
        else:
            attackers_visual = '[empty]'
        embed.add_field(name=f'Attackers: {self.attackers}', value=attackers_visual)

        if len(self.defenders.alive_fighters()) > 0:
            defenders_visual = '\n'.join([str(f) if f.action is None else f'**{f}**' for f in self.defenders.alive_fighters()])
        else:
            defenders_visual = '[empty]'
        embed.add_field(name=f'Defenders: {self.defenders}', value=defenders_visual)
        
        embed.set_footer(text='In Progress 🕑')
        return embed

    async def message(self, content, force=False):
        self.history.append(content + '\n')
        embed = self.start_embed()

        if len(content) > 1000:
            for i in range(len(content) // 1000 + 1):
                embed.add_field(name='Current', value=content[i*1000:(i+1)*1000], inline=False)
        else:
            embed.add_field(name='Current', value=content, inline=False)

        display_length = max(1, 1 + len(content)/30/self.speed)

        if len(self.history) % max(1, self.speed) == 0 or force:
            await self.start_message.edit(embed=embed)
            await asyncio.sleep(display_length)

    def kill(self, attacker, target):
        target.alive = False
    
    def damage(self, attacker, target, damage):
        target.hp -= damage

        if target.hp < 1:
            self.kill(attacker, target)

    def heal(self, healer, target, healing):
        if target.hp < 1:
            return

        target.hp = min(target.hp + healing, target.max_hp)

    async def attack(self, attacker_side, target_side, attacker, target):

        attacker.action = 'attack'
        target.action = 'defend'

        modifier = (attacker.mod(self.stat), '')

        if attacker_side.has_trait('shapechanger', amount=10):
            max_stat = 0
            for monster in attacker_side.alive_fighters() + target_side.alive_fighters():
                max_stat = max(monster['stats'][self.stat])
            modifier = (max_stat, '👽')
        elif attacker_side.has_trait('shapechanger', amount=5):
            modifier = (attacker.mod(self.stat), '👽')
        
        base_attack_roll = random.randint(1, 20)
        #🎯

        critting = [20]
        crit_text = ''

        if attacker_side.has_trait('pacifist', amount=1):
            critting.append(19)
            crit_text += '🕊️'
        if attacker_side.has_trait('pacifist', amount=2):
            critting.append(18)
        if attacker_side.has_trait('pacifist', amount=3):
            critting.append(17)
        if attacker_side.has_trait('pacifist', amount=4):
            critting.append(16)

        if attacker_side.has_trait('yugoloth', amount=3):
            critting.append(1)
            crit_text += '👹'

        if base_attack_roll in critting:
            base_attack_roll = (base_attack_roll, crit_text)
            crit = True
        else:
            base_attack_roll = (base_attack_roll, '')
            crit = False

        attack_roll = base_attack_roll[0] + attacker.mod(self.stat)
        attack_text = ''

        if attacker_side.has_trait('gith', amount=9) and attacker.has_trait('gith'):
            if attacker.cr < target.cr:
                attack_roll += 20
                attack_text += '🧝🏽‍♀️'
        elif attacker_side.has_trait('gith', amount=6) and attacker.has_trait('gith'):
            if attacker.cr < target.cr:
                attack_roll += 10
                attack_text += '🧝🏽‍♀️'
        elif attacker_side.has_trait('gith', amount=3) and attacker.has_trait('gith'):
            if attacker.cr < target.cr:
                attack_roll += 5
                attack_text += '🧝🏽‍♀️'

        if attacker_side.has_trait('orc', amount=9) and attacker.has_trait('orc'):
            attack_roll += int((1 - attacker.hp/attacker.max_hp) * 20 * 3)
            attack_text += '💪'
        elif attacker_side.has_trait('orc', amount=6) and attacker.has_trait('orc'):
            attack_roll += int((1 - attacker.hp/attacker.max_hp) * 20 * 2)
            attack_text += '💪'
        elif attacker_side.has_trait('orc', amount=3) and attacker.has_trait('orc'):
            attack_roll += int((1 - attacker.hp/attacker.max_hp) * 20 * 1)
            attack_text += '💪'

        attack_roll = (attack_roll, attack_text)

        defense_roll = target.ac + 1 - self.round
        defense_text = ''

        if target_side.has_trait('construct', amount=3) and target.has_trait('construct'):
            defense_text += '⚙️'

        defense_roll = (defense_roll, defense_text)

        damage = 0

        infos = []

        if target.has_trait('acid') and target_side.has_trait('acid', amount=3):
            if target_side.has_trait('acid', amount=9):
                damage = 20
            elif target_side.has_trait('acid', amount=6):
                damage = 10
            elif target_side.has_trait('acid', amount=3):
                damage = 5

            self.damage(target, attacker, damage)
            infos.append(f'❇️ {attacker} takes **{damage}** bonus damage from attacking an acid monster ❇️')


        if target.has_trait('ooze') and target_side.has_trait('ooze', amount=3):
            if attacker.hp/attacker.max_hp < 0.2:
                target.max_hp += attacker.hp
                target.hp += attacker.hp

                for stat, amount in attacker.stats.items():
                    target.stats[stat] += amount

                infos.append(f'🧪{target} consumes {attacker}🧪')
                await self.message('\n\n'.join(infos))
                return


        if target.has_trait('elf'):
            
            if target_side.has_trait('elf', amount=9):
                dodge_chance = 0.8
            elif target_side.has_trait('elf', amount=6):
                dodge_chance = 0.6
            elif target_side.has_trait('elf', amount=3):
                dodge_chance = 0.4
            else:
                dodge_chance = 0.3

            if crit:
                infos.append(f'🎯(**{base_attack_roll[0]}**+{attack_roll[0]-base_attack_roll[0]}{attack_roll[1]}={attack_roll[0]}) {attacker} \n 🛡️ \n 🧝(Dodge Chance: {int(dodge_chance*100)}%) {target}')
                hit = True
            else:
                if random.random() > dodge_chance:
                    infos.append(f'⚔️**({base_attack_roll[0]}+{attack_roll[0]-base_attack_roll[0]}{attack_roll[1]}={attack_roll[0]})** {attacker} \n 🛡️ \n 🧝(Dodge Chance: {int(dodge_chance*100)}%) {target}')
                    hit = True
                else:
                    infos.append(f'⚔️({base_attack_roll[0]}+{attack_roll[0]-base_attack_roll[0]}{attack_roll[1]}={attack_roll[0]}) {attacker} \n 🛡️ \n 🧝**(Dodge Chance: {int(dodge_chance*100)}%)** {target}')
                    hit = False
        else:
            if crit:
                infos.append(f'🎯(**{base_attack_roll[0]}**+{attack_roll[0]-base_attack_roll[0]}{attack_roll[1]}={attack_roll[0]}) {attacker} \n 🛡️ \n 🔰({defense_roll[0]}{defense_roll[1]}) {target}')
                hit = True
            else:
                if attacker_side.has_trait('force', amount=10):
                    infos.append(f'🏋️Force bypasses armor🏋️')
                    hit = True
                elif attack_roll <= defense_roll:
                    infos.append(f'⚔️({base_attack_roll[0]}+{attack_roll[0]-base_attack_roll[0]}{attack_roll[1]}={attack_roll[0]}) {attacker} \n 🛡️ \n **🔰({defense_roll[0]}{defense_roll[1]})** {target}')
                    hit = False
                else:
                    infos.append(f'⚔️({base_attack_roll[0]}+{attack_roll[0]-base_attack_roll[0]}{attack_roll[1]}=**{attack_roll[0]}**) {attacker} \n 🛡️ \n 🔰({defense_roll[0]}{defense_roll[1]}) {target}')
                    hit = True

        if not hit:
            if target_side.has_trait('celestial', amount=3) and target.has_trait('celestial'):
                healing_percentage = 0
                if target_side.has_trait('celestial', amount=6):
                    healing_percentage = 0.2
                elif target_side.has_trait('celestial', amount=3):
                    healing_percentage = 0.1

                for monster in target_side.alive_fighters():
                    self.heal(attacker, monster, healing_percentage*monster.max_hp)
                
                infos.append(f'👼 All allies of {target} are healed for {int(healing_percentage*100)}% of their maximum hp 👼')

        await self.message('\n\n'.join(infos))

        if not hit:
            return

        infos, applied_damage = await self.attack_damage(attacker_side, target_side, attacker, target, crit)
        
        await self.message('\n\n'.join(infos))

        infos = []

        if attacker_side.has_trait('demon', amount=3) and attacker.has_trait('demon'):
            if attacker_side.has_trait('demon', amount=9):
                lifesteal = 0.5
            elif attacker_side.has_trait('demon', amount=6):
                lifesteal = 0.3
            elif attacker_side.has_trait('demon', amount=3):
                lifesteal = 0.1
            self.heal(attacker, attacker, int(applied_damage*lifesteal))
            infos.append(f'🎃 {attacker} heals {int(applied_damage*lifesteal)} from attacking 🎃')


        if attacker_side.has_trait('necrotic', amount=3) and attacker.has_trait('necrotic'):
            target.max_hp = target.hp
            infos.append(f'☠️ {target} max hp has been set to {target.max_hp} ☠️')

        if attacker_side.has_trait('psychic', amount=3) and attacker.has_trait('psychic'):
            if attacker_side.has_trait('psychic', amount=9):
                stat_reduction = 3
            elif attacker_side.has_trait('psychic', amount=6):
                stat_reduction = 2
            elif attacker_side.has_trait('psychic', amount=3):
                stat_reduction = 1

            for stat, amount in target.stats.items():
                target.stats[stat] -= stat_reduction

            infos.append(f'🔮 All stats of {target} have been reduced by {stat_reduction}')

        if attacker_side.has_trait('fire', amount=2) and attacker.has_trait('fire'):
            if attacker_side.has_trait('fire', amount=10):
                bonus_damage = 20
            elif attacker_side.has_trait('fire', amount=8):
                bonus_damage = 14
            elif attacker_side.has_trait('fire', amount=6):
                bonus_damage = 8
            elif attacker_side.has_trait('fire', amount=4):
                bonus_damage = 4
            elif attacker_side.has_trait('fire', amount=2):
                bonus_damage = 2

            bonus_targets = [target] + target_side.adjacent(target)

            for t in bonus_targets:
                self.damage(attacker, t, bonus_damage)

            bonus_targets_text = ', '.join([str(bonus_target) for bonus_target in bonus_targets])
            
            info = '🔥 Fire Bonus Damage: 🔥\n'
            for bonus_target in bonus_targets:
                info += f'**{bonus_damage}** bonus damage to {bonus_target}\n'
            infos.append(info)

        if attacker_side.has_trait('aberration', amount=3) and attacker.has_trait('aberration'):
            if attacker_side.has_trait('aberration', amount=9):
                bonus_stats = 3
            elif attacker_side.has_trait('aberration', amount=6):
                bonus_stats = 2
            elif attacker_side.has_trait('aberration', amount=3):
                bonus_stats = 1

            for a in attacker_side.alive_fighters():
                if a.has_trait('aberration'):
                    for stat, amount in a.stats.items():
                        a.stats[stat] += bonus_stats

            infos.append(f'👾 All friendly aberrations gain +{bonus_stats} in all stats 👾')


        if attacker_side.has_trait('lightning', amount=5) and attacker_side.has_trait('lightning'):
            info = '⚡ Lightning damages additional enemies: ⚡\n'

            lightning_targets = []
            for i in range(3):
                if len(target_side.alive_fighters()) < 1:
                    return
                lightning_targets.append(random.choice(target_side.alive_fighters()))

            for t in lightning_targets:
                i, d = await self.attack_damage(attacker_side, target_side, attacker, t, False)
                info += f'**{d}** to {t}' + '\n'

            infos.append(info)

        if attacker_side.has_trait('thunder', amount=3) and attacker.has_trait('thunder'):
            if attacker_side.has_trait('thunder', amount=9):
                amount = -1
            elif attacker_side.has_trait('thunder', amount=6):
                amount = 3
            elif attacker_side.has_trait('thunder', amount=3):
                amount = 2

            info = '🌩️ Thunder damages additional enemies: 🌩️\n'

            i = 1
            while i - amount != 0 and i < len(target_side.alive_fighters()):
                t = target_side.alive_fighters()[i]
                inf, d = await self.attack_damage(attacker_side, target_side, attacker, t, False)
                info += f'**{d}** to {t}' + '\n'
                i += 1

            infos.append(info)

        
        if attacker_side.has_trait('goblinoid', amount=5) and attacker.has_trait('goblinoid'):
            info = '👺 All allied goblinoids attack the target: 👺\n'

            for a in [f for f in attacker_side.alive_fighters() if f.has_trait('goblinoid')]:
                inf, d = await self.attack_damage(attacker_side, target_side, a, target, False)
                info += f'**{d}** by {a}' + '\n'

            infos.append(info)

        
        if crit:

            if attacker_side.has_trait('poison', amount=2) and attacker.has_trait('poison'):
                if attacker_side.has_trait('poison', amount=10):
                    bonus_damage = 50
                elif attacker_side.has_trait('poison', amount=8):
                    bonus_damage = 30
                elif attacker_side.has_trait('poison', amount=6):
                    bonus_damage = 20
                elif attacker_side.has_trait('poison', amount=4):
                    bonus_damage = 12
                elif attacker_side.has_trait('poison', amount=2):
                    bonus_damage = 4

                self.damage(attacker, target, bonus_damage) 
                infos.append(f'🎯💚 {target} takes **{bonus_damage}** bonus damage 💚🎯')


            if attacker_side.has_trait('cold', amount=3) and attacker.has_trait('cold'):
                if attacker_side.has_trait('cold', amount=9):
                    stat_reduction = 7
                elif attacker_side.has_trait('cold', amount=6):
                    stat_reduction = 5
                elif attacker_side.has_trait('cold', amount=3):
                    stat_reduction = 3

                bonus_targets = [target] + target_side.adjacent(target)

                info = f'🎯❄️ These creatures have their stats reduced by {stat_reduction} ❄️🎯\n'
                for t in bonus_targets:
                    for stat, amount in t.stats.items():
                        t.stats[stat] -= stat_reduction
                    info += f'{t}\n'

                infos.append(info)

            if attacker.has_trait('spellcaster'):

                info = '🎯🧙 Spellcaster damages all enemies: 🧙🎯\n'

                for t in target_side.alive_fighters():
                    inf, d = await self.attack_damage(attacker_side, target_side, attacker, t, False)
                    info += f'**{d}** to {t}' + '\n'

                infos.append(info)

        if len(infos) > 0:
            await self.message('\n\n'.join(infos))
        return
                

        
    async def attack_damage(self, attacker_side, target_side, attacker, target, crit):

        infos = []

        multipliers = [(self.round, '⏲️')]

        if crit:
            multipliers.append((2, '🎯'))

        if attacker_side.has_trait('monstrosity', amount=9) and attacker.has_trait('monstrosity'):
            multipliers.append((1.8, '🦖'))
        elif attacker_side.has_trait('monstrosity', amount=6) and attacker.has_trait('monstrosity'):
            multipliers.append((1.4, '🦖'))
        elif attacker_side.has_trait('monstrosity', amount=3) and attacker.has_trait('monstrosity'):
            multipliers.append((1.2, '🦖'))

        if attacker_side.has_trait('underwater', amount=5) and attacker.has_trait('underwater'):
            multipliers.append((0.5, '🌊'))

        target_percentage_health = target.hp/target.max_hp

        if attacker_side.has_trait('yuan-ti', amount=9) and attacker.has_trait('yuan-ti') and target_percentage_health < 0.3:
            multipliers.append((2, '🐍'))
        elif attacker_side.has_trait('yuan-ti', amount=6) and attacker.has_trait('yuan-ti') and target_percentage_health < 0.2:
            multipliers.append((2, '🐍'))
        elif attacker_side.has_trait('yuan-ti', amount=3) and attacker.has_trait('yuan-ti') and target_percentage_health < 0.1:
            multipliers.append((2, '🐍'))
        

        base_damage_roll = random.randint(1, 20)
        damage_mod = attacker.mod(self.stat)
        damage_roll = base_damage_roll + damage_mod

        full_damage = damage_roll
        full_multiplier = 1
        full_multiplier_text = ''
        for m, text in multipliers:
            full_damage *= m
            full_multiplier *= m
            full_multiplier_text += text
        full_damage = int(full_damage)
        

        reductions = []

        if target_side.has_trait('mountain', amount=5) and not target.has_trait('mountain'):
            reductions.append((0.7, '⛰️'))
        if target_side.has_trait('desert', amount=5) and target.has_trait('desert'):
            reductions.append((0.8, '🏜️'))
        if target_side.has_trait('swamp', amount=5) and target.has_trait('swamp') and target.cr < attacker.cr:
            reductions.append((0.7, '🏕️'))
        if target_side.has_trait('underwater', amount=5) and target.has_trait('underwater'):
            reductions.append((0.5, '🌊'))
        
        if target_side.has_trait('dwarf', amount=3) and target.has_trait('dwarf') and target_percentage_health < 0.2:
            if target_side.has_trait('dwarf', amount=8):
                reduction = 0.9
                reductions.append((reduction, '🧔'))
            elif target_side.has_trait('dwarf', amount=6):
                reduction = 0.7
                reductions.append((reduction, '🧔'))
            elif target_side.has_trait('dwarf', amount=3):
                reduction = 0.5
                reductions.append((reduction, '🧔'))

        applied_damage = full_damage
        full_reduction = 1
        full_reduction_text = ''
        for r, text in reductions:
            applied_damage /= r
            full_reduction *= r
            full_reduction_text += text
        applied_damage = int(applied_damage)

        self.damage(attacker, target, applied_damage)

        applied_multiplier = full_multiplier/full_reduction
        full_multiplier = round(full_multiplier*100)/100
        full_reduction = round(full_reduction*100)/100

        damage_info = f'**{full_damage}**{full_multiplier_text} damage from{attacker}'

        if applied_damage != full_damage:
            damage_info += f'\n**{applied_damage}**{full_reduction_text} damage taken by {target}'
        else:
            damage_info += f'\n to {target}'
        infos.append(damage_info)


        return infos, applied_damage

    
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
                        fighter.hp = int(fighter.hp * (1 + 2))
                        fighter.max_hp = fighter.hp
                trait_messages[side.name].append(trait_message('giant', effect=2))
            elif side.has_trait('giant', amount=6):
                for fighter in side.fighters:
                    if fighter.has_trait('giant'):
                        fighter.hp = int(fighter.hp * (1 + 1))
                        fighter.max_hp = fighter.hp
                trait_messages[side.name].append(trait_message('giant', effect=1))
            elif side.has_trait('giant', amount=3):
                for fighter in side.fighters:
                    if fighter.has_trait('giant'):
                        fighter.hp = int(fighter.hp * (1 + 0.5))
                        fighter.max_hp = fighter.hp
                trait_messages[side.name].append(trait_message('giant', effect=0))

        msg = ''
        for side_name, trait_msg in trait_messages.items():
            msg += f'**{side_name}**\n'
            for m in trait_msg:
                msg += m
                msg += '\n\n'
            msg += '\n\n'

        await self.message(msg, force=True)
        await asyncio.sleep(10/self.speed)

        while True:
            self.round += 1
            await self.message(f'--- Round {self.round} ---')

            sides = [self.defenders, self.attackers]

            for side_index, side in enumerate(sides):

                def flip(num):
                    return 1 - num

                for attacker in side.alive_fighters():

                    if len(sides[flip(side_index)].alive_fighters()) < 1:
                        break

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

                    targets = []
                    if attacker.has_trait('crusher'):
                        targets.append(sides[flip(side_index)].alive_fighters()[0])
                    elif attacker.has_trait('piercer'):
                        targets.append(sides[flip(side_index)].alive_fighters()[-1])
                    elif attacker.has_trait('slasher'):
                        for i in range(2):
                            targets.append(random.choice(sides[flip(side_index)].alive_fighters()))

                    for target in targets:
                        await self.attack(side, sides[flip(side_index)], attacker, target)
                        target.action = None

                    attacker.action = None
                    

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
    async def ex_attack(self, ctx, target, group_id, stat, speed=1):

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

        battle = Battle(ctx, stat, defenders, attackers, user_db, target_db, speed=speed)


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