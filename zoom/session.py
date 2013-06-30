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

from system import system
from request import request, webvars
from tools import db

SESSION_COOKIE_NAME = 'dz4sid'
SUBJECT_COOKIE_NAME = 'dz4sub'

class SessionExpiredException(Exception): pass

sessionLife = 60 # time in minutes

def get_session_cookie():
    return get_cookie(SESSION_COOKIE_NAME)

def get_subject():
    value = get_cookie(SUBJECT_COOKIE_NAME)
    if not value or value == 'None':
        return uuid.uuid4().hex
    return value

def get_cookie(name):
    raw_cookie = os.environ.get("HTTP_COOKIE", "")
    cookie = Cookie.SimpleCookie(raw_cookie)
    try:
        value = cookie[name].value
    except KeyError:
        value = None
    return value

def set_session_cookie(response, sid, host, lifespan, secure=True):
    cookie = Cookie.SimpleCookie()

    cookie[SESSION_COOKIE_NAME] = sid
    cookie[SESSION_COOKIE_NAME]['httponly'] = True
    cookie[SESSION_COOKIE_NAME]['expires'] = 60 * lifespan
    if secure:
        cookie[SESSION_COOKIE_NAME]['secure'] = True

    cookie[SUBJECT_COOKIE_NAME] = system.subject
    cookie[SUBJECT_COOKIE_NAME]['httponly'] = True
    cookie[SUBJECT_COOKIE_NAME]['expires'] = 365 * 24 * 60 * 60
    k,v = str(cookie).split(':',1)
    response.headers[k] = v

class Session:
    tablename = 'dz_sessions'


    def __repr__(self):
        return ', '.join(['%s="%s"' % (k,v) for (k,v) in zip(self.__dict__,self.__dict__.values()) if k[0]!='_'])


    def __str__(self):
        return repr(self)


    def create_session_database(self):
        cmd = """
            create table %s (
                sesskey varchar(32) NOT NULL default '',
                expiry int(11) NOT NULL default '0',
                status char(1) not null default 'D',
                value text NOT NULL,
                PRIMARY KEY (sesskey)
            ) type=MyISAM;
        """ % self.tablename
        self.exec_SQL(cmd)


    def gc(self):
        if system.config.get('session', 'destroy', True):
            cmd = 'DELETE FROM %s WHERE (expiry < %s) or (status="D")' % (self.tablename,'%s')
            db(cmd,time.time())


    def new_session(self,timeout=sessionLife):
        def trysid(sid):
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

        self.sid = sid = get_session_cookie()
        valid_sid = sid and len(sid)==32 and self.sid.isalnum()

        if not (valid_sid and load_existing(sid) and self.ip==request.ip):
            self.new_session()


    def save_session(self,response, sid=None, timeout=sessionLife):
        sid = sid or self.sid
        expiry = time.time() + timeout * 60
        values = {}
        for key in self.__dict__.keys():
            if key[0] != '_':
                values[key] = self.__dict__[key]
        value = pickle.dumps(values)
        cmd = 'UPDATE %s SET expiry=%s, value=%s WHERE sesskey=%s' % (self.tablename,'%s','%s','%s')
        curs = db(cmd,expiry,value,sid)
        set_session_cookie(response, session.sid, request.host, sessionLife, system.secure_cookies)


    def destroy_session(self, sid=None):
        sid = sid or self.sid
        self.__dict__.clear()
        
        if system.config.get('sessions', 'destroy', True):
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

session = Session()

if __name__ == '__main__':
    import unittest

    debug = 1

    class SessionTest(unittest.TestCase):
        def test(self):

            #Create session object
            session = Session()

            #Create new session
            id = session.new_session()
            self.assert_(id!='Session error')
            session.MyName = 'Test'
            session.Message = 'This is a test session'
            session.Number = 123

            #Save session
            session.save_session(id)
            self.assertEqual(len(db('select * from '+session.tablename+' where sesskey="'+id+'"').__dict__['data']),1)

            # Create new session object
            session2 = Session()

            # Load above session
            session2.load_session(id)
            self.assertEqual(session2.Number,123)
            self.assertEqual(session2.MyName,'Test')
            self.assertEqual(session2.Message,'This is a test session')
            session2.destroy_session(id)
            if not debug:
               self.assertEqual(len(session.exec_SQL('select * from '+session.tablename+' where sesskey="'+id+'"').__dict__['data']),0)

    unittest.main()

