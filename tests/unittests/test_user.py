"""
    Test the user module

    Copyright (c) 2005-2012 Dynamic Solutions Inc. (support@dynamic-solutions.com)

    This file is part of DataZoomer.
"""

import os, unittest
import datetime

import MySQLdb

from zoom.db import Database
from zoom.system import system
from zoom.user import (
    authenticate,
    activate_user,
    deactivate_user,
    User as OldUser, 
    UnauthorizedException,
)
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

        now = datetime.datetime(2016, 10, 11, 13, 12, 1)

        self.db = Database(MySQLdb.Connect, **params)
        self.db.autocommit(1)

        # Setup users table
        # -------------------------------------------------
        self.db("DROP TABLE IF EXISTS `dz_users`")
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
        records = [
            ('admin', 'admin', 'Admin', 'User', 'A', now, now),
            ('manager1', 'pass1', 'Manager', 'One', 'A', now, now),
            ('user1', 'pass2', 'User', 'One', 'A', now, now),
            ('user2', 'pass3', 'User', 'Two', 'A', now, now),
        ]
        self.db.execute_many("""
            insert into dz_users
                (loginid, password, firstname, lastname, status, dtupd, dtadd)
                values 
                (%s, old_password(%s), %s, %s, %s, %s, %s)
        """, records)

        # Setup groups table
        # -------------------------------------------------
        self.db("DROP TABLE IF EXISTS `dz_groups`")
        self.db("""
                CREATE TABLE `dz_groups` (
                  `groupid` int(11) NOT NULL auto_increment,
                  `type` char(1) default NULL,
                  `name` char(20) default NULL,
                  `descr` char(60) default NULL,
                  `admin` char(20) default NULL,
                  PRIMARY KEY  (`groupid`),
                  UNIQUE KEY `name` (`name`),
                  KEY `name_2` (`name`)
               ) ENGINE=MyISAM DEFAULT CHARSET=utf8;
        """)
        records = [
            (1, 'U','administrators','System Administrators','administrators'),
            (2, 'U','users','Registered Users','administrators'),
            (3, 'U','guests','Guests','administrators'),
            (4, 'U','everyone','All users including guests','administrators'),
            (5, 'U','managers','Site Content Managers','administrators'),
        ]
        self.db.execute_many("""
            insert into dz_groups values (%s, %s, %s, %s, %s)
        """, records)

        # Setup members table
        # -------------------------------------------------
        self.db("DROP TABLE IF EXISTS `dz_members`")
        self.db("""
                CREATE TABLE `dz_members` (
                  `userid` int(11) default NULL,
                  `groupid` int(11) default NULL,
                  UNIQUE KEY `contactid_2` (`userid`,`groupid`),
                  KEY `contactid` (`userid`),
                  KEY `groupid` (`groupid`)
               ) ENGINE=MyISAM DEFAULT CHARSET=utf8;
        """)
        records = [
            # admins
            (1, 1),

            # users
            (1, 2),
            (2, 2),
            (3, 2),
            (4, 2),

            # managers
            (2, 5),
        ]
        self.db.execute_many("""
            insert into dz_members values (%s, %s)
        """, records)

        # Setup subgroups table
        # -------------------------------------------------
        self.db("DROP TABLE IF EXISTS `dz_subgroups`")
        self.db("""
                CREATE TABLE `dz_subgroups` (
                  `groupid` int(11) default NULL,
                  `subgroupid` int(11) default NULL,
                  UNIQUE KEY `groupid_2` (`groupid`,`subgroupid`),
                  KEY `groupid` (`groupid`),
                  KEY `subgroupid` (`subgroupid`)
               ) ENGINE=MyISAM DEFAULT CHARSET=utf8;
        """)
        records = [
            # admin
            (2, 1), # admins are subgroup of users
            (5, 1), # admins are subgroup of managers

            # users 
            (4, 2), # users are subgroup of everyone

            # guests 
            (4, 3), # guests are subgroup of everyone

            # Managers
            (2, 5), # managers are subgroup of users
        ]
        self.db.execute_many("""
            insert into dz_subgroups values (%s, %s)
        """, records)

        # setup the system and install our own test database
        system.setup(os.path.expanduser('~'))
        system.db = self.db
        system.users = UserStore(self.db)   # for authenticate method
        system.database = LegacyDatabase(MySQLdb.Connect, **params) # used by user.update_user, called by authenticate method
        system.database.autocommit(1)

        print self.db('select * from dz_users')
        print self.db('select * from dz_groups')
        print self.db('select * from dz_subgroups')
        print self.db('select * from dz_members')

    def tearDown(self):
        for name in ['dz_users','dz_groups', 'dz_subgroups', 'dz_memmbers']:
            self.db("DROP TABLE IF EXISTS `{}`".format(name))
        self.db.close()

    def test_update_hash_scheme(self):
        old_hash = list(self.db('select password from dz_users'))[0][0]
        authenticated = authenticate('admin', 'admin')
        assert authenticated == True
        new_hash = list(self.db('select password from dz_users'))[0][0]
        assert old_hash <> new_hash
        assert len(old_hash) < len(new_hash)
        assert new_hash.startswith('$bcrypt')


class TestOldUser(TestUser):
    """tests legacy user module"""

    def test_get_user(self):
        user = OldUser('admin')
        self.assertEqual(user.user_id, 1L)
        self.assertEqual(user.login_id, 'admin')
        self.assertEqual(user.username, 'admin')
        self.assertEqual(user.first_name, 'Admin')
        self.assertEqual(user.last_name, 'User')
        user = OldUser('user1')
        self.assertEqual(user.user_id, 3L)

    def test_get_user_case_insensitive(self):
        user = OldUser('Admin')
        self.assertEqual(user.user_id, 1L)
        self.assertEqual(user.login_id, 'admin')
        self.assertEqual(user.username, 'admin')
        self.assertEqual(user.first_name, 'Admin')

    def test_user_groups(self):
        user = OldUser('admin')
        self.assertEqual(user.groups, [
            'administrators',
            'users',
            'everyone',
            'managers'
        ])
        user = OldUser('user1')
        self.assertEqual(user.groups, ['users', 'everyone'])

    def test_user_is_member(self):
        user = OldUser('admin')
        self.assertTrue(user.is_member('administrators'))
        self.assertTrue(user.is_member('users'))
        self.assertFalse(user.is_member('notagroup'))
        user = OldUser('user1')
        self.assertTrue(user.is_member('users'))
        self.assertFalse(user.is_member('administrators'))
        self.assertFalse(user.is_member('notagroup'))

    def test_user_link(self):
        user = OldUser('user1')
        self.assertEqual(user.user_id, 3L)
        print user.user_id
        self.assertEqual(user.link, '<a href="/noapp/3">user1</a>')

    def test_user_is_activate(self):
        user = OldUser('user1')
        self.assertEqual(user.status, 'A')
        deactivate_user(user.username)
        user = OldUser('user1')
        self.assertEqual(user.status, 'I')
        activate_user(user.username)
        user = OldUser('user1')
        self.assertEqual(user.status, 'A')

    def test_user_is_disabled(self):
        user = OldUser('user1')
        self.assertEqual(user.is_disabled, False)
        user.status = 'D'
        self.assertEqual(user.is_disabled, True)

    def test_user_can(self):
        class MyObject(object):
            def allows(self, user, action):
                return action == 'read' or user.username == 'admin'
        obj = MyObject()
        user = OldUser('user1')
        self.assertTrue(user.can('read', obj))
        self.assertFalse(user.can('edit', obj))
        user = OldUser('admin')
        self.assertTrue(user.can('read', obj))
        self.assertTrue(user.can('edit', obj))

    def test_user_authorize(self):
        class MyObject(object):
            def allows(self, user, action):
                return action == 'read' or user.username == 'admin'
        obj = MyObject()

        user = OldUser('user1')
        user.authorize('read', obj)
        with self.assertRaises(UnauthorizedException):
            user.authorize('edit', obj)

        user = OldUser('admin')
        user.authorize('read', obj)
        user.authorize('edit', obj)


