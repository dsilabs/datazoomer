# -*- coding: utf-8 -*-

"""
    zoom.request

    Web requsets.
"""

import os
import sys
import cgi
import urllib
import uuid
from timeit import default_timer as timer

from types import ListType

import zoom.cookies


SESSION_COOKIE_NAME = zoom.cookies.SESSION_COOKIE_NAME
SUBJECT_COOKIE_NAME = zoom.cookies.SUBJECT_COOKIE_NAME


class Webvars(object):
    """Extracts parameters sent as part of the request"""

    # pylint: disable=too-few-public-methods

    def __init__(self, env=None):
        """gather query fields"""

        env = env or os.environ

        # switch to binary mode on windows systems
        # msvcrt and O_BINARY are only defined in Windows Python
        # pylint: disable=import-error
        # pylint: disable=no-member
        try:
            import msvcrt
            msvcrt.setmode(0, os.O_BINARY)  # stdin  = 0
            msvcrt.setmode(1, os.O_BINARY)  # stdout = 1
        except ImportError:
            pass

        module = env.get('wsgi.version', None) and 'wsgi' or 'cgi'

        if env.get('REQUEST_METHOD', 'GET').upper() in ['GET']:
            cgi_fields = cgi.FieldStorage(environ=env, keep_blank_values=1)
        else:
            if module == 'wsgi':
                post_env = env.copy()
                post_env['QUERY_STRING'] = ''
                cgi_fields = cgi.FieldStorage(
                    fp=env.get('wsgi.input'),
                    environ=post_env,
                    keep_blank_values=True
                )
            else:
                cgi_fields = cgi.FieldStorage(
                    fp=sys.stdin,
                    environ=env,
                    keep_blank_values=1
                )

        items = {}
        for key in cgi_fields.keys():

            # ignore legacy setup
            if key == '_route':
                continue

            if type(cgi_fields[key]) == ListType:
                items[key] = [item.value for item in cgi_fields[key]]
            elif cgi_fields[key].filename:
                items[key] = cgi_fields[key]
            else:
                items[key] = cgi_fields[key].value
        self.__dict__ = items

    def __getattr__(self, name):
        return ''  # return blank for missing attributes

    def __str__(self):
        return repr(self.__dict__)

    def __repr__(self):
        return str(self)


def get_parent_dir():
    """get the directory above the current directory"""
    return os.path.split(os.path.abspath(os.getcwd()))[0]


class Request(object):
    """A web request"""

    # pylint: disable=too-few-public-methods, too-many-instance-attributes

    def __init__(self, env=None, instance=None, start_time=None):
        env = env or os.environ
        self.start_time = start_time or timer()
        self.ip_address = None
        self.session_token = None
        self.server = None
        self.route = []
        self.data = {}
        self.referrer = None
        self.uri = None
        self.subject = None
        self.method = None
        self.instance = None
        self.path = ''
        self.setup(env, instance)

    def setup(self, env, instance=None):
        """setup the Request attributes"""

        def new_subject():
            """generate a new subject ID"""
            return uuid.uuid4().hex

        def calc_domain(host):
            """calculate just the high level domain part of the host name

            remove the port and the www. if it exists

            >>> calc_domain('www.dsilabs.ca:8000')
            'dsilabs.ca'

            >>> calc_domain('test.dsilabs.ca:8000')
            'test.dsilabs.ca'

            """
            if host:
                return host.split(':')[0].split('www.')[-1:][0]
            return ''

        path = urllib.unquote(
            env.get('PATH_INFO', env.get('REQUEST_URI', '').split('?')[0])
        )
        current_route = path != '/' and path.split('/')[1:] or []
        cookies = zoom.cookies.get_cookies(env.get('HTTP_COOKIE'))

        module = env.get('wsgi.version', None) and 'wsgi' or 'cgi'

        if module == 'wsgi':
            server = env.get('HTTP_HOST').split(':')[0]
            home = os.getcwd()
        else:
            server = env.get('SERVER_NAME', 'localhost')
            home = os.path.dirname(env.get('SCRIPT_FILENAME', ''))

        instance = instance or get_parent_dir()
        root = os.path.join(instance, 'sites', server)

        # gather some commonly required environment variables
        attributes = dict(
            instance=instance,
            path=path,
            host=env.get('HTTP_HOST'),
            domain=calc_domain(env.get('HTTP_HOST')),
            uri=env.get('REQUEST_URI', 'index.py'),
            query=env.get('QUERY_STRING'),
            ip=env.get('REMOTE_ADDR'),  # deprecated
            ip_address=env.get('REMOTE_ADDR'),
            user=env.get('REMOTE_USER'),
            cookies=cookies,
            session_token=cookies.get(SESSION_COOKIE_NAME, None),
            subject=cookies.get(SUBJECT_COOKIE_NAME, new_subject()),
            port=env.get('SERVER_PORT'),
            root=root,
            server=server,
            script=env.get('SCRIPT_FILENAME'),
            home=home,
            agent=env.get('HTTP_USER_AGENT'),
            method=env.get('REQUEST_METHOD'),
            module=module,
            mode=env.get('mod_wsgi.process_group', None) \
            and 'daemon' or 'embedded',
            protocol=env.get('HTTPS', 'off') == 'on' and 'https' or 'http',
            referrer=env.get('HTTP_REFERER'),
            wsgi_version=env.get('wsgi.version'),
            wsgi_urlscheme=env.get('wsgi.urlscheme'),
            wsgi_multiprocess=env.get('wsgi.multiprocess'),
            wsgi_multithread=env.get('wsgi.multithread'),
            wsgi_filewrapper=env.get('wsgi.filewrapper'),
            wsgi_runonce=env.get('wsgi.runonce'),
            wsgi_errors=env.get('wsgi.errors'),
            wsgi_input=env.get('wsgi.input'),
            route=current_route,
            data=Webvars(env).__dict__,
            env=env
        )
        self.__dict__.update(attributes)

    def __str__(self):
        return '{\n%s\n}' % '\n'.join('  %s:%s' % (
            key,
            self.__dict__[key]) for key in self.__dict__
        )


# pylint: disable=invalid-name
request = Request()
webvars = Webvars()
data = request.data
route = request.route
