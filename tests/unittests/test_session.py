"""
    Test the session module
    
    Copyright (c) 2005-2016 Dynamic Solutions Inc. (support@dynamic-solutions.com)
    
    This file is part of DataZoomer.
"""

import os
import unittest
import Cookie
import time
import logging
import datetime

from zoom.request import request
from zoom.session import Session
from zoom.system import system

logger = logging.getLogger('zoom.session')

class TestRequest(unittest.TestCase):

    def test_session(self):
        system.setup(os.path.expanduser('~'))
        db = system.db

        session = Session(system)

        #Create new session
        id = session.new_session()
        self.assert_(id!='Session error')
        session.MyName = 'Test'
        session.Message = 'This is a test session'
        session.Number = 123

        session.save_session(id)
        try:
            cmd = 'select * from dz_sessions where sesskey=%s'
            q = db(cmd, id)
            self.assertEqual(len(list(q)), 1)

            # Create new session object
            session2 = Session(system)

            # Load previously created session
            request.session_token = id
            session2.load_session()
            self.assertEqual(session2.Number,123)
            self.assertEqual(session2.MyName,'Test')
            self.assertEqual(session2.Message,'This is a test session')

        finally:
            session.destroy_session(id)

            cmd = 'select * from dz_sessions where sesskey=%s'
            q = db(cmd, id)
            self.assertEqual(len(list(q)), 0)

