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

import ConfigParser, os.path


class Config:
    def __init__(self, dz_conf_path, server_name):

        def p(path, *a):
            return os.path.abspath(os.path.join(path,*a))

        def get_config(*a):
            pathname = os.path.join(*a)
            if os.path.exists(pathname):
                config = ConfigParser.ConfigParser()
                config.read(pathname)
                return config

        # read the system config file - one per instance
        self.instance_path = p(dz_conf_path)
        self.system_config = get_config(self.instance_path, 'dz.conf')
        if not self.system_config:
            raise Exception('Config file missing %s' % self.system_config_pathname)
        try:
            sites_path = self.system_config.get('sites', 'path', 'sites')
            self.sites_path = os.path.join(self.instance_path, sites_path)
        except:
            print 'Failed loading config file %s' % self.system_config_pathname
            raise            

        # read the default config file - one per environment
        self.config = get_config(sites_path, 'default', 'site.ini')
        if not self.config:
            # legacy location
            self.config = get_config(sites_path, 'default.conf')

        if server_name:
            self.site_config = get_config(sites_path, server_name, 'site.ini')
            if not self.site_config:
                # legacy location
                self.site_config = get_config(sites_path, server_name, 'site.conf')

        # read the site config file - one per site
        self.site_path = os.path.join(self.sites_path, server_name)


    def get(self, section, option, default=None):

        def missing_report(section, option):
            raise Exception('Unable to read [%s]%s from configs:\n%s\n%s' % (
                section, option,
                #self.system_config_pathname,
                os.path.join(self.sites_path, 'default.ini'),
                os.path.join(self.site_path, 'site.ini')))

        try:
            return self.site_config.get(section, option)
        except:            
            try:
                return self.config.get(section, option)

            except:
                if default != None:
                    return default
                else:
                    missing_report(section, option)


    def __str__(self):
        return '<Config: %s>' % repr([self.default_config_pathname, self.site_config_pathname])


if __name__ == '__main__':
    import doctest
    doctest.testmod()



