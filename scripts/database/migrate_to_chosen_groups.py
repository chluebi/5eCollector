import lib.database as db
import lib.util

config = lib.util.config


commands = (
    '''DELETE FROM chosen;''',
    '''ALTER TABLE chosen DROP COLUMN HP;''',
    '''ALTER TABLE chosen RENAME COLUMN monster_id TO group_id;'''
    )

cur = db.conn.cursor()

for c in commands:
    try:    
        cur.execute(c)
    except Exception as e:
        print('could not execute command', c)
        raise e

db.conn.commit()
cur.close()