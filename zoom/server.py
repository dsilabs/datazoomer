"""
    portable server

    runs an instance of DataZoomer using the builtin Python WSGI server.

    >>> server = WSGIApplication()
"""

import sys
from wsgiref.simple_server import make_server
from timeit import default_timer as timer

from zoom.request import Request
import zoom.middleware

def reset_modules():
    """reset the modules to a known starting set

    memorizes the modules currently in use and then removes any other
    modules when called again"""
    global init_modules
    if globals().has_key('init_modules'):
        for module in [x for x in sys.modules.keys() if x not in init_modules]:
            del sys.modules[module]
    else:
        init_modules = sys.modules.keys()


class WSGIApplication(object):
    """a WSGI Application wrapper for DataZoomer
    """
    def __init__(self, instance='.', handlers=None):
        self.handlers = handlers
        self.instance = instance

    def __call__(self, environ, start_response):
        reset_modules()
        start_time = timer()
        request = Request(environ, self.instance, start_time)
        status, headers, content = middleware.handle(
            request,
            self.handlers,
        )
        start_response(status, headers)
        return [content]


def run(port=8004, instance=None):
    """run DataZoomer using internal HTTP Server

    The instance variable is the path of the directory on the system where the
    sites folder is located. (e.g. /work/web)
    """
    server = make_server('', port, WSGIApplication(instance))
    server.serve_forever()


