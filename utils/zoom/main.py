"""
    zoom

    DataZoomer command line utility
"""

import inspect

from optparse import OptionParser

from zoom import ItemList

import commands


class SimpleException(Exception):
    """an exception that traps everything"""
    pass


def get_functions():
    """get a dictionary containing the valid command functions"""
    functions = {
        command: getattr(commands, command) for
        command in dir(commands) if command in commands.__all__
    }
    return functions


def dispatch(args, options):
    """dispatch a command for running"""
    functions = get_functions()
    cmd = args[0]
    if cmd in functions:
        functions[cmd](options, *args[1:])
    else:
        raise Exception('No such command %s' % cmd)


def list_commands():
    """print lits of valid commands to stdout"""
    result = ItemList([('command', 'purpose', 'usage')])
    for name, function in sorted(get_functions().items()):
        if not name.startswith('_'):
            doc = function.__doc__
            argspec = inspect.getargspec(function)
            sig = ['zoom {} [<options>]'.format(name)]
            sig.extend(['<{}>'.format(arg)
                        for arg in argspec.args if arg != 'options'])
            if argspec.varargs:
                sig.append('[{}...]'.format(argspec.varargs))
            sig = ' '.join(sig)
            result.append([name, doc, sig])
    print result


def main():
    """main program

    calls the appropriate method corresponding to the command line args
    """

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet", dest="verbose",
                      action="store_false", default=True,
                      help="don't print status messages to stdout")
    (options, args) = parser.parse_args()

    try:
        if len(args):
            dispatch(args, options)
        else:
            list_commands()

    except SimpleException as msg:
        print 'fatal: %s' % msg


if __name__ == '__main__':
    main()
