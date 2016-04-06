import inspect
import os
import psutil
import psycopg2
import sys
import time
from contextlib import contextmanager
from collections import defaultdict
from datetime import datetime
import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from util import FunctionThread


class MonitorAction:
    @classmethod
    def do(cls, action, **kwargs):
        obj = cls()
        with monitor(cls.__name__.lower(), action, obj._pids_to_monitor()):
            getattr(obj, action)(**kwargs)

    def _pids_to_monitor(self):
        return None

    @classmethod
    def add_subparser(cls, parser):
        subparsers = parser.add_subparsers()
        for subaction, doc in cls.subactions():
            subaction_parser = subparsers.add_parser(subaction, help=doc, description=doc)
            cls.add_action_parameters(subaction_parser, subaction)
            subaction_parser.set_defaults(func=cls.do, action=subaction)

    @classmethod
    def subactions(cls):
        return [(name, getattr(cls, name).__doc__) for name in dir(cls)
                if inspect.isfunction(getattr(cls, name)) and not name.startswith('_') and name not in cls._base_functions()]

    @staticmethod
    def _base_functions():
        return [name for name, _ in inspect.getmembers(MonitorAction, predicate=inspect.ismethod)]

    @classmethod
    def add_action_parameters(cls, parser, action):
        sig = inspect.signature(getattr(cls, action))
        for name, param in ((name, param) for name, param in sig.parameters.items() if name not in ['self']):
            type = param.annotation if param.annotation == inspect.Parameter.empty else str
            required = param.default == inspect.Parameter.empty
            parser.add_argument('--%s' % name, required=required, type=type)


@contextmanager
def monitor(db_name, action_name, other_pids=None):
    start = time.time()

    pool = []
    outputs = defaultdict(lambda: defaultdict(list))
    for pid, name in [(None, 'os'), (os.getpid(), 'python')] + (other_pids or []):
        pool += [monitor_writer_thread(f, outputs[name][f.__name__]) for f in monitoring_functions(pid)]

    for thread in pool:
        thread.start()

    yield
    end = time.time()

    for thread in pool:
        thread.stop()

    for thread in pool:
        thread.join()

    #plot_output_pdf(outputs, 'result.pdf')
    duration = end-start
    save_output(outputs, db_name, action_name, duration, start)
    print("%s took %0.3f seconds\n" % (db_name, duration))


def monitoring_functions(pid=None):
    if not pid:
        return [
            psutil.virtual_memory,
            psutil.disk_io_counters,
        ]
    else:
        p = psutil.Process(pid)
        return [
            p.memory_percent,
            p.memory_full_info,
            p.io_counters,
        ]


def monitor_writer_thread(func, out, interval=1):
    func2 = lambda: out.append((time.time(), func()))
    return FunctionThread(func2, interval)


def plot_output(outputs, post_func=None):
    for fig, (program, monitor) in enumerate((program, monitor) for program in outputs for monitor in outputs[program]):
        plt.figure(fig)
        plt.title('%s - %s' % (program, monitor))
        output = outputs[program][monitor]
        if not hasattr(output[0][1], '_fields'):
            plt.plot([x[0] for x in output], [x[1] for x in output])
        else:
            for submonitor in output[0][1]._fields:
                plt.plot([x[0] for x in output], [getattr(x[1], submonitor) for x in output], label=submonitor)
                plt.legend()
        if post_func:
            post_func()


def plot_output_pdf(outputs, file_name):
    with PdfPages(file_name) as pdf:
        plot_output(outputs, post_func=pdf.savefig)


def save_output(outputs, db_name, action_name, duration, start_time):
    connection_string = "dbname=postgres user=postgres"
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    sql = """
    INSERT INTO db_speed_test.run (database, action, duration)
        VALUES (
            %(database)s, %(action)s, %(duration)s
        ) RETURNING run;
    """
    data = {
        'database': db_name,
        'action': action_name,
        'duration': duration
    }
    cur.execute(sql, data)
    run = cur.fetchone()[0]

    for program, monitor in ((program, monitor) for program in outputs for monitor in outputs[program]):
        table = monitor
        output = outputs[program][monitor]
        if not hasattr(output[0][1], '_fields'):
            submonitors = [None]
        else:
            submonitors = output[0][1]._fields

        for submonitor in submonitors:
            values = [str_join(',',
                               run,
                               program,
                               monitor,
                               submonitor or 'NULL',
                               x[0]-start_time,
                               (x[1] if not submonitor else getattr(x[1], submonitor)))
                      for x in output]
            sql = """
            INSERT INTO db_speed_test.monitor (
                run, program, monitor, submonitor, time, value
            )
            VALUES {values};
            """.format(values=','.join('(%s)' % v for v in values))
            cur.execute(sql)

    conn.commit()
    conn.close()


def str_join(on, *args):
    return on.join(str(arg) if isinstance(arg, (int, float)) else ("'%s'" % str(arg)) for arg in args)

