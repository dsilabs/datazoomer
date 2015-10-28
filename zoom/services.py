
import db
import os
import time
import sys
import logging
import traceback
from subprocess import Popen, PIPE, call

class ServiceException(Exception): pass

ERROR_FILE = 'traceback.txt'

con_formatter = logging.Formatter('%(asctime)s  %(name)-15s %(levelname)-8s %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(con_formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)

logger = logging.getLogger('service')
#logger.setLevel(logging.DEBUG)

sleep_time = 0.25

def emit(t):
    sys.stdout.write('{}'.format(t))
    sys.stdout.flush()

def perform(jobs_path):

    def run_main(pathname):
        path, name = os.path.split(pathname)
        try:
            save_dir = os.getcwd()
            os.chdir(path)
            try:
                p = Popen(['python', name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                output, err = p.communicate(b"")
                rc = p.returncode
                if err:
                    raise ServiceException(err)
            finally:
                os.chdir(save_dir)
        except:
            logger.error('an error occured in %s' % pathname)

            t = traceback.format_exc()

            emit('\nException occured in %s\n' % pathname)
            emit('*' * 40 + '\n')
            emit(t)
            emit('*' * 40 + '\n')

            error_file = os.path.join(path, ERROR_FILE)
            f = open(error_file,'w')
            f.write(t)
            f.close()
        finally:
            logger.debug('ran %s' % path)

    for filename in os.listdir(jobs_path):
        pathname = os.path.abspath(os.path.join(jobs_path, filename))
        if os.path.isdir(pathname):
            fn = os.path.join(pathname, 'service.py')
            if os.path.exists(fn):
                run_main(fn)

    import random
    return random.randint(0,3)

def process(jobs_path, time_to_stop=False):
    def sleep(t):
        #emit('sleeping\n')
        time.sleep(t)

    done = False
    first_time = True
    while not done:

        if not first_time: sleep(sleep_time)
        first_time = False

        n = perform(jobs_path)
        #if n:
        #    emit('{} jobs performed\n'.format(n))

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
    try:
        process(jobs_path, quit_in(2))
    except KeyboardInterrupt:
        pass


