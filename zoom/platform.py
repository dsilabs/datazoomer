
import os
import web
import Cookie

from request import Request
from system import System
from user import User
from session import Session
from response import *

SESSION_COOKIE_NAME = 'zoom_sid'
SESSION_COOKIE_LIFESPAN = 60

# handy (and threadsafe) global objects
request = Request()
system = System()
user = User()
session = Session()

def get_current_username(system):
    return \
        system.config.get('users','override','') or \
        session.get('username',None) or \
        os.environ.get('REMOTE_USER',None) or \
        system.config.get('users','default','guest') or \
        None

def bake_session_cookie(sid, host, lifespan, secure=True):
    cookie = Cookie.SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = sid
    cookie[SESSION_COOKIE_NAME]['httponly'] = True
    cookie[SESSION_COOKIE_NAME]['expires'] = 60 * lifespan
    if secure:
        cookie[SESSION_COOKIE_NAME]['secure'] = True
    (k,v) = cookie[SESSION_COOKIE_NAME].output().split(':',1)
    return k, v

class Handler:
    """
    Handles requests.
    """

    def __init__(self, instance_path='../sites'):
        self.instance_path = os.path.abspath(instance_path)

    def __call__(self):

        global request, system, session, user

        try:

            request.setup(web.ctx)
            system.setup(self.instance_path, request)

            # establish session
            sid = system.request.cookies.get(SESSION_COOKIE_NAME, None)
            db = system.database
            ip = '1.1.1.1'
            new_sid = session.establish(db, ip, sid)

            current_username = get_current_username(system)

            user.setup(system.database, current_username)

            response = system.run()

            # save session
            lifespan = 60
            session.save(lifespan)
            web.header(*bake_session_cookie(new_sid, 'localhost', lifespan, secure=False))

            return response

        except:
            import traceback
            result = HTMLResponse('<pre>handle_request exception:\n\n%s</pre>' % traceback.format_exc())
            for k,v in result.headers.iteritems():
                web.header(k,v)
            content = result.content
            web.header('Content-length',str(len(content)))
            return content

def run(instance_path='../sites'):
    """
    Run this instance.  Called once when server starts.
    """

    urls = (
        '/.*', Handler(instance_path),
        #'.*', foo,
        )

    try:
        platform = web.application(urls)
        platform.run()

    except SystemExit:
        pass

    except:
        import traceback
        print 'Content-type: text/html\n\n'
        print '<pre>%s</pre>'  % traceback.format_exc()



