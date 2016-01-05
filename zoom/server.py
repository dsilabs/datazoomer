"""
    portable server

    >>> server = WSGIApplication()
"""

import sys
from request import Request
import middleware
from wsgiref.simple_server import make_server
from middleware import handle


#----------- WSGI application
#def application(environ, start_response):
    #return WSGIApplication()(environ, start_response)


class WSGIApplication(object):
    def __init__(self, instance='.', handlers=None):
        self.handlers = handlers
        self.instance = instance

    def __call__(self, environ, start_response):
        request = Request(environ, self.instance)
        status, headers, content = middleware.handle(
                request,
                self.handlers,
                )
        start_response(status, headers)
        return [content]

def run_once(port=8004, instance=None):
    done = False
    try:
        while not done:
            server = make_server('', port, WSGIApplication(instance))
            try:
                server.handle_request()
            finally:
                del server
            done = True
    except KeyboardInterrupt:
        print('done')

def run(port=8004, instance=None):
    server = make_server('', port, WSGIApplication(instance))
    server.serve_forever()

if __name__ == '__main__':
    port = 8004
    instance = '/home/herb/work/web'
    run(port, instance)
