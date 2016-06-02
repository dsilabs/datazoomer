"""
    Test the user module

    Copyright (c) 2005-2012 Dynamic Solutions Inc. (support@dynamic-solutions.com)

    This file is part of DataZoomer.
"""

import os, unittest

import MySQLdb

from zoom.db import Database
from zoom.system import system
from zoom.user import authenticate
from zoom.users import UserStore
from zoom.database import Database as LegacyDatabase


class TestUser(unittest.TestCase):

    def setUp(self):
        params = dict(
            host='database',
            user='testuser',
            passwd='password',
            db='test',
        )
        self.drop_cmd = "DROP TABLE IF EXISTS `dz_users`"
        self.db = Database(MySQLdb.Connect, **params)
        self.db.autocommit(1)
        self.db(self.drop_cmd)
        self.db("""
CREATE TABLE `dz_users` (
  `userid` int(5) NOT NULL auto_increment,
  `loginid` char(50) default NULL,
  `password` varchar(125) default NULL,
  `firstname` char(40) default NULL,
  `lastname` char(40) default NULL,
  `email` char(60) default NULL,
  `phone` char(30) default NULL,
  `fax` char(30) default NULL,
  `dtupd` datetime default NULL,
  `dtadd` datetime default NULL,
  `status` char(1) default NULL,
  PRIMARY KEY  (`userid`),
  UNIQUE KEY `userid` (`loginid`),
  KEY `userid_2` (`loginid`),
  KEY `email` (`email`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
""")
        self.db("""
insert into dz_users
    (loginid, password, firstname, lastname, status, dtupd, dtadd)
    values ('admin', old_password('admin'), 'admin', 'admin', 'A', now(), now())
        """)

        # setup the system and install our own test database
        system.setup(os.path.expanduser('~'))
        system.db = self.db
        system.users = UserStore(self.db)   # for authenticate method
        system.database = LegacyDatabase(MySQLdb.Connect, **params) # used by user.update_user, called by authenticate method
        system.database.autocommit(1)

    def tearDown(self):
        self.db(self.drop_cmd)
        self.db.close()

    def test_update_hash_scheme(self):
        old_hash = list(self.db('select password from dz_users'))[0][0]
        authenticated = authenticate('admin', 'admin')
        assert authenticated == True
        new_hash = list(self.db('select password from dz_users'))[0][0]
        assert old_hash <> new_hash
        assert len(old_hash) < len(new_hash)
        assert new_hash.startswith('$bcrypt')
