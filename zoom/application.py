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
import response
import ConfigParser
from system import system


def list_it(iter):
    return [a.strip() for a in iter.split(',') if a]

class Application:
    def __init__(self,name,path):
        self.name    = name
        self.get = self.read_config
        self.path    = path
        self.dir     = os.path.split(path)[0]
        #self.settings = system.settings.app(name)
        from zoom import manager, EntityStore
        from settings import Settings, ApplicationSettings
        self.settings = Settings(
            EntityStore(system.db, ApplicationSettings),
            self,
            name
          )
        get = self.settings.get
        self.theme   = get('theme')
        self.enabled = get('enabled')
        self.version = get('version')
        self.icon    = get('icon')
        self.title   = get('title') or name.capitalize()
        self.visible = get('visible')
        self.description = get('description', '')
        self.categories = list_it(get('categories',''))
        self.tags = list_it(get('tags',''))
        self.keywords = get('keywords','')
        self.in_development = get('in_development')

    def read_config(self,section,key,default=None):
        config_file1 = os.path.join(self.dir,'config.ini')
        config_file2 = os.path.join(os.path.split(self.dir)[0],'default.ini')
        config = ConfigParser.ConfigParser()
        try:
            config.read(config_file1)
            return config.get(section,key)
        except:
            try:
                config.read(config_file2)
                return config.get(section,key)
            except:
                if default != None:
                    return default
                else:
                    raise Exception('Config setting [{}]{} not found in {} or {}'.format(section, key, config_file1, config_file2))

    def run(self):
        t = self.dispatch()
        return self.respond(t)

    def dispatch(self):
        os.chdir(os.path.split(self.path)[0])
        import imp
        app = getattr(imp.load_source('app',self.path),'app')
        if app:
            return app()

    def respond(self,t):
        if t:
            if isinstance(t,response.Response):
                return t

            elif hasattr(t,'render') and t.render:
                result = t.render()
                return result

            elif type(t) == type([]):  # an array of string-like things (like WSGI)
                return dzresponse.HTMLResponse(''.join(t))

            elif isinstance(t, basestring):  # a string-like thing
                return response.HTMLResponse(t)

        return response.HTMLResponse('OK') #self.render_view()

    def __repr__(self):
        return repr('Application: %s' % self.__dict__)

