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

"""Stores session variables"""


import time
import pickle
import uuid

from zoom.request import request


class SessionExpiredException(Exception):
    """exception to raise when a session has expired
    """
    pass

SESSION_LIFE = 60 # time in minutes


class Session(object):
    """manage user session data"""

    def __init__(self, system):
        self._system = system
        self.ip_address = None

    def __repr__(self):
        """
            >>> session = Session(None)
            >>> session.name = 'test'
            >>> session.age = 1
            >>> repr(session)
            "<Session: {'age': 1, 'ip_address': None, 'name': 'test'}>"
        """
        printables = dict(
            [(k, v) for k, v in self.__dict__.items() if not k.startswith('_')]
        )
        return '<Session: {}>'.format(repr(printables))


    def __str__(self):
        return repr(self)


    def collect_garbage(self):
        """delete unused session records"""
        if self._system.config.get('session', 'destroy', True):
            cmd = 'delete from dz_sessions where (expiry < %s) or (status="D")'
            self._system.db(cmd, time.time())


    def new_session(self, timeout=SESSION_LIFE):
        """create a new session"""
        def trysid(sid):
            """create and test the availability of a session id"""
            database = self._system.database
            cmd = "insert into dz_sessions values (%s, %s, 'A', '')"
            try:
                database(cmd, sid, expiry)
                return 1
            except:
                raise

        def make_session_id():
            """make a new session id"""
            return uuid.uuid4().get_hex()

        self.collect_garbage()

        crazyloop = 10
        expiry = time.time() + timeout * 60
        newsid = make_session_id()
        success = trysid(newsid)

        # Try again in the unlikely event that the generated
        # session id is being used
        while not success and crazyloop > 0:
            newsid = make_session_id()
            success = trysid(newsid)
            crazyloop -= 1

        if success:
            self.sid = newsid
            self.ip_address = request.ip_address
            return newsid
        else:
            raise Exception('Session error')


    def load_session(self):
        """load a session"""

        def load_existing(sid):
            """load an existing session"""
            database = self._system.database
            cmd = """
            select *
            from dz_sessions
            where sesskey=%s and expiry>%s and status='A'"""
            curs = database(cmd, sid, time.time())
            if len(curs):
                try:
                    values = (curs[0].VALUE and \
                              pickle.loads(curs[0].VALUE) or {})
                except:
                    values = {}
                for key in values:
                    self.__dict__[key] = values[key]
                return True

        self.sid = sid = request.session_token
        valid_sid = sid and len(sid) == 32 and self.sid.isalnum()

        if not (valid_sid and load_existing(sid) and \
                self.ip_address == request.ip_address):
            self.new_session()


    def save_session(self, sid=None, timeout=SESSION_LIFE):
        """save a session"""
        sid = sid or self.sid

        # using __dict__ method because getattr is overridden
        timeout_in_seconds = self.__dict__.get('lifetime', timeout * 60)

        expiry = time.time() + timeout_in_seconds
        values = {}
        for key in self.__dict__.keys():
            if key[0] != '_':
                values[key] = self.__dict__[key]
        value = pickle.dumps(values)
        cmd = 'update dz_sessions set expiry=%s, value=%s where sesskey=%s'
        database = self._system.database
        database(cmd, expiry, value, sid)
        return timeout_in_seconds


    def destroy_session(self, sid=None):
        """destroy a session"""
        sid = sid or self.sid
        system = self._system
        try:
            self.__dict__.clear()
        finally:
            self._system = system

        if self._system.config.get('sessions', 'destroy', True):
            cmd = 'delete from dz_sessions where sesskey=%s'
            self._system.db(cmd, sid)
        else:
            cmd = """
            update dz_sessions
            set expiry=%s, status="D"
            where sesskey=%s"""
            self._system.db(cmd, time.time(), sid)


    def __getattr__(self, name):
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            return None
