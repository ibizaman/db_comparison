import io
import time
import threading


class StringIteratorIO(io.TextIOBase):
    # http://stackoverflow.com/a/12604375/1013628

    def __init__(self, iter):
        self._iter = iter
        self._left = ''

    def readable(self):
        return True

    def _read1(self, n=None):
        while not self._left:
            try:
                self._left = next(self._iter)
            except StopIteration:
                break
        ret = self._left[:n]
        self._left = self._left[len(ret):]
        return ret

    def read(self, n=None):
        l = []
        if n is None or n < 0:
            while True:
                m = self._read1()
                if not m:
                    break
                l.append(m)
        else:
            while n > 0:
                m = self._read1(n)
                if not m:
                    break
                n -= len(m)
                l.append(m)
        return ''.join(l)


class FunctionThread(threading.Thread):
    def __init__(self, func, interval=1):
        self.func = func
        self.interval = interval
        self._stop_flag = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        while not self._stop_flag.isSet():
            self.func()
            time.sleep(self.interval)

    def stop(self):
        self._stop_flag.set()

