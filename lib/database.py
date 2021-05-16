import psycopg2

import lib.util

config = lib.util.config

def connect():
    conn = psycopg2.connect(host=config['database']['host'],
                            port=config['database']['port'],
                            database=config['database']['database'],
                            user=config['database']['user'],
                            password=config['database']['password'])
    return conn

conn = connect()

def delete_tables(conn):
    commands = (
        '''
        DROP TABLE guilds CASCADE;
        ''',
        '''
        DROP TABLE users CASCADE;
        ''',
        '''
        DROP TABLE monsters CASCADE; 
        ''',
        '''
        DROP TABLE chosen;
        '''
        '''
        DROP TABLE free_monsters; 
        ''',
        '''
        DROP TABLE groups CASCADE;
        ''',
        '''
        DROP TABLE groupMonsters CASCADE;
        '''
        )

    cur = conn.cursor()

    for c in commands:
        try:    
            cur.execute(c)
        except Exception as e:
            print('could not execute command', c)
            
            if not type(e) is psycopg2.errors.UndefinedTable:
                cur.close()
                raise e

    conn.commit()
    cur.close()

def create_tables(conn):
    commands = (
        '''
        CREATE TABLE guilds (
            id bigint PRIMARY KEY UNIQUE NOT NULL
        )
        ''',
        '''
        CREATE TABLE users ( 
            id SERIAL UNIQUE NOT NULL,
            user_id bigint NOT NULL,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE,
            score int,
            rolls int,
            roll_timestamp double precision,
            catches int,
            catch_timestamp double precision,
            attacks int,
            attack_timestamp double precision,
            PRIMARY KEY (user_id, guild_id)
        );
        ''',
        '''
        CREATE TABLE monsters (
            id SERIAL UNIQUE NOT NULL,
            name text,
            type text,
            level int,
            exhausted_timestamp double precision,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE,
            owner_id bigint REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (id, owner_id)
        );
        ''',
        '''
        CREATE TABLE chosen (
            id SERIAL UNIQUE NOT NULL,
            HP int,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE,
            owner_id bigint REFERENCES users(id) ON DELETE CASCADE,
            monster_id bigint REFERENCES monsters(id) ON DELETE CASCADE, 
            created_timestamp double precision,
            PRIMARY KEY (id, monster_id)
        );
        ''',
        '''
        CREATE TABLE free_monsters (
            id SERIAL,
            type text,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE,
            channel_id bigint,
            message_id bigint,
            created_timestamp double precision
        )
        ''',
        '''
        CREATE TABLE groups (
            id SERIAL UNIQUE NOT NULL,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE,
            owner_id bigint REFERENCES users(id) ON DELETE CASCADE,
            name TEXT,
            description TEXT,
            favorite BOOLEAN
        )
        ''',
        '''
        CREATE TABLE groupMonsters (
            monster_id bigint REFERENCES monsters(id) ON DELETE CASCADE,
            group_id bigint REFERENCES groups(id) ON DELETE CASCADE,
            group_index int
        )
        ''')

    cur = conn.cursor()

    for c in commands:
        try:    
            cur.execute(c)
        except Exception as e:
            print('could not execute command', c)
            raise e

    conn.commit()
    cur.close()


class Guild:

    def __init__(self, row):
        self.id = row[0]

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM guilds WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return Guild(row)

    @staticmethod
    def create(id):
        cur = conn.cursor()
        command = '''INSERT INTO guilds(id) VALUES (%s);'''
        cur.execute(command, (id,))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = ('''DELETE FROM guilds WHERE id = %s''')
        cur.execute(command, (id,))
        cur.close()


class User:

    def __init__(self, row):
        self.id, self.user_id, self.guild_id, self.score, self.rolls, self.roll_timestamp, self.catches, self.catch_timestamp, self.attacks, self.attack_timestamp = row

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return User(row)

    @staticmethod
    def get_by_member(guild_id, user_id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE user_id = %s AND guild_id = %s'''
        cur.execute(command, (user_id, guild_id))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return User(row)

    @staticmethod
    def get_by_guild(guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE guild_id = %s'''
        cur.execute(command, (guild_id,))
        rows = cur.fetchall()
        cur.close()
        return [User(row) for row in rows]

    @staticmethod
    def create(id, guild_id, timestamp):
        cur = conn.cursor()
        command = '''INSERT INTO users(user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp, attacks, attack_timestamp) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);'''
        cur.execute(command, (id, guild_id, 0,
         config['game']['rolling']['rolls'], timestamp, config['game']['rolling']['catches'], timestamp, config['game']['combat']['attacks'], timestamp))
        conn.commit()
        cur.close()

    @staticmethod
    def roll(id, guild_id, rolls, roll_timestamp):
        cur = conn.cursor()

        if roll_timestamp is not None:
            command = '''UPDATE users
                        SET rolls = %s, roll_timestamp = %s
                        WHERE user_id = %s AND guild_id = %s;'''
            cur.execute(command, (rolls, roll_timestamp, id, guild_id))

        else:
            command = '''UPDATE users
                        SET rolls = %s
                        WHERE user_id = %s AND guild_id = %s;'''
            cur.execute(command, (rolls, id, guild_id))
        
        conn.commit()
        cur.close()


    @staticmethod
    def catch(id, guild_id, catches, catch_timestamp):
        cur = conn.cursor()

        if catch_timestamp is not None:
            command = '''UPDATE users
                        SET catches = %s, catch_timestamp = %s
                        WHERE user_id = %s AND guild_id = %s;'''
            cur.execute(command, (catches, catch_timestamp, id, guild_id))

        else:
            command = '''UPDATE users
                        SET catches = %s
                        WHERE user_id = %s AND guild_id = %s;'''
            cur.execute(command, (catches, id, guild_id))
        
        conn.commit()
        cur.close()


    @staticmethod
    def attack(id, guild_id, attacks, attack_timestamp):
        cur = conn.cursor()

        if attack_timestamp is not None:
            command = '''UPDATE users
                        SET attacks = %s, attack_timestamp = %s
                        WHERE user_id = %s AND guild_id = %s;'''
            cur.execute(command, (attacks, attack_timestamp, id, guild_id))

        else:
            command = '''UPDATE users
                        SET attacks = %s
                        WHERE user_id = %s AND guild_id = %s;'''
            cur.execute(command, (attacks, id, guild_id))
        
        conn.commit()
        cur.close()


    @staticmethod
    def set_score(id, guild_id, score):
        cur = conn.cursor()
        command = '''UPDATE users
                    SET score = %s
                    WHERE user_id = %s AND guild_id = %s;'''
        cur.execute(command, (score, id, guild_id))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id, guild_id):
        cur = conn.cursor()
        command = '''DELETE FROM users WHERE user_id = %s AND guild_id = %s'''
        cur.execute(command, (id, guild_id))
        cur.close()


class Monster:

    def __init__(self, row):
        self.id, self.name, self.type, self.level, self.exhausted_timestamp, self.guild_id, self.owner_id = row

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM monsters WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return Monster(row)

    @staticmethod
    def get_by_owner(guild_id, owner_id):
        cur = conn.cursor()
        command = '''SELECT * FROM monsters WHERE guild_id = %s AND owner_id = %s'''
        cur.execute(command, (guild_id, owner_id))
        rows = cur.fetchall()
        cur.close()
        return [Monster(row) for row in rows]

    @staticmethod
    def get_by_guild(guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM monsters WHERE guild_id = %s'''
        cur.execute(command, (guild_id, ))
        rows = cur.fetchall()
        cur.close()
        return [Monster(row) for row in rows]

    @staticmethod
    def get_by_type(guild_id, type):
        cur = conn.cursor()
        command = '''SELECT * FROM monsters WHERE guild_id = %s AND type = %s'''
        cur.execute(command, (guild_id, type))
        rows = cur.fetchall()
        cur.close()
        return [Monster(row) for row in rows]

    @staticmethod
    def rename(id, name):
        cur = conn.cursor()
        command = '''UPDATE monsters
                    SET name = %s
                    WHERE id = %s;'''
        cur.execute(command, (name, id))
        conn.commit()
        cur.close()

    @staticmethod
    def change_owner(id, owner_id):
        cur = conn.cursor()
        command = '''UPDATE monsters
                    SET owner_id = %s
                    WHERE id = %s;'''
        cur.execute(command, (owner_id, id))
        conn.commit()
        cur.close()

    @staticmethod
    def exhaust(id, exhausted_timestamp):
        cur = conn.cursor()
        command = '''UPDATE monsters
                    SET exhausted_timestamp = %s
                    WHERE id = %s;'''
        cur.execute(command, (exhausted_timestamp, id))
        conn.commit()
        cur.close()

    @staticmethod
    def create(name, level, guild_id, owner_id):
        cur = conn.cursor()
        command = '''INSERT INTO monsters(name, type, level, exhausted_timestamp, guild_id, owner_id) VALUES (%s, %s, %s, %s, %s, %s);'''
        cur.execute(command, (name, name, level, 0, guild_id, owner_id))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = '''DELETE FROM monsters WHERE id = %s'''
        cur.execute(command, (id,))
        conn.commit()
        cur.close()


class Group:

    def __init__(self, row):
        self.id, self.guild_id, self.owner_id, self.name, self.description, self.favorite = row

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM groups WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return Group(row)

    @staticmethod
    def get_by_owner(guild_id, owner_id):
        cur = conn.cursor()
        command = '''SELECT * FROM groups WHERE guild_id = %s AND owner_id = %s'''
        cur.execute(command, (guild_id, owner_id))
        rows = cur.fetchall()
        cur.close()
        return [Group(row) for row in rows]

    @staticmethod
    def change_name(id, name):
        cur = conn.cursor()
        command = '''UPDATE groups
                    SET name = %s
                    WHERE id = %s;'''
        cur.execute(command, (name, id))
        conn.commit()
        cur.close()

    @staticmethod
    def change_description(id, description):
        cur = conn.cursor()
        command = '''UPDATE groups
                    SET description = %s
                    WHERE id = %s;'''
        cur.execute(command, (description, id))
        conn.commit()
        cur.close()

    @staticmethod
    def change_favorite(id, favorite):
        if favorite:
            favorite = 't'
        else:
            favorite = 'f'
        cur = conn.cursor()
        command = '''UPDATE groups
                    SET favorite = %s
                    WHERE id = %s;'''
        cur.execute(command, (favorite, id))
        conn.commit()
        cur.close()


    @staticmethod
    def create(guild_id, owner_id, name, description, favorite=True):
        if favorite:
            favorite = 't'
        else:
            favorite = 'f'

        cur = conn.cursor()
        command = '''INSERT INTO groups(guild_id, owner_id, name, description, favorite) VALUES (%s, %s, %s, %s, %s);'''
        cur.execute(command, (guild_id, owner_id, name, description, favorite))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = '''DELETE FROM groups WHERE id = %s'''
        cur.execute(command, (id,))
        cur.close()
        


class GroupMonster:

    def __init__(self, row):
        self.monster_id, self.group_id, self.group_index = row

    @staticmethod
    def get(monster_id, group_id):
        cur = conn.cursor()
        command = '''SELECT * FROM groupMonsters WHERE monster_id = %s AND group_id = %s'''
        cur.execute(command, (monster_id, group_id))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return GroupMonster(row)
        
    @staticmethod
    def get_by_monster(monster_id):
        cur = conn.cursor()
        command = '''SELECT * FROM groupMonsters WHERE monster_id = %s'''
        cur.execute(command, (monster_id,))
        rows = cur.fetchall()
        cur.close()
        return [GroupMonster(row) for row in rows]

    @staticmethod
    def get_by_group(group_id):
        cur = conn.cursor()
        command = '''SELECT * FROM groupMonsters WHERE group_id = %s'''
        cur.execute(command, (group_id,))
        rows = cur.fetchall()
        cur.close()
        return [GroupMonster(row) for row in rows]

    @staticmethod
    def create(monster_id, group_id, group_index):
        cur = conn.cursor()
        command = '''INSERT INTO groupMonsters(monster_id, group_id, group_index) VALUES (%s, %s, %s);'''
        cur.execute(command, (monster_id, group_id, group_index))
        conn.commit()
        cur.close()

    @staticmethod
    def change_index(monster_id, group_id, new_index):
        cur = conn.cursor()
        command = '''UPDATE groupMonsters
                    SET group_index = %s
                    WHERE monster_id = %s AND group_id = %s;'''
        cur.execute(command, (new_index, monster_id, group_id))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(monster_id, group_id):
        cur = conn.cursor()
        command = '''DELETE FROM groupMonsters WHERE monster_id = %s AND group_id = %s;'''
        cur.execute(command, (monster_id, group_id))
        cur.close()


class Chosen:

    def __init__(self, row):
        self.id, self.hp, self.guild_id, self.owner_id, self.monster_id, self.created_timestamp = row

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return Chosen(row)

    @staticmethod
    def get_by_monster(id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE monster_id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return Chosen(row)

    @staticmethod
    def get_by_guild(guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE guild_id = %s'''
        cur.execute(command, (guild_id,))
        rows = cur.fetchall()
        cur.close()
        return [Chosen(row) for row in rows]

    @staticmethod
    def get_by_owner(guild_id, owner_id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE guild_id = %s AND owner_id = %s'''
        cur.execute(command, (guild_id, owner_id))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return Chosen(row)

    @staticmethod
    def create(hp, guild_id, owner_id, monster_id, created_timestamp):
        cur = conn.cursor()
        command = '''INSERT INTO chosen(hp, guild_id, owner_id, monster_id, created_timestamp) VALUES (%s, %s, %s, %s, %s);'''
        cur.execute(command, (hp, guild_id, owner_id, monster_id, created_timestamp))
        conn.commit()
        cur.close()

    @staticmethod
    def damage(id, hp):
        cur = conn.cursor()
        command = '''UPDATE chosen
                    SET HP = %s
                    WHERE id = %s;'''
        cur.execute(command, (hp, id))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = '''DELETE FROM chosen WHERE id = %s'''
        cur.execute(command, (id,))
        cur.close()

    @staticmethod
    def remove_by_owner(id):
        cur = conn.cursor()
        command = '''DELETE FROM chosen WHERE owner_id = %s'''
        cur.execute(command, (id,))
        cur.close()


class FreeMonster:

    def __init__(self, row):
        self.id, self.type, self.guild_id, self.channel_id, self.message_id, self.created_timestamp = row

    @staticmethod
    def get(guild_id, channel_id, message_id):
        cur = conn.cursor()
        command = '''SELECT * FROM free_monsters WHERE (guild_id = %s AND channel_id = %s) AND message_id = %s'''
        cur.execute(command, (guild_id, channel_id, message_id))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return None
        else:
            return FreeMonster(row)

    @staticmethod
    def get_by_type(guild_id, type):
        cur = conn.cursor()
        command = '''SELECT * FROM free_monsters WHERE guild_id = %s AND type = %s'''
        cur.execute(command, (guild_id, type))
        rows = cur.fetchall()
        cur.close()
        return [FreeMonster(row) for row in rows]

    @staticmethod
    def get_expired(timestamp):
        cur = conn.cursor()
        command = '''SELECT * FROM free_monsters WHERE created_timestamp < %s'''
        cur.execute(command, (timestamp, ))
        rows = cur.fetchall()
        cur.close()
        return [FreeMonster(row) for row in rows]

    @staticmethod
    def create(typ, guild_id, channel_id, message_id, created_timestamp):
        cur = conn.cursor()
        command = '''INSERT INTO free_monsters(type, guild_id, channel_id, message_id, created_timestamp) VALUES (%s, %s, %s, %s, %s);'''
        cur.execute(command, (typ, guild_id, channel_id, message_id, created_timestamp))
        conn.commit()
        cur.close()

    @staticmethod
    def all():
        cur = conn.cursor()
        command = '''SELECT * FROM free_monsters'''
        cur.execute(command)
        rows = cur.fetchall()
        cur.close()
        return [FreeMonster(row) for row in rows]

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = '''DELETE FROM free_monsters WHERE id = %s'''
        cur.execute(command, (id,))
        cur.close()

    @staticmethod
    def remove_expired(timestamp):
        cur = conn.cursor()
        command = '''DELETE FROM free_monsters WHERE created_timestamp < %s'''
        cur.execute(command, (timestamp, ))
        cur.close()