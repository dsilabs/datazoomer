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

"""Application module"""

import os
import imp
import ConfigParser

from . import response
from zoom.system import system
from zoom.settings import NEGATIVE

DEFAULT_SETTINGS = dict(
    title='',
    icon='blank_doc',
    version=0.0,
    enabled=True,
    visible=True,
    theme='',
    description='',
    categories='',
    tags='',
    keywords='',
    in_development=False,
    app_menu_size=5,
)


def list_it(iterable):
    """create list of stripped item from comma delimited string"""
    return [a.strip() for a in iterable.split(',') if a]


def respond(content):
    """construct a response"""
    if content:
        if isinstance(content, response.Response):
            return content

        elif hasattr(content, 'render') and content.render:
            result = content.render()
            return result

        elif type(content) == type([]):
            # an array of string-like things (like WSGI)
            return response.HTMLResponse(''.join(content))

        elif isinstance(content, basestring):
            # a string-like thing
            return response.HTMLResponse(content)

    return response.HTMLResponse('OK') #self.render_view()

#config_parser = ConfigParser.ConfigParser()

class Application(object):
    """Application"""

    # pylint: disable=too-many-instance-attributes
    # It's reasonable in this case.


    def __init__(self, name, path):
        self.name = name
        self.get = self.read_config # remove?
        self.path = path
        self.dir = os.path.split(path)[0]
        self.url = '/' + name
        self.config_parser = ConfigParser.ConfigParser()

        config = self.get_config(DEFAULT_SETTINGS)
        self.settings = system.settings.app_settings(self, config)
        get = self.settings.get

        self.theme = get('theme')
        self.enabled = get('enabled')
        self.version = get('version')
        self.icon = get('icon')
        self.title = get('title') or name.capitalize()
        self.visible = get('visible') not in NEGATIVE
        self.description = get('description', '')
        self.categories = list_it(get('categories', ''))
        self.tags = list_it(get('tags', ''))
        self.keywords = get('keywords', '')
        self.in_development = get('in_development')
        self.app_menu_size = get('app_menu_size')

        self.helpers = {}

    def get_settings(self):
        """
        get settings specific to this application
        """
        negative = ['NO', 'No', 'nO', 'no', 'N', 'n', False, '0', 0]

        config_file1 = os.path.join(self.dir, 'config.ini')
        config1 = ConfigParser.ConfigParser()
        config1.read(config_file1)

        config_file2 = os.path.join(os.path.split(self.dir)[0], 'default.ini')
        config2 = ConfigParser.ConfigParser()
        config2.read(config_file2)

        result = {}
        for key, default in DEFAULT_SETTINGS.items():
            try:
                value = config1.get('settings', key)
            except:
                try:
                    value = config2.get('settings', key)
                except:
                    value = default
            if type(default) == bool:
                value = value not in negative
            result[key] = value
        return result

    def get_config(self, default=None):

        def as_dict(config):
            """
            Converts a ConfigParser object into a dictionary.
            """
            the_dict = {}
            for section in config.sections():
                for key, val in config.items(section):
                    #the_dict['.'.join([self.name, key])] = val
                    the_dict[key] = val
            return the_dict

        def get_config(pathname):
            self.config_parser.read(pathname)
            return as_dict(self.config_parser)

        join = os.path.join
        split = os.path.split

        local_settings_config_file = join(self.dir, 'config.ini')
        shared_settings_config_file = join(split(self.dir)[0], 'default.ini')
        system_settings_config_file = join(split(self.dir)[0], '..', '..', 'default.ini')

        local_settings = get_config(local_settings_config_file)
        shared_settings = get_config(shared_settings_config_file)
        system_settings = get_config(system_settings_config_file)

        result = {}
        result.update(default or {})
        result.update(system_settings)
        result.update(shared_settings)
        result.update(local_settings)
        return result

    def read_config(self, section, key, default=None):
        """read config file information"""
        config_file1 = os.path.join(self.dir, 'config.ini')
        config_file2 = os.path.join(os.path.split(self.dir)[0], 'default.ini')
        config_file3 = os.path.join(os.path.split(self.dir)[0], '..', '..', 'default.ini')

        config = ConfigParser.ConfigParser()
        try:
            config.read(config_file1)
            return config.get(section, key)
        except:
            try:
                config.read(config_file2)
                return config.get(section, key)
            except:
                try:
                    config.read(config_file3)
                    return config.get(section, key)
                except:
                    if default != None:
                        return default
                    else:
                        tpl = 'Config setting [{}]{} not found in {} or {} or {}'
                        msg = tpl.format(section, key, config_file1, config_file2, config_file3)
                        raise Exception(msg)

    def run(self, request):
        """run an app"""
        result = self.dispatch(request)
        return respond(result)

    def dispatch(self, request):
        """dispatch request to an app"""
        os.chdir(os.path.split(self.path)[0])
        app = getattr(imp.load_source('app', self.path), 'app')
        if app:
            try:
                return app(request)
            except TypeError as error:
                if 'takes no arguments' in str(error):
                    # legacy app
                    return app()
                raise

    def initialize(self, request):
        name = 'initialize.py'
        pathname = os.path.join(os.path.split(self.path)[0], name)
        if os.path.exists(pathname):
            app = getattr(imp.load_source('main', pathname), 'main')
            if app:
                app(request)

    def __repr__(self):
        return repr('Application: %s' % self.__dict__)

