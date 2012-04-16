
__all__ = ['Session']

import uuid
import time
import pickle
import web

from utils import *

SESSION_COOKIE_NAME = 'zoom_sid'
SESSION_COOKIE_LIFESPAN = 60

from zoom.database import test_database

class Session(threadeddict):

#    def clear(self):
#        keeparound = self.get('_keeparound',None)
#        threadeddict.clear(self)
#        self._keeparound = keeparound
#
#    def new(self):
#        """
#        create a new session
#
#            >>> import test_database
#            >>> session = Session()
#            >>> session.setup(test_database.test_database())
#            >>> session.new()
#            >>> session
#            ''
#
#        """
#        self.clear()
#        self.sid = uuid.uuid4().hex
#
#        cmd = "insert into sessions values (%s,%s,'A','')"
#        db = self._keeparound['db']
#        db(cmd, self.sid, time.time() + 60 * self._keeparound['lifespan'])
#        return self.sid
#

    @classmethod
    def create_sessions_table(self, db):
        """
        create the sessions table

            >>> db = test_database()
            >>> status = db('drop table sessions')
            >>> Session.create_sessions_table(db)
            >>> 'sessions' in db.table_names()
            True
            >>> db('drop table sessions')
            0L
            >>> 'sessions' in db.table_names()
            False
            >>> Session.create_sessions_table(db)
        """

        db('drop table if exists sessions')
        cmd = """
            create table sessions (
                sid varchar(32) NOT NULL default '',
                expiry int(11) NOT NULL default '0',
                status char(1) not null default 'D',
                ip char(15) not null default '',
                value text NOT NULL,
                PRIMARY KEY (sid)
            );
        """
        db(cmd)

    def setup(self, db, ip):
        self._db = db
        self._ip = ip

    def load(self, sid=None):
        """
        load a session

            >>> db = test_database()
            >>> session = Session()
            >>> session.setup(db, '1.1.1.1')
            >>> session.load()
            >>> session
            <Session {}>
            >>> session.name = 'test'
            >>> session
            <Session {'name': 'test'}>


        """

        #db = system.database
        #sid = system.request.cookies.get(SESSION_COOKIE_NAME, None)
        db = self._db

        if sid and len(sid)==32 and sid.isalnum():
            cmd = 'select * from sessions where sid=%s and ip=%s and status="A" and expiry>%s'
            rec = db(cmd, sid, self._ip, time.time())
            if rec:
                self.sid = sid

                rec = rec[0]
                try:
                    values = (rec.VALUE and pickle.loads(rec.VALUE or {}))
                except:
                    values = {}
                self.update(values)

                self.session_counter = self.get('session_counter',0) + 1
                return True


    def save(self, lifespan=3600):
        """
        save a session

            >>> db = test_database()
            >>> session = Session()
            >>> session.setup(db, '1.1.1.1')
            >>> session.load()
            >>> session
            <Session {}>
            >>> sid = session.save()
            >>> len(sid)
            32

        """
        db = self._db

        sid = self.get('sid', uuid.uuid4().hex)
        expiry = time.time() + lifespan

        values = {}
        for key in self.keys():
            if not key.startswith('_') and key not in ['sid']:
                values[key] = self[key]
        data = pickle.dumps(values)

        if 'sid' in self:
            cmd = 'update sessions set expiry=%s, ip=%s, value=%s where sid=%s'
            db(cmd, expiry, web.ctx.ip, data, sid)
        else:
            self.sid = sid
            cmd = 'insert into sessions (sid, expiry, ip, status, value) values (%s,%s,%s,%s,%s)'
            db(cmd, sid, expiry, self._ip, 'A', data)

        return sid

    def kill(self, sid):
        db = self._db
        cmd = 'delete from sessions where sid=%s'
        db(cmd, self.sid)
        self.clear()

    def __repr__(self):     
        values = {}
        for key in self.__dict__.keys():
            if key[0] != '_':
                values[key] = self.__dict__[key]
        return '<Session ' + repr(values) + '>'


import doctest
doctest.testmod()

