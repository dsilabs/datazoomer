"""
    zoom

    DataZoomer command line utility

"""
# pylint: disable=unused-argument

import os
import time
import shlex

from subprocess import Popen, PIPE
from os.path import exists


__all__ = [
    'auto',
    'server',
    'publish',
]


def run(cmd, returncode=False):
    """
    Run a shell command and return the response as a string

        >>> run("echo testing")
        'testing\\n'

    """
    print cmd
    if returncode:
        process = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        return process.returncode, str(stdout), str(stderr)
    else:
        return str(Popen(shlex.split(cmd), stdout=PIPE).communicate()[0])

def server(options, port=8000, instance='.'):
    """run an instance using Python's builtin HTTP server"""
    from zoom.server import run
    run(port, instance)
    print('\rstopped')

def auto(options, command, name, *args):
    """run a command automatically whenever a file changes"""
    if not exists(name):
        print 'missing: %s' % name
        return False

    if os.path.isdir(name):
        print 'directory : %s' % name
        subjects = [os.path.join(name, f) for f in os.listdir(name)
                    if f.endswith('.py')]
    else:
        print 'file : %s' % name
        subjects = [name]

    print 'subjects : ', subjects

    oldstamp = {}
    done = False
    while not done:
        try:
            try:
                timestamp = {name: os.stat(name).st_mtime
                            for name in subjects}
            except OSError:
                pass

            for name in timestamp:
                if (not name in oldstamp) or (
                    oldstamp[name] < timestamp[name]):

                    oldstamp[name] = timestamp[name]
                    cmd = ' '.join([command, name] + list(args))
                    print '=' * 70
                    print 'running %r' % cmd
                    status, out, err = run(cmd, True)
                    print status
                    print '- ' * 35
                    print out
                    print '- ' * 35
                    print err
            time.sleep(1)
        except KeyboardInterrupt:
            print '\rdone\n'
            done = True


def publish(options, path, server='git@dsilabs.ca'):
    """publish a resource to a repository server"""

    abspath = os.path.abspath
    split = os.path.split
    join = os.path.join

    source = abspath(path)
    if not os.path.isdir(path):
        print('fatal: {} is not a valid path'.format(source))
    else:
        stage = source + '.git'
        path, name = split(source)
        _, kind = split(path)
        dest = server + ':' + join('dev', kind)

        if not kind in ['apps', 'libs', 'themes', 'jobs']:
            raise Exception('fatal: unknown resource type')
        t = run('ssh {} "ls dev/{}"'.format(server, kind))
        if name+'.git' in t.splitlines():
            print('fatal: {} already exists in {}'.format(name, dest))
        else:
            status, out, err = run('git clone --bare {} {}'.format(source, stage), True)
            #print status, out, err
            if status:
                print(err)
            else:
                status, out, err = run('scp -r {} {}'.format(stage, dest), True)
                if status:
                    print(err)
                else:
                    run('rm -rf {}'.format(stage))


def unpublish(options, path, server='git@dsilabs.ca'):
    """unpublish a resource from a repository server"""

    abspath = os.path.abspath
    split = os.path.split
    join = os.path.join

    source = abspath(path)
    if not os.path.isdir(path):
        print('fatal: {} is not a valid path'.format(source))
    else:
        stage = source + '.git'
        path, name = split(source)
        _, kind = split(path)
        dest = server + ':' + join('dev', kind)

        if not kind in ['apps', 'libs', 'themes', 'jobs']:
            raise Exception('fatal: unknown resource type')
        t = run('ssh {} "ls dev/{}"'.format(server, kind))
        if name+'.git' not in t.splitlines():
            print('fatal: {} does not exist in {}'.format(name, dest))
        else:
            run('ssh {} "rm -rf dev/{}/{}"'.format(server, kind, name))

