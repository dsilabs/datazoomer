"""
    Test the request module
    
    Copyright (c) 2005-2012 Dynamic Solutions Inc. (support@dynamic-solutions.com)
    
    This file is part of DataZoomer.
"""

import os
import unittest
import Cookie
import time
import logging
import datetime

from zoom.cookies import SUBJECT_COOKIE_NAME, make_cookie, add_value, get_value
from zoom.request import Request

logger = logging.getLogger('zoom.request')

class TestRequest(unittest.TestCase):

    def test_subject_cookie(self):
        # the subject token is extracted from the cookie and 
        # made available as part of the request.
        cookie = make_cookie()
        add_value(cookie, SUBJECT_COOKIE_NAME, 'mycookie', 60, True)

        env = {'HTTP_COOKIE': get_value(cookie)}
        request = Request(env)
        self.assertEqual(request.subject, 'mycookie')

    def test_expired_subject_cookie(self):
        # if the subject cookie has expired the browser does not send it
        # so the request module makes a new subject token.
        env = {}
        request = Request(env)
        self.assertNotEqual(request.subject, 'mycookie')
        assert len(request.subject) == 32

