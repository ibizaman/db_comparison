import psycopg2


connection_string = "dbname=postgres user=postgres"
conn = psycopg2.connect(connection_string)
cur = conn.cursor()

sql = """
DROP SCHEMA IF EXISTS db_speed_test CASCADE;
CREATE SCHEMA db_speed_test;

CREATE TABLE db_speed_test.run (
    run SERIAL PRIMARY KEY,
    database VARCHAR(50),
    action VARCHAR(50),
    duration REAL NOT NULL
);

CREATE TABLE db_speed_test.monitor (
    run INTEGER NOT NULL
        REFERENCES db_speed_test.run(run) ON DELETE RESTRICT,
    program VARCHAR(50) NOT NULL,
    monitor VARCHAR(50) NOT NULL,
    submonitor VARCHAR(50) NULL,
    time REAL NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY(run, program, monitor, submonitor, time)
);
"""
cur.execute(sql);

conn.commit();
conn.close();
