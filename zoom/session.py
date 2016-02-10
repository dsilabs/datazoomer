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
import sys
import random
import pickle
import os
import Cookie
import uuid

from request import request


class SessionExpiredException(Exception): pass

session_life = 60 # time in minutes


class Session(object):
    tablename = 'dz_sessions'

    def __init__(self, system):
        self._system = system


    def __repr__(self):
        return ', '.join(['%s="%s"' % (k,v) for (k,v) in zip(self.__dict__,self.__dict__.values()) if k[0]!='_'])


    def __str__(self):
        return repr(self)


    def gc(self):
        if self._system.config.get('session', 'destroy', True):
            cmd = 'DELETE FROM %s WHERE (expiry < %s) or (status="D")' % (self.tablename,'%s')
            db = self._system.database
            db(cmd,time.time())


    def new_session(self, timeout=session_life):
        def trysid(sid):
            db = self._system.database
            cmd = "INSERT INTO %s VALUES (%s,%s,'A','')" % (self.tablename,'%s','%s')
            try:
                db(cmd,newsid,expiry)
                return 1
            except:
                raise

        def make_session_id(st='nuthin'):
            return uuid.uuid4().get_hex()

        self.gc()

        crazyloop = 10
        expiry = time.time() + timeout * 60
        newsid = make_session_id()
        success = trysid(newsid)

        # Try again in the unlikely event that the generated session id is being used
        while not success and crazyloop > 0:
            newsid = make_session_id()
            success = trysid(newsid)
            crazyloop -= 1

        if success:
            self.sid = newsid
            self.ip = request.ip
            return newsid
        else:
            raise Exception,'Session error'


    def load_session(self):

        def load_existing(sid):
            db = self._system.database
            cmd = "SELECT * FROM %s WHERE sesskey=%s AND expiry>%s and status='A'" %(self.tablename,'%s','%s')
            curs = db(cmd, sid, time.time())
            if len(curs):
                try:
                    values = (curs[0].VALUE and pickle.loads(curs[0].VALUE) or {})
                except:
                    values = {}                
                for key in values:
                    self.__dict__[key] = values[key]
                return True

        self.sid = sid = request.session_token
        valid_sid = sid and len(sid)==32 and self.sid.isalnum()

        if not (valid_sid and load_existing(sid) and self.ip==request.ip):
            self.new_session()


    def save_session(self, response, sid=None, timeout=session_life):
        sid = sid or self.sid
        timeout_in_seconds = self.__dict__.get('lifetime', timeout * 60)
        expiry = time.time() + timeout_in_seconds
        values = {}
        for key in self.__dict__.keys():
            if key[0] != '_':
                values[key] = self.__dict__[key]
        value = pickle.dumps(values)
        cmd = 'UPDATE %s SET expiry=%s, value=%s WHERE sesskey=%s' % (self.tablename,'%s','%s','%s')
        db = self._system.database
        curs = db(cmd,expiry,value,sid)


    def destroy_session(self, sid=None):
        sid = sid or self.sid

        system = self._system
        self.__dict__.clear()
        self._system = system

        db = self._system.database
        
        if self._system.config.get('sessions', 'destroy', True):
            cmd = 'delete from %s where sesskey=%s' % (self.tablename, '%s')
            db(cmd, sid)
        else:
            cmd = 'update %s set expiry=%s, status="D" where sesskey=%s' % (self.tablename, '%s', '%s')
            db(cmd, time.time(), sid)


    def __getattr__(self,name):
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            return None

