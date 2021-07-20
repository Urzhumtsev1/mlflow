from config import DB_URI
from psycopg2 import connect
from psycopg2.extras import execute_batch
from psycopg2.sql import SQL, Identifier, Placeholder


class PgConn:

    def __init__(self):
        self.connection = connect(DB_URI)
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()

    def insert_execute_batch(self, schema, table, data):
        # if data is None: self.logger.warning(f"data is None: data: {data} table: {table}"); return
        columns = list(data[0].keys())
        with self.cursor as cursor:
            execute_batch(
                cursor,
                SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING")
                    .format(
                        Identifier(schema, table),
                        SQL(', ').join(map(Identifier, columns)), 
                        SQL(', ').join(Placeholder() * len(columns))
                    ), 
                tuple(tuple(i.values()) for i in data)
            )

    def close(self):
        self.connection.close()
