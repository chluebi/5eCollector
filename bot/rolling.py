import discord
from discord.ext import commands, tasks
import time
import asyncio

import lib.checks
import lib.database as db
import lib.embeds


config = lib.util.config


class RollCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def roll_task(ctx, delay):
        await asyncio.sleep(delay*2)
        user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)

        db.User.set_score(ctx.message.author.id, ctx.guild.id, user_db.score+1)

        monster = lib.resources.random_monster()
        embed = lib.embeds.generate_monster_embed(monster)

        embed.set_author(name=str(ctx.message.author), icon_url=ctx.message.author.avatar_url)
        embed.set_footer(text=f'🛡️ only catchable by {ctx.message.author} 🛡️')

        message = await ctx.send(embed=embed)

        id = db.FreeMonster.create(monster['name'], ctx.guild.id, ctx.author.id, ctx.message.channel.id, message.id, time.time())
        await message.add_reaction('🗨️')

        await asyncio.sleep(config['game']['rolling']['roll_grace'])

        if db.FreeMonster.get(ctx.guild_id, ctx.author.id, ctx.message.channel.id) is not None:
            embed.set_footer(text='🔓 Uncaught 🔓')
            await message.edit(embed=embed)


    @commands.command()
    @commands.check(lib.checks.guild_exists_check)
    @commands.check(lib.checks.user_exists_check)
    async def roll(self, ctx, amount=1):
        
        for r in range(int(amount)):
            user_db = db.User.get_by_member(ctx.guild.id, ctx.message.author.id)

            if user_db.rolls < 1:
                roll_countdown = (user_db.roll_timestamp + config['game']['rolling']['roll_cooldown']) - time.time()
                if roll_countdown > 0:
                    await ctx.send(f'You are out of rolls. (Resets in **{lib.time_handle.seconds_to_text(roll_countdown)}**)')
                    return
                else:
                    db.User.roll(ctx.message.author.id, ctx.guild.id, config['game']['rolling']['rolls']-1, time.time())
            else:
                if user_db.rolls == config['game']['rolling']['rolls']:
                    db.User.roll(ctx.message.author.id, ctx.guild.id, user_db.rolls-1, time.time())
                else:
                    db.User.roll(ctx.message.author.id, ctx.guild.id, user_db.rolls-1, None)

            self.bot.loop.create_task(RollCog.roll_task(ctx, r))
                

    @commands.Cog.listener()
    async def on_ready(self):
        self.remove_expired.start()


    @tasks.loop(seconds=config['game']['rolling']['expire_cooldown'])
    async def remove_expired(self):
        expired_monsters_db = db.FreeMonster.get_expired(time.time() - config['game']['rolling']['expire_cooldown'])

        for expired_monster_db in expired_monsters_db:
            monster = lib.resources.get_monster(expired_monster_db.type)
            embed = lib.embeds.generate_monster_embed(monster)
            embed.set_footer(text=f'❌ Expired ❌')

            guild = self.bot.get_guild(expired_monster_db.guild_id)
            channel = guild.get_channel(expired_monster_db.channel_id)
            if channel is None:
                continue
            message = await channel.fetch_message(expired_monster_db.message_id)

            await message.edit(embed=embed)
            await message.remove_reaction('🗨️', self.bot.user)

            db.FreeMonster.remove(expired_monster_db.id)


class CatchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        user = guild.get_member(payload.user_id)


        ctx = await self.bot.get_context(message)

        if user.bot is True:
            return
        
        if payload.emoji.name == '🗨️':
            user_db = db.User.get_by_member(ctx.guild.id, user.id)
            if user_db is None:
                return

            if user_db.catches < 1:
                catch_countdown = (user_db.catch_timestamp + config['game']['rolling']['catch_cooldown']) - time.time()
                if catch_countdown > 0:
                    await ctx.send(f'You are out of catches. (Resets in **{lib.time_handle.seconds_to_text(catch_countdown)}**)')
                    return
                else:
                    db.User.catch(user.id, ctx.guild.id, config['game']['rolling']['catches']-1, time.time())
            else:
                if user_db.catches == config['game']['rolling']['catches']:
                    db.User.catch(user.id, ctx.guild.id, user_db.catches-1, time.time())
                else:
                    db.User.catch(user.id, ctx.guild.id, user_db.catches-1, None)

            db.User.set_score(user.id, ctx.guild.id, user_db.score+10)

            free_monster_db = db.FreeMonster.get(ctx.guild.id, ctx.message.channel.id, ctx.message.id)

            if free_monster_db is None:
                return

            if user.id != free_monster_db.owner_id and time.time() < free_monster_db.created_timestamp + config['game']['rolling']['roll_grace']:
                grace = free_monster_db.created_timestamp + config['game']['rolling']['roll_grace'] - time.time()
                await ctx.message.channel.send(f'This Monster can only be caught by their roller, retry in {lib.time_handle.seconds_to_text(grace)}.')
                return

            db.FreeMonster.remove(free_monster_db.id)
            owner_id = db.User.get_by_member(ctx.guild.id, user.id).id
            db.Monster.create(free_monster_db.type, 1, ctx.guild.id, owner_id)

            monster = lib.resources.get_monster(free_monster_db.type)

            embed = lib.embeds.generate_monster_embed(monster)

            embed.set_author(name=str(user), icon_url=user.avatar_url)
            embed.set_footer(text=f'🎯 caught by {user} 🎯')
            await ctx.message.edit(embed=embed)
            await ctx.message.remove_reaction('🗨️', ctx.me)



def setup(bot):
    bot.add_cog(RollCog(bot))
    bot.add_cog(CatchCog(bot))