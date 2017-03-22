"""
    services.py

    background services
"""

import os
import time
import sys
import logging
import traceback
import shlex
import platform
import datetime
import argparse

from subprocess import Popen, PIPE

import zoom
from zoom.db import database as DB
from zoom.utils import locate_config, Config
from zoom.instance import Instance


class ServiceException(Exception): pass

ERROR_FILE = 'error.txt'

# Logging
# ==================================================================================
csv_formatter = logging.Formatter('"%(asctime)s","%(name)s","%(levelname)s","%(message)s"')
con_formatter = logging.Formatter('%(asctime)s  %(name)-15s %(levelname)-8s %(message)s')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(con_formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)

logger = logging.getLogger('services')


def get_logger(name):
    """convenience function for services to get a logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    info_log = '../info.log'
    info_handler = logging.FileHandler(info_log, 'a')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(csv_formatter)
    logger.addHandler(info_handler)

    error_log = '../error.log'
    error_handler = logging.FileHandler(error_log, 'a')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(csv_formatter)
    logger.addHandler(error_handler)

    return logger


# Database
# ==================================================================================
_db = None

DB_NGIN = 'mysql'
DB_HOST = 'localhost'
DB_NAME = 'datazoomer'
DB_USER = 'root'
DB_PASS = ''

db_defaults = dict(
    engine = DB_NGIN,
    host = DB_HOST,
    name = DB_NAME,
    user = DB_USER,
    passwd = DB_PASS,
)

def connect_db(*a, **k):
    if 'config' in k:
        if not os.path.exists(k['config']):
            raise Exception('Config file missing.')
        config = Config(k['config'])
        plist = [
            ('engine','engine','engine'),
            ('host','host','dbhost'),
            ('name','db','dbname'),
            ('user','user','dbuser'),
            ('passwd','password','dbpass')
        ]
        db_params = {}
        for p,s,t in plist:
            v = k.get(p, config.get('database', t, db_defaults.get(p)))
            if v:
                if p == 'name':
                    s = 'db'
                else:
                    s = p
                db_params[s] = v
        try:
            db = DB(**db_params)
        except:
            logger.error('Error connecting to database with config %s' % repr((a,k)))
            raise
        logger.debug('Connected to db with config %s' % repr((a,k)))
    else:
        try:
            db = DB(*a, **k)
        except:
            logger.error('Error connecting to database with config %s' % repr((a,k)))
            raise
        logger.debug('Connected to db with %s' % repr((a,k)))
    return db

def db(*a, **k):
    global _db
    return _db(*a, **k)

def get_db():
    """ return a configured db object """
    config = locate_config('services.ini')
    return connect_db(config=config)

def services_file_missing(*a, **k):
    raise Exception('error: unable to locate services.ini config file')

def use(dbname):
    global _db
    return _db.use(dbname)

def store(kind, db=None):
    if db == None:
        db = _db
    if type(kind) == str:
        s = zoom.EntityStore(db)
        s.kind = kind
    else:
        s = zoom.EntityStore(db, kind)
    return s

_config = locate_config('services.ini')
if _config:
    _db = connect_db(config=_config)
else:
    _db = services_file_missing

# State
# ==================================================================================
class ServiceState(zoom.Entity): pass

def poke(name, value=None):
    s = store(ServiceState, _db)
    if value==None:
        rec = s.first(name=name)
        if rec: s.delete(rec)
    else:
        r = s.first(name=name)
        if r:
            r.value = value
        else:
            r = ServiceState(name=name, value=value)
        s.put(r)

def peek(name, default=None):
    s = store(ServiceState, _db)
    r = s.first(name=name)
    return r and r.value or default


# Job Scheduling
# ==================================================================================
class Scheduler(object):
    """process scheduler"""

    def __init__(self, name, debug=False):
        self.name = name
        self.debug = debug

    def its_time(self, interval):
        """return True if interval time has passed
        """
        if type(interval) != datetime.timedelta:
            interval = datetime.timedelta(minutes=interval)
        name = '{}.({}).run'.format(self.name, interval)
        logger.debug('cell name: %s', name)
        now = datetime.datetime.now()
        last_run = peek(name, now - interval)
        next = last_run + interval
        if self.debug or now >= next:
            logger.debug('time interval has passed')
            if now >= next:
                intervals_missed = (now - next).seconds / interval.seconds
                if intervals_missed:
                    logger.debug('{} intervals missed'.format(intervals_missed))
                next += intervals_missed * interval
                poke(name, next)
            else:
                poke(name, now)
            return True
        else:
            logger.debug('next interval {}'.format(next))
        return False

    def every(self, interval, function):
        """run a function on given time interval

        If any intervals have been missed since the last run then the Scheduler
        will skip over the missed intervals and just run the function one time
        to catch up.
        """
        name = self.name + '.' + function.__name__ + '.run'
        logger.debug('cell name: %s', name)
        now = datetime.datetime.now()
        last_run = peek(name, now - interval)
        next = last_run + interval
        if self.debug or now >= next:
            logger.debug('running now')
            if now >= next:
                intervals_missed = (now - next).seconds / interval.seconds
                if intervals_missed:
                    logger.debug('{} intervals missed'.format(intervals_missed))
                next += intervals_missed * interval
                poke(name, next)
            else:
                poke(name, now)
            function()
        else:
            logger.debug('next run {}'.format(next))


# Background Processing Classes
# ==================================================================================


class Worker(object):
    """background worker

    Usually used only internally."""
    def __init__(self, service, function):
        self.service = service
        self.function = function
        self.name = type(function) == type('') and function or function.__name__

    @property
    def topic(self):
        """return the topic this worker listens to"""
        return ''.join(['service.', self.service.name, '.', self.name])

    @property
    def queue(self):
        """return the queue this worker uses"""
        return zoom.system.queues.topic(self.topic, 1)

    def process(self):
        """process a job"""
        self.service.logger.debug('processing jobs on queue {!r}'.format(self.topic))
        return self.queue.process(self.function)

    def __call__(self):
        self.process()


class Service(object):
    """background processing service

    Use this class to create a service.
    """

    def __init__(self, name, schedule=None):
        self.name = name
        self.schedule = schedule
        if not zoom.system.is_setup:
            zoom.system.setup()
        self.logger = get_logger(name)
        self.instance = Instance(self.name)

    def process(self, *jobs):
        """process service requests for all sites"""
        parser = argparse.ArgumentParser('Run {!r} background services'.format(self.name))
        parser.add_argument('-q', '--quiet', action='store_true', help='supresss output')
        parser.add_argument('-n', '--dryrun', action='store_true', help='don\'t actually run the services, just show if they exists and would have been run.')
        parser.add_argument('-d', '--debug', action='store_true', help='show all debugging information as services run')
        args = parser.parse_args()

        if args.debug:
            console_handler.setLevel(logging.DEBUG)

        if args.quiet:
            console_handler.setLevel(logging.ERROR)

        self.logger.debug('service {} starting'.format(
            self.name,
        ))

        workers = [Worker(self, job) for job in jobs]
        self.instance.run(*workers)

        self.logger.debug('service {} done'.format(
            self.name,
        ))

    def every(self, interval, *jobs):
        """process jobs on an time interval"""
        parser = argparse.ArgumentParser('Run {!r} background services'.format(self.name))
        parser.add_argument('-q', '--quiet', action='store_true', help='supresss output')
        parser.add_argument('-n', '--dryrun', action='store_true', help='don\'t actually run the services, just show if they exists and would have been run.')
        parser.add_argument('-d', '--debug', action='store_true', help='show all debugging information as services run')
        parser.add_argument('-f', '--force', action='store_true', help='force services to run ahead of schedule')
        args = parser.parse_args()

        if args.debug:
            debug_log = '../debug.log'
            debug_handler = logging.FileHandler(debug_log, 'a')
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(csv_formatter)
            logger.addHandler(debug_handler)

            console_handler.setLevel(logging.DEBUG)

        if args.quiet:
            console_handler.setLevel(logging.ERROR)

        self.logger.debug('service {!r} starting'.format(
            self.name,
        ))

        scheduler = Scheduler(self.name, args.force)
        if scheduler.its_time(interval):
            self.instance.run(*jobs)

        self.logger.debug('service {!r} done'.format(
            self.name,
        ))


    def run(self, job, a0=None, *a, **k):
        """queue a job"""
        Worker(self, job).queue.put(a0, *a, **k)

    def call(self, job, *a, **k):
        """queue a job expecting a result"""
        queue = Worker(self, job).queue
        id = queue.put(*a, **k)
        result = queue.join([id])[0]
        return result



# Job runner
# ==================================================================================
def cmd(x, returncode=False, location=None):
    """
    Run a shell command and return the response as a string

        >>> cmds = platform.system() == 'Windows' and "{} /c echo testing".format(os.environ.get('COMSPEC','cmd.exe')) or "echo testing"
        >>> res = cmd(cmds)
        >>> assert res.strip() == 'testing'

    """
    logger.debug('cmd(%r)' % cmd)
    save_dir = os.getcwd()
    posix = platform.system() <> 'Windows' and True or False
    try:
        if returncode:
            # capture return code, stdout and stderr
            if location: os.chdir(location)
            p = Popen(shlex.split(x, posix=posix), stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            result = p.returncode, str(stdout), str(stderr)
        else:
            # capture stdout only
            result = str(Popen(shlex.split(x, posix=posix), stdout=PIPE).communicate()[0])
    finally:
        os.chdir(save_dir)
    return result


def emit(t):
    if t and not args.quiet:
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

            error_file = os.path.abspath(os.path.join(path, ERROR_FILE))
            f = open(error_file,'w')
            f.write(msg)
            f.close()

            logger.error('error output dumped to {}'.format(error_file))

        more_to_do = False

        path, name = os.path.split(pathname)
        try:
            save_dir = os.getcwd()
            os.chdir(path)
            try:

                if args.dryrun:
                    logger.info('would run {}'.format(pathname))
                    err = False
                    rc = 0
                    output = ''
                else:
                    logger.debug('running {}'.format(pathname))
                    cmd = ['python', name]
                    if args.debug:
                        cmd.append('-d')
                    logger.debug('running {!r} in {}'.format(' '.join(cmd), path))
                    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                    output, err = p.communicate(b"")
                    rc = p.returncode

                if err:
                    report_error('error %s from %s' % (err, pathname), err)
                elif rc:
                    if args.keepalive:
                        logger.debug('keepalive with return code {!r}'.format(rc))
                        more_to_do = True
                    else:
                        report_error(
                                'non-zero code returned by {}'.format(pathname),
                                "return code: {}\n".format(rc)
                                )
                emit(output)

            finally:
                os.chdir(save_dir)

        except Exception:
            t = traceback.format_exc()
            report_error('Exception raised', t)

        finally:
            logger.debug('ran %s' % pathname)
            logger.debug('return code {!r}, more_to_do={!r}'.format(rc, more_to_do))

        return more_to_do

    work_remaining = []
    for filename in os.listdir(jobs_path):
        pathname = os.path.abspath(os.path.join(jobs_path, filename))
        if os.path.isdir(pathname):
            fn = os.path.join(pathname, 'service.py')
            skipfile = os.path.join(pathname, 'skip')
            if os.path.exists(fn) and not os.path.exists(skipfile):
                work_remaining.append(run_main(fn))
            elif os.path.exists(skipfile):
                logger.debug('skipping {}'.format(pathname))

    return any(work_remaining)


def run_for(t):
    if t == None: return True
    stop_time = time.time() + t
    return lambda: time.time() > stop_time


def process(args, time_to_stop=False):
    def sleep(t):
        time.sleep(t)

    jobs_path = args.path[0]
    sleep_time = args.sleep

    logger.debug('starting services in %s' % jobs_path)

    done = False
    first_time = True
    while not done:

        if not first_time: sleep(sleep_time)
        first_time = False

        r = perform(jobs_path)

        if r:
            logging.debug('resetting timer to {} seconds'.format(args.timeout))
            time_to_stop = run_for(args.timeout)

        if callable(time_to_stop):
            done = time_to_stop()
        else:
            done = time_to_stop

    logger.debug('done')

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Run background services')
    parser.add_argument('-q', '--quiet', action='store_true', help='supress output')
    parser.add_argument('-l', '--log', action='store_true', help='log activity to info and error log files')
    parser.add_argument('-i', '--info', action='store', help='override info log file location')
    parser.add_argument('-e', '--error', action='store', help='override error info location')
    parser.add_argument('-r', '--raw', action='store_true', help='raw output')
    parser.add_argument('-n', '--dryrun', action='store_true', help='don\'t actually run the services, just show if they exists and would have been run.')
    parser.add_argument('-d', '--debug', action='store_true', help='show all debugging information as services run')
    parser.add_argument('-k', '--keepalive', action='store_true', help='keep running if there is more work to do')
    parser.add_argument('-t', '--timeout', action='store', type=float, default=None, help='number of seconds to idle before stopping')
    parser.add_argument('-s', '--sleep', action='store', type=float, default=0.5, help='number of seconds to sleep while idling')
    parser.add_argument('path', metavar='P', type=str, nargs='+', help='path to workers')
    args = parser.parse_args()

    join = os.path.join
    abspath = os.path.abspath

    if args.log:

        if args.debug:
            debug_log_pathname = abspath(args.error or join(args.path[0], 'debug.log'))
            debug_handler = logging.FileHandler(debug_log_pathname, 'a')
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(csv_formatter)
            root_logger.addHandler(debug_handler)

        info_log_pathname = abspath(args.info or join(args.path[0], 'info.log'))
        file_handler = logging.FileHandler(info_log_pathname, 'a')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(csv_formatter)
        root_logger.addHandler(file_handler)
        
        error_log_pathname = abspath(args.error or join(args.path[0], 'error.log'))
        error_handler = logging.FileHandler(error_log_pathname, 'a')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(csv_formatter)
        root_logger.addHandler(error_handler)

    if args.debug:
        console_handler.setLevel(logging.DEBUG)

    if args.quiet:
        console_handler.setLevel(logging.ERROR)

    if args.log:
        if args.debug:
            logger.debug('logging debug to %s', debug_log_pathname)
        logger.debug('logging errors to %s', error_log_pathname)
        logger.debug('logging info to %s', info_log_pathname)
    else:
        logger.debug('logging is off (use -l to turn on)')

    try:
        process(args, run_for(args.timeout))
    except KeyboardInterrupt:
        sys.stdout.write('\r')
        logger.warning('stopped')
