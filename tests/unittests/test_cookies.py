"""
    Test the request module

    Copyright (c) 2005-2012 Dynamic Solutions Inc.
    support@dynamic-solutions.com

    This file is part of DataZoomer.
"""

import unittest
import Cookie
import logging

from zoom.cookies import (
    make_cookie,
    add_value,
    SESSION_COOKIE_NAME,
    SUBJECT_COOKIE_NAME,
)



class TestRequest(unittest.TestCase): #pylint: disable=R0904
    """test system cookies"""

    def test_create_cookie(self):
        """
        Create a secure session and subject cookie
        """
        logger = logging.getLogger('zoom.cookies')

        cookie = make_cookie()
        add_value(cookie, SESSION_COOKIE_NAME, 'mysession', 60, True)
        add_value(cookie, SUBJECT_COOKIE_NAME, 'mysubject', 60, True)
        logger.info(str(cookie))

        cookie2 = Cookie.SimpleCookie()
        cookie2[SESSION_COOKIE_NAME] = 'mysession'
        cookie2[SESSION_COOKIE_NAME]['httponly'] = True
        cookie2[SESSION_COOKIE_NAME]['expires'] = 60
        cookie2[SESSION_COOKIE_NAME]['secure'] = True
        cookie2[SUBJECT_COOKIE_NAME] = 'mysubject'
        cookie2[SUBJECT_COOKIE_NAME]['httponly'] = True
        cookie2[SUBJECT_COOKIE_NAME]['expires'] = 60
        cookie2[SUBJECT_COOKIE_NAME]['secure'] = True
        logger.info(str(cookie2))

        self.assertEqual(str(cookie), str(cookie2))

    def test_create_not_secure_cookie(self):
        """
        Create a non-secure session and subject cookie
        """
        logger = logging.getLogger('zoom.cookies')

        cookie = make_cookie()
        add_value(cookie, SESSION_COOKIE_NAME, 'mysession', 60, False)
        add_value(cookie, SUBJECT_COOKIE_NAME, 'mysubject', 60, False)
        logger.info(str(cookie))

        cookie2 = Cookie.SimpleCookie()
        cookie2[SESSION_COOKIE_NAME] = 'mysession'
        cookie2[SESSION_COOKIE_NAME]['httponly'] = True
        cookie2[SESSION_COOKIE_NAME]['expires'] = 60
        cookie2[SUBJECT_COOKIE_NAME] = 'mysubject'
        cookie2[SUBJECT_COOKIE_NAME]['httponly'] = True
        cookie2[SUBJECT_COOKIE_NAME]['expires'] = 60
        logger.info(str(cookie2))

        self.assertEqual(str(cookie), str(cookie2))


