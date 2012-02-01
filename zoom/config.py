"""
    Config

    Accesses configuration settings from a main configuration and
    a site specific configuration file.  This allows a main config
    file for most settings with the ability to override for
    site specific settings.

    >>> config = Config()
    >>> config.setup('../../test','localhost')
    >>> config.get('site','name')
    'Zoom'

    >>> config.get('site','title')
    'Zoom Platform'

"""

import os
import ConfigParser

class Config:

    def setup(self,instance_path,server_name):
        system_config_pathname = os.path.join(instance_path,'zoom.ini')
        if not os.path.exists(system_config_pathname):
            raise Exception('Missing config file %s (%s)' % 
                    (repr(system_config_pathname),repr(os.path.abspath(system_config_pathname))))

        # Read the instance config (defaults)
        self.system_config_pathname = os.path.abspath(system_config_pathname)
        self.system_config = ConfigParser.ConfigParser()
        self.system_config.read(system_config_pathname)

        # Read the site config (overrides defaults)
        system_path, filename = os.path.split(self.system_config_pathname)
        self.server_name = server_name.lower()
        site_directory = self.server_name.strip('www.')
        self.site_path = os.path.join(system_path,site_directory)
        self.site_config_pathname = os.path.join(system_path,site_directory,'config.ini')
        self.site_config = ConfigParser.ConfigParser()
        self.site_config.read(self.site_config_pathname)

    def get(self,section,option,default=None):
        try:
            return self.site_config.get(section,option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            try:
                return self.system_config.get(section,option)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                if default != None:
                    return default
                else:
                    raise
        except:
            raise

config = Config()

if __name__ == '__main__':
    import doctest
    doctest.testmod()

    



