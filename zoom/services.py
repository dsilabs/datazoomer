
import db
import os
import time
import sys
import logging
import traceback

from subprocess import Popen, PIPE

class ServiceException(Exception): pass

ERROR_FILE = 'error.txt'

csv_formatter = logging.Formatter('"%(asctime)s","%(name)s","%(levelname)s","%(message)s"')
con_formatter = logging.Formatter('%(asctime)s  %(name)-15s %(levelname)-8s %(message)s')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(con_formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)

logger = logging.getLogger('services')

def emit(t):
    if not args.quiet:
        sys.stdout.write('{}'.format(t))
        sys.stdout.flush()

def perform(jobs_path):

    def run_main(pathname):
        def report_error(title, msg):
            logger.error(title)

            emit('\n%s\n' % title)
            emit('*' * 40 + '\n')
            emit(msg)
            emit('*' * 40 + '\n\n')

            error_file = os.path.join(path, ERROR_FILE)
            f = open(error_file,'w')
            f.write(msg)
            f.close()

        path, name = os.path.split(pathname)
        try:
            save_dir = os.getcwd()
            os.chdir(path)
            try:
                p = Popen(['python', name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                output, err = p.communicate(b"")
                rc = p.returncode
                if err:
                    report_error('error from %s' % pathname, err)

                elif rc:
                    report_error(
                            'non-zero code returned by {}'.format(pathname),
                            "return code: {}\n".format(rc)
                            )
                if output:
                    service_dir, service_name = os.path.split(path)
                    service_logger = logging.getLogger(service_name)
                    service_logger.info('. '.join(l for l in output.splitlines() if l))
            finally:
                os.chdir(save_dir)

        except Exception:
            t = traceback.format_exc()
            report_error('Exception raised', t)

        finally:
            logger.debug('ran %s' % path)

    for filename in os.listdir(jobs_path):
        pathname = os.path.abspath(os.path.join(jobs_path, filename))
        if os.path.isdir(pathname):
            fn = os.path.join(pathname, 'service.py')
            if os.path.exists(fn):
                run_main(fn)


def process(args, time_to_stop=False):
    def sleep(t):
        time.sleep(t)

    jobs_path = args.path[0]
    sleep_time = args.sleep

    done = False
    first_time = True
    while not done:

        if not first_time: sleep(sleep_time)
        first_time = False

        perform(jobs_path)

        if callable(time_to_stop):
            done = time_to_stop()
        else:
            done = time_to_stop


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser('Run background services')
    parser.add_argument('-q', '--quiet', action='store_true', help='supresss output')
    parser.add_argument('-l', '--log', action='store_true', help='log activity to info and error log files')
    parser.add_argument('-i', '--info', action='store', help='override info log file location')
    parser.add_argument('-e', '--error', action='store', help='override error info location')
    parser.add_argument('-d', '--debug', action='store_true', help='show all debugging information as services run')
    parser.add_argument('-k', '--keepalive', action='store_true', help='keep running if there is more work to do')
    parser.add_argument('-t', '--timeout', action='store', type=float, default=10, help='number of seconds to idle before stopping')
    parser.add_argument('-s', '--sleep', action='store', type=float, default=0.5, help='number of seconds to sleep while idling')
    parser.add_argument('path', metavar='P', type=str, nargs='+', help='path to workers')
    args = parser.parse_args()

    if args.debug:
        root_logger.setLevel(logging.DEBUG)
    if args.quiet:
        console_handler.setLevel(logging.ERROR)

    if args.log:
        info_log = args.info or os.path.join(args.path[0], 'info.log')
        error_log = args.error or os.path.join(args.path[0], 'error.log')

        file_handler = logging.FileHandler(info_log, 'a')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(csv_formatter)
        root_logger.addHandler(file_handler)
        
        error_handler = logging.FileHandler(error_log, 'a')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(csv_formatter)
        root_logger.addHandler(error_handler)


    def run_for(t):
        stop_time = time.time() + t
        return lambda: time.time() > stop_time

    try:
        process(args, run_for(args.timeout))
    except KeyboardInterrupt:
        logger.warning('stopped')


