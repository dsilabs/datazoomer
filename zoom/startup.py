"""
    zoom.startup

    This module is responsible for initializing the system, running the
    application and capturing and rendering all output.
"""

import os
import StringIO
import traceback
import cProfile
import pstats
import timeit
import sys
import urllib

from zoom.system import system, SystemTimer
from zoom.log import logger
from zoom.page import Page
from zoom.tools import redirect_to, load_template, htmlquote
from zoom.response import HTMLResponse
from zoom.session import SessionExpiredException
from zoom.request import request, data, route
from zoom.user import user
from zoom.manager import manager
from zoom.visits import visited
from zoom.cookies import set_session_cookie
from zoom.exceptions import UnauthorizedException


NEW_INSTALL_MESSAGE = """
<head>
    <style>
      body { font-family: "Helvetica Neue",Helvetica,Arial,sans-serif; }
        div#welcome { margin-left: 5%; margin-top: 50px; }
    </style>
</tail>
<body>
<div id="welcome">
<h1>Welcome!</h1>
This site is currently under construction.
</div>
</body>
"""

FRIENDLY_ERROR_MESSAGE = """
<H1>How embarrassing!</H1>
You have found an error in the <dz:site_name> system.
  Sorry about that.<br><br>

We have sent a message to the system administrator who will
 look into it as soon as possible.<br><br>

Thank you for your patience,<br>
The <dz:site_name> Team.<br>
"""

STANDARD_ERROR_MESSAGE = '<H1>Whoops!</H1><pre>%(message)s</pre>'

SYSTEM_ERROR_MESSAGE = '<H1>System Error</H1><pre>%(message)s</pre>'

SESSION_EXPIRED_MESSAGE = ('Your session has expired.'
                           'Please <a href="/login">login</a>.')

RESTRICTED_ACCESS_MESSAGE = """
<H1>Restricted Access</H1>
This site is for authorized users only.
  Please contact <dz:owner_name> for more information.
"""

SYSTEM_ERROR_TEMPLATE = """
Content-type: text/html

<H1>System Error</H1>
<pre>%s</pre>
"""

PAGE_MISSING_MESSAGE = '<H1>Page Missing</H1>Page not found'

UNAUTHORIZED_MESSAGE = ('<H1>Unauthorized</H1>Please contact'
                        'the system administator for assistance.')


class CrossSiteRequestForgeryAttempt(Exception):
    """cross site forgery attempt exception"""
    pass


def generate_response(instance_path, start_time=None):
    """generate response to web request"""

    profiler = None
    debugging = True

    system_timer = SystemTimer(start_time)

    # capture stdout
    real_stdout = sys.stdout
    sys.stdout = StringIO.StringIO()
    try:
        try:
            # initialize context
            system.setup(instance_path, request.server, system_timer)
            system_timer.add('system initializated')

            user.setup()
            system_timer.add('user initializated')

            manager.setup()
            system_timer.add('manager initializated')

            if user.is_disabled:
                # we know who the user is, and their account is disabled
                msg = 'User {user.link} is disabled'
                raise UnauthorizedException(msg.format(user=user))

            debugging = (system.debugging or system.show_errors or
                         user.is_developer or user.is_administrator)

            session = system.session

            if system.track_visits:
                visited(request.subject, session.sid)

            csrf_token = data.pop('csrf_token', None)
            if request.method == 'POST' and system.csrf_validation:
                if csrf_token == session.csrf_token:
                    del session.csrf_token
                else:
                    msg = 'expected:%s got:%s' % (
                        session.csrf_token, csrf_token)
                    raise CrossSiteRequestForgeryAttempt(msg)

            requested_app_name = manager.requested_app_name()
            default_app_name = manager.default_app_name()

            os.chdir(system.config.sites_path)

            if not request.route:
                request.route.append(default_app_name)

            for app in manager.apps.values():
                app.initialize(request)

            if manager.can_run(requested_app_name):
                system.app = manager.get_app(requested_app_name)

                profiler = (system.profile or user.profile) \
                    and cProfile.Profile()
                if profiler:
                    profiler.enable()

                system_timer.add('app ready')

                response = system.app.run(request)

                system_timer.add('app returned')

                if profiler:
                    profiler.disable()

            elif manager.can_run_if_login(requested_app_name):
                # as it stands now, an attacker can generate a list of
                # enabled apps by iterating the/a namespace and seeing
                # which ones return a logon form.

                def referrer():
                    """get the referrer"""
                    uri = urllib.urlencode(dict(referrer=request.uri))
                    return uri and "?{}".format(uri) or ''
                response = redirect_to('/login{}'.format(referrer()))

            elif not requested_app_name:
                app = manager.get_app(default_app_name)
                if app:
                    system.app = app
                else:
                    raise Exception(default_app_name + ' app missing')
                response = system.app.run(request)

            elif manager.can_run(default_app_name):
                response = redirect_to('/')

            else:
                response = Page(PAGE_MISSING_MESSAGE).render()
                response.status = '404'

            timeout = session.save_session()
            set_session_cookie(
                response,
                session.sid,
                request.subject,
                timeout,
                system.secure_cookies,
            )

        except UnauthorizedException:
            logger.security('unauthorized access attempt')
            if debugging:
                raise
            else:
                response = Page(UNAUTHORIZED_MESSAGE).render()
                response.status = '403'

        except CrossSiteRequestForgeryAttempt:
            logger.security('cross site forgery attempt')
            if debugging:
                raise
            else:
                response = redirect_to('/')

        except SessionExpiredException:
            response = Page(load_template(
                'system_application_session_expired',
                SESSION_EXPIRED_MESSAGE)).render()

        except:
            t = htmlquote(traceback.format_exc())
            logger.error(t)
            if debugging:
                try:
                    tpl = load_template(
                        'system_application_error_developer',
                        STANDARD_ERROR_MESSAGE)
                    msg = tpl % dict(message=t)
                except:
                    msg = SYSTEM_ERROR_MESSAGE % dict(message=t)
            else:
                try:
                    msg = load_template(
                        'system_application_error_user',
                        FRIENDLY_ERROR_MESSAGE
                    )
                except:
                    msg = FRIENDLY_ERROR_MESSAGE

            try:
                response = Page(msg).render()
            except:
                response = HTMLResponse(msg)

        if profiler:
            stats_s = StringIO.StringIO()
            sortby = 'cumulative'
            ps = pstats.Stats(profiler, stream=stats_s)
            ps.sort_stats(sortby)
            ps.print_stats(.1)
            t = stats_s.getvalue()
            t = t.replace(
                system.lib_path, '~zoom'
            ).replace(
                '/usr/lib/python2.7/dist-packages/',
                '~'
            ).replace(
                '/usr/local/lib/python2.7/dist-packages/',
                '~'
            )

            print(''.join([
                '\n\n  System Performance Metrics\n ' + '=' * 30,
                system_timer.report(),
                system.database.report(),
                system.db.report(),
                '  Profiler\n ------------\n',
                t
            ]))
    finally:
        printed_output = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = real_stdout
        logger.complete()

    system.release()

    if hasattr(response, 'printed_output'):
        response.printed_output = printed_output.replace(
            '<', '&lt;'
            ).replace(
            '>', '&gt;'
            )

    return response


def run_as_cgi(instance_path='..', start_time=timeit.default_timer()):

    if not os.path.exists(os.path.join(instance_path, 'dz.conf')):
        response = HTMLResponse(NEW_INSTALL_MESSAGE)
    else:
        response = generate_response(instance_path, start_time)

    sys.stdout.write(response.render())


def run_as_app(a_request):
    """run as a wsgi style app"""

    request.__dict__ = a_request.__dict__

    data.clear()
    data.update(request.data)

    del route[:]
    route.extend(request.route)

    if not os.path.exists(os.path.join(request.instance, 'dz.conf')):
        response = HTMLResponse(NEW_INSTALL_MESSAGE)
    else:
        response = generate_response(request.instance)

    return response

# pylint disable=invalid-name
run = run_as_cgi
