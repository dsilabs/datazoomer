
__all__ = ['Session']

import uuid
import time
import pickle
#import web

from utils import *

if __name__ == '__main__':
    from zoom.database import test_database

class Session(threadeddict):

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

    def new(self):
        """
        create a new session

            >>> session = Session()
            >>> session.setup(test_database(), '1.1.1.1')
            >>> id = session.new()
            >>> len(id)
            32
            >>> session
            <Session {}>

        """
        db, ip = self._db, self._ip
        self.clear()
        self._db, self._ip = db, ip
        self.save()
        return self._sid


    def load(self, sid):
        """
        load a session

            >>> db = test_database()
            >>> session = Session()
            >>> session.setup(db, '1.1.1.1')
            >>> sid = session.new()
            >>> session.name = 'jo'
            >>> session.save()
            >>> session2 = Session()
            >>> session2.setup(db, '1.1.1.1')
            >>> session2.load(sid)
            >>> session2
            <Session {'name': 'jo'}>

        """

        db = self._db

        if sid and len(sid)==32 and sid.isalnum():
            cmd = 'select * from sessions where sid=%s and ip=%s and status="A" and expiry>%s'
            rec = db(cmd, sid, self._ip, time.time())
            if rec:
                self._sid = sid

                rec = rec[0]
                try:
                    values = (rec.VALUE and pickle.loads(rec.VALUE or {}))
                except:
                    values = {}
                self.update(values)
                return True

    def establish(self, db, ip, sid):
        self.setup(db, ip)
        if not self.load(sid):
            sid = self.new()
        return sid

    def save(self, lifespan=3600):
        """
        save a session

            >>> # create a session and store some data in it
            >>> db = test_database()
            >>> session = Session()
            >>> session.setup(db, '1.1.1.1')
            >>> sid = session.new()
            >>> session
            <Session {}>
            >>> session.name = 'sam'
            >>> session.save()
            >>> ignore_sid = session.new()
            >>> session
            <Session {}>

            >>> # create another session and store some data in it
            >>> session2 = Session()
            >>> session2.setup(db, '1.1.1.1')
            >>> new_sid = session2.new()
            >>> session2.name = 'joe'
            >>> session2.save()

            >>> # read the saved session data
            >>> session3 = Session()
            >>> session3.setup(db, '1.1.1.1')
            >>> session3.load(sid)
            >>> session3
            <Session {'name': 'sam'}>

            >>> session4 = Session()
            >>> session4.setup(db, '1.1.1.1')
            >>> session4.load(new_sid)
            >>> session4
            <Session {'name': 'joe'}>

            >>> # save the session again and see that it has changed
            >>> session4.name = 'bob'
            >>> session4.special = 'not so'
            >>> session4.save()
            >>> throwaway_sid = session4.new()
            >>> session4.load(new_sid)
            >>> session4
            <Session {'name': 'bob', 'special': 'not so'}>


        """
        db = self._db

        sid = self.get('_sid', uuid.uuid4().hex)
        expiry = time.time() + lifespan

        values = {}
        for key in self.keys():
            if not key.startswith('_'):
                values[key] = self[key]
        data = pickle.dumps(values)

        if '_sid' in self:
            cmd = 'update sessions set expiry=%s, value=%s where sid=%s'
            db(cmd, expiry, data, sid)
        else:
            self._sid = sid
            cmd = 'insert into sessions (sid, expiry, ip, status, value) values (%s,%s,%s,%s,%s)'
            db(cmd, sid, expiry, self._ip, 'A', data)

    def kill(self):
        """
        removes the session from the database and clears it
        """
        db = self._db
        cmd = 'delete from sessions where sid=%s'
        db(cmd, self._sid)
        self.clear()

    def __repr__(self):     
        values = {}
        for key in self.keys():
            if not key.startswith('_'):
                values[key] = self.__dict__[key]
        return '<Session ' + repr(values) + '>'


import doctest
doctest.testmod()

