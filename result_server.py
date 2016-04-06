"""
Shows results interactively
"""
import os
import psycopg2
import psycopg2.extras
import json
from datetime import datetime
from contextlib import contextmanager
from flask import Flask, request, render_template
from collections import OrderedDict, defaultdict


template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_folder)

connection_string = "dbname=postgres user=postgres"


@contextmanager
def db(as_dict=None):
    conn = psycopg2.connect(connection_string)
    if not as_dict:
        cur = conn.cursor()
    else:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        yield cur
    except:
        conn.rollback()
        raise
    else:
        conn.commit()
    finally:
        conn.close()


@app.route('/')
def run_selection():
    runs = _get_all_runs_info(request.args.get('index', 0), request.args.get('count', 30))
    return render_template('run_selection.html', columns=(runs[0].keys() if runs else None), runs=runs)


RUN_MONITORS_QUERY = """
SELECT
    program AS group,
    monitor AS subgroup
FROM db_speed_test.monitor
WHERE run=%(run)s
GROUP BY program, monitor
ORDER BY program, monitor
"""
@app.route('/run/<run>')
def run(run):
    with db(as_dict=True) as cur:
        cur.execute(RUN_MONITORS_QUERY, {'run': run})
        return render_template('run.html', graphs=cur.fetchall(), run=run)


@app.route('/run_json/<run>')
def run_json(run):
    with db(as_dict=True) as cur:
        cur.execute("SELECT database, action, duration FROM db_speed_test.run WHERE run=%(run)s",
                    {'run': run})
        return json.dumps(dict(cur.fetchone()))


MONITORS_JSON_QUERY = """
SELECT
    program,
    monitor,
    (CASE WHEN submonitor = 'NULL' THEN monitor ELSE submonitor END) AS submonitor,
    time,
    value
FROM db_speed_test.monitor
WHERE run=%(run)s
ORDER BY program, monitor, submonitor, time
"""

@app.route('/monitors_json/<run>')
def monitors_json(run):
    x = []
    with db(as_dict=True) as cur:
        cur.execute(MONITORS_JSON_QUERY, {'run': run})
        x = cur.fetchall()

    timeseries = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    current = (None, None)
    submonitor_timeseries = []
    for (program, monitor, submonitor, time, value) in x:
        if current != (program, monitor):
            timeseries[program][monitor] = _merge_submonitors(submonitor_timeseries)
            current = (program, monitor)
            submonitor_timeseries = []
        submonitor_timeseries.append((submonitor, time, value))

    return json.dumps(timeseries)


def start(port):
    app.run(host='0.0.0.0', port=port, debug=True)


GET_ALL_RUNS_INFO_QUERY = """
SELECT
    run,
    database,
    action,
    duration
FROM db_speed_test.run
LIMIT %(to)s
OFFSET %(from)s
"""
def _get_all_runs_info(index, count):
    with db(as_dict=True) as cur:
        cur.execute(GET_ALL_RUNS_INFO_QUERY, {'from': index, 'to': count})
        return _ordered_columns(cur, ['run', 'database', 'action', 'duration'])


def _merge_submonitors(submonitors):
    timeseries = defaultdict(list)
    columns = set()
    for (submonitor, time, value) in submonitors:
        timeseries[time].append((submonitor, value))
        columns.add(submonitor)
    columns = sorted(list(columns))

    return {
        'labels': ['time'] + columns,
        'data': _timeseries_to_table(columns, timeseries),
    }


def _timeseries_to_table(columns, timeseries):
    table = []
    for t in sorted(timeseries):
        current_row = [t] + [None for _ in range(len(columns))]
        for label, value in timeseries[t]:
            current_row[columns.index(label) + 1] = value
        table.append(current_row)
    return table


def _ordered_columns(rows, order):
    return [OrderedDict([(c, row[c]) for c in order]) for row in rows]

