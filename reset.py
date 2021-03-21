import lib.database


lib.database.delete_tables(lib.database.conn)
lib.database.create_tables(lib.database.conn)