import discord
from discord.ext import commands
import asyncio
import time

import lib.checks
import lib.database as db
import lib.embeds
import lib.util

class StatsCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def stats(self, ctx, category, start=1, l=10, order='+'):

        ranking = []
        ranking_title = ''

        if category in ['points']:

            ranking_title = '**Ranking by Points**'
            rows = db.User.get_by_guild(ctx.guild.id)
            
            for user_db in rows:
                #user_db_id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = row
                user = ctx.guild.get_member(user_db.user_id)
                if user is not None:
                    ranking.append((user_db.score, f'{user} ({user_db.score})'))

        elif category in ['glory', 'chosen']:
            ranking_title = '**Ranking by Glory**'
            chosens_db = db.Chosen.get_by_guild(ctx.guild.id)

            for chosen_db in chosens_db:
                user = ctx.guild.get_member(db.User.get(chosen_db.owner_id).user_id)

                group_db = db.Group.get(chosen_db.group_id)

                text = f'#{group_db.id} **{group_db.name}**'

                glory = lib.util.get_glory(chosen_db.created_timestamp)

                text += f' **[Glory: {glory}]**'
                text = f'{user}\'s ' + text

                ranking.append((glory, text))

        elif category in ['monster', 'monsters']:
            ranking_title = '**Ranking by Monsters**'
            rows = db.User.get_by_guild(ctx.guild.id)

            for user_db in rows:
                #user_db_id, user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp = row
                monster_rows = db.Monster.get_by_owner(user_db.guild_id, user_db.id)
                user = ctx.guild.get_member(user_db.user_id)
                ranking.append((len(monster_rows), f'{user} ({len(monster_rows)})'))

        elif category in ['level', 'hp', 'ac', 'cr', 'str', 'dex', 'con', 'int', 'wis', 'cha']:
            ranking_title = f'**Ranking by {category.capitalize()}**'
            monsters = db.Monster.get_by_guild(ctx.guild.id)

            if category in ['level']:
                for monster_db in monsters:
    
                    user_db = db.User.get(monster_db.owner_id)
                    user = lib.getters.get_user_by_id(user_db.user_id, ctx.guild.members)

                    text = lib.embeds.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp)
                    
                    text += f' **[Level: {monster_db.level}]**'
                    text = f'{user}\'s ' + text

                    ranking.append((monster_db.level, text))
            else:
                
                for monster_db in monsters:
                    monster = lib.resources.get_monster(monster_db.type)

                    user_db = db.User.get(monster_db.owner_id)
                    user = lib.getters.get_user_by_id(user_db.user_id, ctx.guild.members)

                    text = lib.embeds.monster_full_title(monster_db.id, monster_db.name, monster_db.type, monster_db.level, monster_db.exhausted_timestamp)
                    
                    if category in ['hp']:
                        stat = lib.util.get_hp(monster['hp'], monster_db.level)
                    elif category in ['ac']:
                        stat = lib.util.get_ac(monster['ac'], monster_db.level)
                    elif category in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                        stat = lib.util.get_stat(monster, category, monster_db.level)
                    elif category in ['cr']:
                        stat = monster[category] if monster[category] < 1 else int(monster[category])

                    text += f' **[{category.capitalize()}: {stat}]**'
                    text = f'{user}\'s ' + text

                    ranking.append((stat, text))
        else:
            return

        ranking = sorted(ranking, key=lambda x: x[0], reverse=True)
        leaderboard = list(enumerate(ranking, 1))

        l = min(l, 100)
        start = start - 1
        total = len(leaderboard)
        end = min(l, len(leaderboard[::-1][start:]))

        end = start + end
        
        if order in ['-']:
            leaderboard = leaderboard[::-1]

        leaderboard = leaderboard[start:end]
        if order in ['-']:
            end, start = start+1, end-1
        
        ranking_subtitle = f'From #{leaderboard[0][0]} to #{leaderboard[-1][0]} [Total: {total}]'

        message = ['']

        for i, (_, rank) in leaderboard:
            if len(message[-1]) + len(rank) > 1800:
                message.append(f'**#{i}** ' + rank + '\n')
            else:
                message[-1] += f'**#{i}** ' + rank + '\n'


        message = [f'{m}' for m in message]


        message[0] =  f'{ranking_title}\n' + f'{ranking_subtitle}\n' + message[0]

        for m in message:
            await ctx.message.channel.send(m)

def setup(bot):
    bot.add_cog(StatsCog(bot))