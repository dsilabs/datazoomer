# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import cgi
import urllib
import uuid

from types import ListType

import zoom.cookies


SESSION_COOKIE_NAME = zoom.cookies.SESSION_COOKIE_NAME
SUBJECT_COOKIE_NAME = zoom.cookies.SUBJECT_COOKIE_NAME


def new_subject():
    return uuid.uuid4().hex


def calc_domain(host):
    if host:
        return host.split(':')[-1:][0].split('www.')[-1:][0]
    return ''


class Webvars(object):
    def __init__(self, env=os.environ):
        """gather query fields"""

        # switch to binary mode on windows systems
        try:
            import msvcrt,os
            msvcrt.setmode( 0, os.O_BINARY ) # stdin  = 0
            msvcrt.setmode( 1, os.O_BINARY ) # stdout = 1
        except ImportError:
            pass

        if env.get('REQUEST_METHOD','GET').upper() in ['GET']:
            cgi_fields = cgi.FieldStorage(environ=env,keep_blank_values=1)
        else:
            cgi_fields = cgi.FieldStorage(fp=sys.stdin, environ=env, keep_blank_values=1)
        webvars = {}
        for key in cgi_fields.keys():

            # ignore legacy setup
            if key == '_route':
                continue

            if type(cgi_fields[key])==ListType:
                webvars[key] = [item.value for item in cgi_fields[key]]
            elif cgi_fields[key].filename:
                webvars[key] = cgi_fields[key]
            else:
                webvars[key] = cgi_fields[key].value
        self.__dict__ = webvars        
        
        def __getattr__(self,name):
            try:
                self.__dict__[name]
            except:
                raise AttributeError 
                
    def __getattr__(self,name):
        return '' # return blank for missing attributes                
                
    def __str__(self):
        return repr(self.__dict__)

    def __repr__(self):
        return str(self)


class Request(object):
    def __init__(self, env=os.environ):

        path = urllib.quote(env.get('PATH_INFO', env.get('REQUEST_URI','').split('?')[0]))
        route = path != '/' and path.split('/')[1:] or []
        cookies = zoom.cookies.get_cookies(env.get('HTTP_COOKIE'))
        self.ip_address = None
        self.session_token = None
        self.server = None
        self.route = None

        # gather some commonly required environment variables
        request = dict(
            path = path,
            host = env.get('HTTP_HOST'),
            domain = calc_domain(env.get('HTTP_HOST')),
            uri = env.get('REQUEST_URI','index.py'),
            query = env.get('QUERY_STRING'),
            ip = env.get('REMOTE_ADDR'), # deprecated
            ip_address = env.get('REMOTE_ADDR'),
            user = env.get('REMOTE_USER'),
            cookies = cookies,
            session_token = cookies.get(SESSION_COOKIE_NAME, None),
            subject = cookies.get(SUBJECT_COOKIE_NAME, new_subject()),
            port = env.get('SERVER_PORT'),
            server = env.get('SERVER_NAME','localhost'),
            script = env.get('SCRIPT_FILENAME'),
            home = os.path.dirname(env.get('SCRIPT_FILENAME','')),
            agent  = env.get('HTTP_USER_AGENT'),
            method = env.get('REQUEST_METHOD'),
            module = env.get('wsgi.version',None) and 'wsgi' or 'cgi',
            mode = env.get('mod_wsgi.process_group', None) and 'daemon' or 'embedded',
            protocol = env.get('HTTPS','off') == 'on' and 'https' or 'http',
            referrer = env.get('HTTP_REFERER'),
            wsgi_version = env.get('wsgi.version'),
            wsgi_urlscheme = env.get('wsgi.urlscheme'),
            wsgi_multiprocess = env.get('wsgi.multiprocess'),
            wsgi_multithread = env.get('wsgi.multithread'),
            wsgi_filewrapper = env.get('wsgi.filewrapper'),
            wsgi_runonce = env.get('wsgi.runonce'),
            wsgi_errors = env.get('wsgi.errors'),
            wsgi_input = env.get('wsgi.input'),
            route = route,
            data = Webvars(env).__dict__,
            env = env
            )
        self.__dict__ = request

    def __str__(self):
        return '{\n%s\n}' % '\n'.join('  %s:%s' % 
                (key,self.__dict__[key]) for key in self.__dict__)


request = Request()
webvars = Webvars()
data    = request.data
route   = request.route

