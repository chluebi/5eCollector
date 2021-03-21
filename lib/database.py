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
        DROP TABLE monsters; 
        ''',
        '''
        DROP TABLE free_monsters; 
        '''
        )

    cur = conn.cursor()

    for c in commands:
        cur.execute(c)

    conn.commit()
    cur.close()

def create_tables(conn):
    commands = (
        '''
        CREATE TABLE guilds (
            id bigint PRIMARY KEY
        )
        ''',
        '''
        CREATE TABLE users ( 
            id bigint UNIQUE NOT NULL,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE,
            level int,
            rolls int,
            timestamp_roll double precision,
            catches int,
            timestamp_catch double precision,
            PRIMARY KEY (id, guild_id)
        );
        ''',
        '''
        CREATE TABLE monsters (
            id SERIAL,
            name text,
            type text,
            guild_id bigint REFERENCES guilds(id) ON DELETE CASCADE, 
            owner_id bigint REFERENCES users(id) ON DELETE CASCADE,
            PRIMARY KEY (id, owner_id)
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
        cur.execute(c)

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
        command = '''DELETE FROM guilds WHERE id = %s'''
        cur.execute(command, (id,))
        cur.close()


class User:

    @staticmethod
    def get(id, guild_id):
        cur = conn.cursor()
        command = '''SELECT * FROM users WHERE id = %s AND guild_id = %s'''
        cur.execute(command, (id, guild_id))
        row = cur.fetchone()
        cur.close()
        return row

    @staticmethod
    def create(id, guild_id):
        cur = conn.cursor()
        command = '''INSERT INTO users(id, guild_id, level, rolls, timestamp_roll, catches, timestamp_catch) 
        VALUES (%s, %s, %s, %s, %s, %s, %s);'''
        cur.execute(command, (id, guild_id, 1,
         config['game']['rolls'], 0, config['game']['catches'], 0))
        conn.commit()
        cur.close()

    @staticmethod
    def explore(id, guild_id, rolls, timestamp_roll):
        cur = conn.cursor()

        if timestamp_roll is not None:
            command = '''UPDATE users
                        SET rolls = %s, timestamp_roll = %s
                        WHERE id = %s AND guild_id = %s;'''
            cur.execute(command, (rolls, timestamp_roll, id, guild_id))

        else:
            command = '''UPDATE users
                        SET rolls = %s
                        WHERE id = %s AND guild_id = %s;'''
            cur.execute(command, (rolls, id, guild_id))
        
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id, guild_id):
        cur = conn.cursor()
        command = '''DELETE FROM users WHERE id = %s AND guild_id = %s'''
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
    def create(name, guild_id, owner_id):
        cur = conn.cursor()
        command = '''INSERT INTO monsters(name, guild_id, owner_id) VALUES (%s, %s, %s);'''
        cur.execute(command, (name, guild_id, owner_id))
        conn.commit()
        cur.close()

    @staticmethod
    def remove(id):
        cur = conn.cursor()
        command = '''DELETE FROM monsters WHERE id = %s'''
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