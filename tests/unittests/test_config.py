"""
    Test the config module

    Copyright (c) 2005-2016 Dynamic Solutions Inc.
    support@dynamic-solutions.com

    This file is part of DataZoomer.
"""

from os.path import join, split, abspath, exists
import unittest
import logging

from zoom.config import Config


class TestConfig(unittest.TestCase): #pylint: disable=R0904
    """test config module"""

    def test_create(self):
        """test creating and using a config object"""

        def find_config(directory):
            """climb the directory tree looking for config"""
            pathname = join(directory, 'dz.conf')
            if exists(pathname):
                return directory
            parent, _ = split(directory)
            if parent != '/':
                return find_config(parent)

        logger = logging.getLogger('zoom.unittest.test_config')
        config_location = find_config(abspath('.'))
        standard_config_file = join(split(__file__)[0], config_location)
        config = Config(standard_config_file, 'localhost')
        logger.debug(config_location)
        instance_root = abspath(join(split(__file__)[0], config_location))
        assert config
        self.assertEqual(config.sites_path, join(instance_root, 'web', 'sites'))
        self.assertEqual(config.site_path,
                         join(instance_root, 'web', 'sites', 'localhost'))

