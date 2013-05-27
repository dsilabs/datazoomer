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
from application import Application
from system import system
from user import user
from request import route, webvars
import tools

DEFAULT_SYSTEM_APPS = ['register','profile','login','logout']
DEFAULT_MAIN_APPS   = ['home','apps','users','groups','info']

def get_apps(app_paths):
    apps = {}
    for path in app_paths:
        app_names = [name.lower() for name in os.listdir(path) if name[0]!='.' and os.path.isdir(os.path.join(path,name))]
        for name in app_names:
            if os.path.exists(os.path.join(path,name,'app.py')) and not name in apps:
                apps[name] = Application(name,os.path.join(path,name,'app.py'))
    return apps

class Manager:
    #def __init__(self):
    #    return self.setup()

    def setup(self):
        self.app_path  = system.config.get('apps','path')
        self.app_paths = [os.path.abspath(path) for path in self.app_path.split(';') if os.path.isdir(path)]
        self.apps = get_apps(self.app_paths)
        
    def get_app(self,name):
        return self.apps.get(name,None)
        
    def get_system_app_names(self):
        system_apps = tools.get_setting('system') or DEFAULT_SYSTEM_APPS
        return [app for app in system_apps if app in self.apps and app in user.apps]     

    def get_standard_app_names(self):
        system_apps = self.get_system_app_names()
        return [app for app in self.apps if app not in system_apps and app in user.apps]     

    def get_unregistered_app_names(self):
        system_apps = self.get_system_app_names()
        standard_apps = self.get_standard_app_names()
        return [app for app in self.apps if app not in system_apps+standard_apps and app in user.apps]     

    def get_main_app_names(self):
        set_menu = tools.get_setting('main')
        if set_menu == None:
            main_apps =  DEFAULT_MAIN_APPS
        else:
            main_apps = set_menu            
        return [app for app in main_apps if app in self.apps and app in user.apps]     

    def default_app_name(self):
        if user.is_anonymous:
            name = system.config.get('apps','index')
        else:
            name = system.config.get('apps','home')  
        if self.can_run(name):
            return name
        else:
            return system.config.get('apps','login','login')            
        
    def can_run(self,name):
        return name in self.apps and self.apps[name].enabled and (user.is_admin or name in user.apps)
        
    def requested_app_name(self):
        return route and route[0] or getattr(webvars,'app',None)


if __name__ != '__main__':
    manager = Manager()
else:
    #system.config.setup()
    manager = Manager()
    print manager.get_app('hello')

