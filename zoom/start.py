
import os
import sys
import request
import middleware

path = os.path.dirname('.')
if not path in sys.path:
    sys.path.insert(0, path)


#----------- WSGI application
def application(environ, start_response):
    return WSGIApplication()(environ, start_response)

class WSGIApplication(object):
    def __init__(self, handlers=None, root=None):
        self.handlers = handlers
        self.root = root

    def __call__(self, environ, start_response):
        req = request.request
        req.setup(environ, self.root)
        req.root = self.root
        status, headers, content = middleware.handle(
                req,
                #self.handlers,
                )
        start_response(status, headers)
        return [content]



#----------- CGI handler
def output_header(status, response_headers):
    s = 'Status: %s\n' % status
    h = ''.join(["%s: %s\n" % x for x in response_headers])
    sys.stdout.write(s + h + '\n')

def handler():
    t = application(os.environ, output_header)
    sys.stdout.write(''.join(t))


#-----------
if __name__ == '__main__':
    print(handler())
