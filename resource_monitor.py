import threading
import psutil
import os
import time

class ResourceMonitor(threading.Thread):
    def __init__(self, interval=0.1):
        super().__init__()
        self.stop_flag = False
        self.interval = interval
        self.timestamps = []
        self.cpu_usage = []
        self.ram_usage = []
        self.start_t = 0

    def run(self):
        self.start_t = time.time()
        process = psutil.Process(os.getpid())
        while not self.stop_flag:
            self.timestamps.append(time.time() - self.start_t)
            # cpu_percent(percpu=False) - ogólne zużycie systemu
            self.cpu_usage.append(psutil.cpu_percent(interval=None))
            # RAM procesu w MB
            self.ram_usage.append(process.memory_info().rss / 1024 / 1024)
            time.sleep(self.interval)