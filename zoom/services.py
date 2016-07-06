"""
    services.py

    background services
"""

import os
import time
import sys
import logging
import traceback
import ConfigParser
import shlex
import platform
import datetime

import zoom
from zoom.db import database as DB
from subprocess import Popen, PIPE

class ServiceException(Exception): pass

ERROR_FILE = 'error.txt'

csv_formatter = logging.Formatter('"%(asctime)s","%(name)s","%(levelname)s","%(message)s"')
con_formatter = logging.Formatter('%(asctime)s  %(name)-15s %(levelname)-8s %(message)s')

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

logger = logging.getLogger('services')


def get_logger(name):
    """convenience function for services to get a logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    info_log = '../info.log'
    file_handler = logging.FileHandler(info_log, 'a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(csv_formatter)
    logger.addHandler(file_handler)

    error_log = '../error.log'
    error_handler = logging.FileHandler(error_log, 'a')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(csv_formatter)
    logger.addHandler(error_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(con_formatter)
    logger.addHandler(console_handler)

    return logger


# Config
# ==================================================================================
def parents(path):
    if not os.path.isdir(path):
        return parents(os.path.split(os.path.abspath(path))[0])
    parent = os.path.abspath(os.path.join(path, os.pardir))
    if path == parent:
        return []
    else:
        return [path] + parents(parent)

def locate_config(filename='services.ini', start='.'):
    for path in parents(start):
        pathname = os.path.join(path, filename)
        if os.path.exists(pathname):
            return pathname
    for path in parents(os.path.join(os.path.expanduser('~'))):
        pathname = os.path.join(path, filename)
        if os.path.exists(pathname):
            return pathname

class Config(object):

    def __init__(self, filename):
        self.config = ConfigParser.ConfigParser()
        if not filename or not os.path.exists(filename):
            raise Exception('%s file missing' % filename)
        self.config.read(filename)

    def get(self, section, option, default=None):
        try:
            return self.config.get(section, option)
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            if default != None:
                return default
            raise

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

    def __init__(self, name, debug=False):
        self.name = name
        self.debug = debug

    def every(self, interval, function):
        """run a function on given time interval

        If any intervals have been missed since the last run then the Scheduler
        will skip over the missed intervals and just run the function one time
        to catch up.
        """
        name = self.name + '.' + function.__name__ + '.run'
        if self.debug:
            print 'event name: ', name
        now = datetime.datetime.now()
        last_run = peek(name, now - interval)
        next = last_run + interval
        if self.debug or now >= next:
            if now >= next:
                intervals_missed = (now - next).seconds / interval.seconds
                next += intervals_missed * interval
                poke(name, next)
            else:
                poke(name, now)
            function()


# Background Processing Classes
# ==================================================================================
class Site(object):

    def __init__(self, name):
        self.name = name


class Instance(object):
    """represents an installed DataZoomer instance

    Use for performing methods on an entire instance.
    """

    def __init__(self, name, path='.'):
        self.name = name
        self.config = Config(locate_config('dz.conf', path))

    @property
    def sites_path(self):
        """the path to the sites of the instance"""
        return self.config.get('sites', 'path')

    @property
    def path(self):
        """the path of the instance"""
        path, _ = os.path.split(self.sites_path)
        return path

    @property
    def sites(self):
        """a list of sites for the instance"""
        listdir = os.listdir
        isdir = os.path.isdir
        join = os.path.join
        path = self.sites_path
        return [Site(name) for name in listdir(path) if isdir(join(path, name))]

    def run(self, *jobs):
        """run jobs on an entire instance"""
        logger = logging.getLogger(self.name)
        for site in self.sites:
            try:
                zoom.system.setup(self.path, site.name)
            except Exception, e:
                logger.warning(str(e))
                logger.warning('unable to setup {}'.format(site.name))
                continue
            if zoom.system.background:
                for job in jobs:
                    logger.debug('running {}.{} for {}'.format(self.name,
                                                               job.__name__,
                                                               site.name))
                    job()


class Worker(object):
    """background worker

    Usually used only internally."""
    def __init__(self, service, function):
        self.service = service
        self.function = function

    @property
    def topic(self):
        """return the topic this worker listens to"""
        return ''.join(['service.', self.service, '.', self.function.__name__])

    @property
    def queue(self):
        """return the queue this worker uses"""
        return zoom.system.queues.topic(self.topic, 1)

    def process(self):
        """process a job"""
        system = zoom.system
        return self.queue.process(self.function)


class Service(object):
    """background processing service

    Use this class to create a service.
    """

    def __init__(self, name, schedule=None):
        self.name = name
        self.schedule = schedule

    def process(self, *jobs):
        """process service requests for all sites"""
        workers = [Worker(self.name, job).process for job in jobs]
        Instance(self.name).run(*workers)

    def run(self, job, a0=None, *a, **k):
        """queue a job"""
        Worker(self.name, job).queue.put(a0, *a, **k)

    def call(self, job, *a, **k):
        """queue a job expecting a result"""
        queue = Worker(self.name, job).queue
        id = queue.put(*a, **k)
        result = queue.join([id])[0]
        return result


# Job runner
# ==================================================================================
def cmd(x, returncode=False, location=None):
    """
    Run a shell command and return the response as a string

        >>> cmds = platform.system() == 'Windows' and "{} /c echo testing".format(os.environ.get('COMSPEC','cmd.exe')) or "echo testing"
        >>> res =cmd(cmds)
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

        more_to_do = False

        path, name = os.path.split(pathname)
        try:
            save_dir = os.getcwd()
            os.chdir(path)
            try:
                p = Popen(['python', name], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                output, err = p.communicate(b"")
                rc = p.returncode
                if err:
                    report_error('error %s from %s' % (err, pathname), err)

                elif rc:
                    if args.keepalive:
                        more_to_do = True
                    else:
                        report_error(
                                'non-zero code returned by {}'.format(pathname),
                                "return code: {}\n".format(rc)
                                )
                if output:
                    #service_dir, service_name = os.path.split(path)
                    #service_logger = logging.getLogger(service_name)
                    #if args.raw:
                    emit(output)
                    pass
                    #else:
                    #    service_logger.info('. '.join(l for l in output.splitlines() if l))
            finally:
                os.chdir(save_dir)

        except Exception:
            t = traceback.format_exc()
            report_error('Exception raised', t)

        finally:
            logger.debug('ran %s' % path)

        return more_to_do

    work_remaining = []
    for filename in os.listdir(jobs_path):
        pathname = os.path.abspath(os.path.join(jobs_path, filename))
        if os.path.isdir(pathname):
            fn = os.path.join(pathname, 'service.py')
            skipfile = os.path.join(pathname, 'skip')
            if os.path.exists(fn) and not os.path.exists(skipfile):
                work_remaining.append(run_main(fn))

    return any(work_remaining)

def run_for(t):
    if not t: return False
    stop_time = time.time() + t
    return lambda: time.time() > stop_time


def process(args, time_to_stop=False):
    def sleep(t):
        time.sleep(t)

    jobs_path = args.path[0]
    sleep_time = args.sleep

    logger.info('starting services in %s' % jobs_path)

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

    logger.info('done')

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser('Run background services')
    parser.add_argument('-q', '--quiet', action='store_true', help='supresss output')
    parser.add_argument('-l', '--log', action='store_true', help='log activity to info and error log files')
    parser.add_argument('-i', '--info', action='store', help='override info log file location')
    parser.add_argument('-e', '--error', action='store', help='override error info location')
    parser.add_argument('-r', '--raw', action='store_true', help='raw output')
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

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(con_formatter)
    root_logger.addHandler(console_handler)

    try:
        process(args, run_for(args.timeout))
    except KeyboardInterrupt:
        logger.warning('stopped')


