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
]


def run(cmd, returncode=False):
    """
    Run a shell command and return the response as a string

        >>> run("echo testing")
        'testing\\n'

    """
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


