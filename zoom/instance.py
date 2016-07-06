"""
    instance.py

    datazoomer instance
"""

import os

from zoom.utils import parents, locate_config, Config

class Site(object):

    def __init__(self, name):
        self.name = name


class Instance(object):
    """represents an installed DataZoomer instance

    Use for performing methods on an entire instance.
    """

    def __init__(self, name, path='.'):
        self.name = name
        self.config = Config(locate_config('dz.conf', path))

    @property
    def sites_path(self):
        """the path to the sites of the instance"""
        return self.config.get('sites', 'path')

    @property
    def path(self):
        """the path of the instance"""
        path, _ = os.path.split(self.sites_path)
        return path

    @property
    def sites(self):
        """a list of sites for the instance"""
        listdir = os.listdir
        isdir = os.path.isdir
        join = os.path.join
        path = self.sites_path
        return [Site(name) for name in listdir(path) if isdir(join(path, name))]

    def run(self, *jobs):
        """run jobs on an entire instance"""
        logger = logging.getLogger(self.name)
        for site in self.sites:
            try:
                zoom.system.setup(self.path, site.name)
            except Exception, e:
                logger.warning(str(e))
                logger.warning('unable to setup {}'.format(site.name))
                continue
            if zoom.system.background:
                for job in jobs:
                    logger.debug('running {}.{} for {}'.format(self.name,
                                                               job.__name__,
                                                               site.name))
                    job()

