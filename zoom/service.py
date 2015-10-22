
import db
import os
import time
import sys

sleep_time = 0.25

def emit(t):
    sys.stdout.write('{}'.format(t))
    sys.stdout.flush()

def perform(jobs_path):
    emit('tick\n')
    for filename in os.listdir(jobs_path):
        pass
    import random
    return random.randint(0,1)

def process(jobs_path, time_to_stop=False):
    def sleep(t):
        emit('sleeping\n')
        time.sleep(t)

    done = False
    first_time = True
    while not done:

        if not first_time: sleep(sleep_time)
        first_time = False

        n = perform(jobs_path)
        emit('{} jobs performed\n'.format(n))

        if callable(time_to_stop):
            done = time_to_stop()
        else:
            done = time_to_stop


if __name__ == '__main__':

    def quittin_time(t):
        return lambda: time.time() > t

    def quit_in(t):
        stop_time = time.time() + t
        return lambda: time.time() > stop_time

    jobs_path = '/home/herb/work/services'
    process(jobs_path, quit_in(1))

    print 'ok'

