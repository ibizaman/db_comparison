"""
Test performance of postgres databases
"""
import psycopg2
import random
from contextlib import contextmanager
from datetime import datetime, timedelta

from monitor import MonitorAction
from util import StringIteratorIO


class Postgres(MonitorAction):
    connection_string = "dbname=postgres user=postgres"
    symbols = ['one', 'two', 'three']
    table = 'ttptest.tick'

    def __init__(self):
        self.conn = psycopg2.connect(self.connection_string)

    def __del__(self):
        self.conn.commit();
        self.conn.close();

    def _pids_to_monitor(self):
        cur = self.conn.cursor()
        cur.execute("SELECT pg_backend_pid()")
        pid = cur.fetchone()[0]
        return [(pid, 'postgres')]

    def create_table(self, with_indexes:bool=True):
        """Create table used to insert and select"""
        cur = self.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS {table}".format(table=self.table))
        cur.execute("""
                    CREATE TABLE {table} (
                        datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        symbol VARCHAR(50),
                        bid NUMERIC(10, 2),
                        ask NUMERIC(10, 2)
                    );
                    """.format(table=self.table))
        if with_indexes:
            cur.execute("""
                        CREATE INDEX ON {table} (datetime);
                        CREATE INDEX ON {table} (symbol);
                        CREATE INDEX ON {table} (bid);
                        CREATE INDEX ON {table} (ask);
                        """.format(table=self.table))

    def insert_batch(self, num_rows:int):
        """Insert num_rows in table"""
        cur = self.conn.cursor()
        cur.copy_from(StringIteratorIO(self._insert_iterator(num_rows)),
                      table=self.table,
                      columns=['symbol', 'bid', 'ask', 'datetime'],
                      sep=',')

    def select(self):
        """Select in various ways from the tables"""
        cur = self.conn.cursor()
        cur.execute("SELECT bid FROM {table} WHERE symbol=one")
        cur.fetchall()

    def _insert_iterator(self, num_rows):
        now = datetime(2016, 1, 1)
        for _ in range(0, int(num_rows)):
            symbol = random.choice(self.symbols)
            bid = random.uniform(0, 1000)
            ask = random.uniform(0, 1000)
            yield '%s,%s,%s,%s\n' % (symbol, bid, ask, now)
            now += timedelta(seconds=1)

    @contextmanager
    def _cursor(self):
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn.cursor()
        except:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()

