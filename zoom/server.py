
import sys

#from zoom.startup import run_as_wsgi

#def run(port=8000):
#    from wsgiref.simple_server import make_server
#    from start import application
#    server = make_server('' , port, application)
#    done = False
#    while not done:
#        try:
#            server.handle_request()
#        except KeyboardInterrupt:
#            sys.stdout.write('\rdone\n')
#            done = True
#        done = True
#
#def run(port=8004, middleware=None):
#    from wsgiref.simple_server import make_server
#    def handle(environ, start_response):
#        return run_as_wsgi(environ, start_response)
#    server = make_server('' , port, handle)
#    #server = make_server('' , port, run_as_wsgi)
#    done = False
#    while not done:
#        try:
#            server.handle_request()
#        except KeyboardInterrupt:
#            sys.stdout.write('\rdone\n')
#            done = True

def run(port=8004, handlers=None, root=None):
    from wsgiref.simple_server import make_server
    from start import application, WSGIApplication
    server = make_server('' , port, WSGIApplication(handlers, root))
    done = False
    while not done:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            sys.stdout.write('\rdone\n')
            done = True

