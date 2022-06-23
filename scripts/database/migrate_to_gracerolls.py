import lib.database as db
import lib.util

config = lib.util.config


commands = (
    '''ALTER TABLE free_monsters ADD owner_id bigint;''',
    )

cur = db.conn.cursor()

for c in commands:
    try:    
        cur.execute(c)
    except Exception as e:
        print('could not execute command', c)
        raise e

commands = (
    '''UPDATE free_monsters SET owner_id = -1;''',
)

for c in commands:
    try:    
        cur.execute(c, (0,))
    except Exception as e:
        print('could not execute command', c)
        raise e


db.conn.commit()
cur.close()