"""Test session module"""

from zoom.session import *

import unittest
import test_database

class SessionTest(unittest.TestCase):


    def setUp(self):
        # test database
        self.db = db = test_database.test_database()

        # create session object
        session = Session()
        session.create_sessions_table(db)


    def test(self):

        db = self.db

        # create session object
        session = Session()

        # create a new session
        session.new()
        session.username = 'jsmith'
        session.number = 123
        sid = session.save(db)

        # load existing session
        new_session = Session()
        new_session.load(db, sid)
        self.assertEqual(new_session.username, 'jsmith')
        self.assertEqual(new_session.number, 123)

        # kill the session
        new_session.kill() 
