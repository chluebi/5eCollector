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
            message_id bigint
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

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM guilds WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return row

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

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_by_member(guild_id, user_id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE user_id = %s AND guild_id = %s'''
        cur.execute(command, (user_id, guild_id))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_by_guild(guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE guild_id = %s'''
        cur.execute(command, (guild_id,))
        row = cur.fetchall()
        cur.close()
        return row

    @staticmethod
    def create(id, guild_id, timestamp):
        cur = conn.cursor()
        command = '''INSERT INTO users(user_id, guild_id, score, rolls, roll_timestamp, catches, catch_timestamp) 
        VALUES (%s, %s, %s, %s, %s, %s, %s);'''
        cur.execute(command, (id, guild_id, 0,
         config['game']['rolls'], timestamp, config['game']['catches'], timestamp))
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
    def score(id, guild_id, score):
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

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM monsters WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_by_owner(guild_id, owner_id):
        cur = conn.cursor()
        command = '''SELECT * FROM monsters WHERE guild_id = %s AND owner_id = %s'''
        cur.execute(command, (guild_id, owner_id))
        rows = cur.fetchall()
        cur.close()
        return rows

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
        cur.close()


class Chosen:

    @staticmethod
    def get(id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_by_monster(id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE monster_id = %s'''
        cur.execute(command, (id,))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def get_by_guild(guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE guild_id = %s'''
        cur.execute(command, (guild_id,))
        row = cur.fetchall()
        cur.close()
        return row

    @staticmethod
    def get_by_owner(guild_id, owner_id):
        cur = conn.cursor()
        command = '''SELECT * FROM chosen WHERE guild_id = %s AND owner_id = %s'''
        cur.execute(command, (guild_id, owner_id))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def create(hp, guild_id, owner_id, monster_id, created_timestamp):
        cur = conn.cursor()
        command = '''INSERT INTO chosen(hp, guild_id, owner_id, monster_id, created_timestamp) VALUES (%s, %s, %s, %s, %s);'''
        cur.execute(command, (hp, guild_id, owner_id, monster_id, created_timestamp))
        conn.commit()
        cur.close()

    @staticmethod
    def damage(hp, id):
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

    @staticmethod
    def get(guild_id, channel_id, message_id):
        cur = conn.cursor()
        command = '''SELECT * FROM free_monsters WHERE (guild_id = %s AND channel_id = %s) AND message_id = %s'''
        cur.execute(command, (guild_id, channel_id, message_id))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def create(typ, guild_id, channel_id, message_id):
        cur = conn.cursor()
        command = '''INSERT INTO free_monsters(type, guild_id, channel_id, message_id) VALUES (%s, %s, %s, %s);'''
        cur.execute(command, (typ, guild_id, channel_id, message_id))
        conn.commit()
        cur.close()

    @staticmethod
    def all():
        cur = conn.cursor()
        command = '''SELECT * FROM free_monsters'''
        cur.execute(command)
        row = cur.fetchall()
        cur.close()
        return row

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = '''DELETE FROM free_monsters WHERE id = %s'''
        cur.execute(command, (id,))
        cur.close()