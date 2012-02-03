"""zoom: manages web apps"""

from __future__ import generators

__version__ = "0.01"
__author__ = [
    "Herb Lainchbury <herb@dynamic-solutions.com>",
    ]
__license__ = "Mozilla Public License 1.1"
__contributors__ = [
]


import web

from response import *

from request import Request
from system import System
from user import User
from session import Session

request = Request()
system = System()
session = Session()
user = User()

def request_handler(instance_path='../sites'):

    # Initialize handy (and threadsafe) global objects
    global request, system, session, user
    request.setup(web.ctx)
    system.setup(instance_path, request)
    session.setup(system.database)
    user.setup(system.database, session.username or system.guest_username)

    return system.run()

def run(instance_path='../sites'):

    urls = (
        '/.*', request_handler,
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



