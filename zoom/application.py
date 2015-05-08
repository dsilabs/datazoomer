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

class Application:
    def __init__(self,name,path):
        self.name    = name
        self.path    = path
        self.dir     = os.path.split(path)[0]
        self.theme   = self.read_config('settings', 'theme', '') or None
        self.enabled = True
        self.version = None
        self.icon    = self.read_config('settings','icon',system.config.get('apps','icon','blank_doc'))
        self.title   = self.read_config('settings','title',name.capitalize())
        self.visible = self.read_config('settings','visible',True) not in ['no', 'n', False, '0']
        self.description = self.read_config('settings','description','')
        self.categories = [a.strip() for a in self.read_config('settings','categories','').split(',') if a]
        self.tags = [a.strip() for a in self.read_config('settings','tags','').split(',') if a]
        self.keywords = self.read_config('settings','keywords','')
        self.in_development = self.read_config('settings', 'in_development', False)

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

            elif type(t) == type(""):  # a string-like thing
                return response.HTMLResponse(t)

        return response.HTMLResponse('OK') #self.render_view()

    def __repr__(self):
        return repr('Application: %s' % self.__dict__)

