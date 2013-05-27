#
# This module is responsible for initializing the system, running the application
# and capturing and rendering all output.
# 

import sys
import os
import StringIO
import traceback
import datetime

from system import system
from log import logger
from page import Page
from tools import redirect_to, load_template
from response import HTMLResponse, RedirectResponse
from session import session, SessionExpiredException
from request import request, data
from user import user
from manager import manager

FRIENDLY_ERROR_MESSAGE = """
<H1>How embarrassing!</H1>
You have found an error in the <dz:site_name> system.  Sorry about that.<br><br>

We have sent a message to the system administrator who will look into it as soon as possible.<br><br>

Thank you for your patience,<br>
The <dz:site_name> Team.<br>
"""

STANDARD_ERROR_MESSAGE = '<H1>Whoops!</H1><pre>%(message)s</pre>'

SESSION_EXPIRED_MESSAGE = 'Your session has expired.  Please <a href="/login">login</a>.'

RESTRICTED_ACCESS_MESSAGE = "<H1>Restricted Access</H1>This site is for authorized users only.  Please contact <dz:owner_name> for more information."

SYSTEM_ERROR_TEMPLATE = \
"""
Content-type: text/html

<H1>System Error</H1>
<pre>%s</pre>
"""

class CrossSiteRequestForgeryAttempt(Exception): pass

def generate_response(instance_path):

    # capture stdout
    real_stdout = sys.stdout
    sys.stdout = StringIO.StringIO()
    try:
        try:
            system.setup(instance_path)
            logger.setup()
            session.load_session()
            user.setup()
            manager.setup()

            csrf_token = data.pop('csrf_token',None)
            if request.method == 'POST' and system.csrf_validation:
                if csrf_token == session.csrf_token:
                    del session.csrf_token
                else:
                    raise CrossSiteRequestForgeryAttempt('expected:%s got:%s' % (session.csrf_token, csrf_token))

            requested_app_name = manager.requested_app_name()
            default_app_name   = manager.default_app_name()

            os.chdir(system.config.sites_path)

            if not request.route:
                request.route.append(default_app_name)
            if manager.can_run(requested_app_name):
                system.app = manager.get_app(requested_app_name)
                response = system.app.run()
            elif not requested_app_name:
                system.app = manager.get_app(default_app_name)
                response = system.app.run()
            elif manager.can_run(default_app_name):
                response = redirect_to('/')
            else:
                response = Page('<H1>Page Missing</H1>Page not found').render()
                response.status = '404'

            session.save_session(response)

        except CrossSiteRequestForgeryAttempt:
            logger.security('cross site forgery attempt')
            if not (system.config.get('error','users','0')=='1' or user.is_developer or user.is_administrator):
                raise
            else:
                response = redirect_to('/')

        except SessionExpiredException:
            response = Page(load_template('system_application_session_expired', SESSION_EXPIRED_MESSAGE)).render()

        except:
            t = traceback.format_exc()
            logger.error(t)
            if system.config.get('error','users','0')=='1' or user.is_developer or user.is_administrator:
                msg = load_template('system_application_error_developer', STANDARD_ERROR_MESSAGE)
                response = Page(msg % dict(message=t)).render()
            else:
                msg = load_template('system_application_error_user', FRIENDLY_ERROR_MESSAGE)
                response = Page(msg).render()

    finally:
        printed_output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = real_stdout
        logger.complete()

    if hasattr(response,'printed_output'):
        response.printed_output = printed_output.replace('<','&lt;').replace('>','&gt;')

    return response

def run_as_cgi(instance_path='..'):
    response = generate_response(instance_path)
    sys.stdout.write(response.render())

run = run_as_cgi

