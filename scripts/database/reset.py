import lib.database as db

db.delete_tables(db.conn)
db.create_tables(db.conn)