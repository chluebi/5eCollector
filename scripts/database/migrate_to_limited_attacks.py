import lib.database as db
import lib.util

config = lib.util.config


commands = (
    '''
    ALTER TABLE users ADD attacks int;
    ''',
    '''
    ALTER TABLE users ADD attack_timestamp double precision;
    ''',
    )

cur = db.conn.cursor()

for c in commands:
    try:    
        cur.execute(c)
    except Exception as e:
        print('could not execute command', c)
        raise e


command = '''SELECT * FROM guilds'''
cur.execute(command)
rows = cur.fetchall()

guilds_ids = [row[0] for row in rows]

for guild_id in guilds_ids:
    command = '''UPDATE users
                SET attacks = %s, attack_timestamp = %s
                WHERE guild_id = %s;
                '''
    cur.execute(command, (config['game']['combat']['attacks'], config['game']['combat']['attack_cooldown'], guild_id))


db.conn.commit()
cur.close()