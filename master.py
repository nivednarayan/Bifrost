from multiprocessing import Process, cpu_count
from worker import worker_proxy
from config import load_config
import time
import signal
import sys

config = load_config("config.yaml")
workers = []

def handle_sighup(signum, frame):
    global config
    config = load_config("config.yaml")
    for p in workers:
        p.terminate()

def handle_sigterm(signum, frame): 
    for p in workers: 
          p.terminate()
    sys.exit()

signal.signal(signal.SIGHUP, handle_sighup)
signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == '__main__':
    for _ in range(cpu_count()):
        p = Process(target=worker_proxy, args=(config,))
        p.start()
        workers.append(p)

    while True:
        for i, p in enumerate(workers):
            if not p.is_alive():    
                p = Process(target=worker_proxy, args=(config,))
                p.start()
                workers[i] = p
        time.sleep(1)
