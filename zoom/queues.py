"""
    messages system (experimental)
"""

import uuid
import time
import datetime
import platform
import logging
from zoom import json, Record, EntityStore

__all__ = [
    'Queues',
    'Topic',
    'EmptyException',
    'WaitException',
    'StopListening',
    'StopHandling',
    ]

now = datetime.datetime.now

class EmptyException(Exception): pass
class WaitException(Exception): pass
class StopListening(Exception): pass
class StopHandling(Exception): pass

def response_topic_name(topic, id):
    """calculate the name of the reponse topic for a topic"""
    return '%s.response.%s' % (topic, id)
        
class SystemMessage(Record): pass
Message = SystemMessage


def setup_test():
    from zoom.store import setup_test
    db = setup_test()
    return Queues(db)


class TopicIterator(object):

    def __init__(self, topic, newest=None):
        self.topic = topic

    def __iter__(self):
        return self

    def next(self):
        try:
            message = self.topic.poll()
        except EmptyException:
            raise StopIteration
        else:
            return message


class Topic(object):
    """
    message topic
    """

    def __init__(self, name, newest=None, db=None):
        self.name = name
        self.db = db
        self.messages = EntityStore(db, Message)
        self.newest = newest != None and newest or self.last() or -1


    def last(self):
        """get row_id of the last (newest) message in the topic"""
        if self.name:
            cmd = """
                select max(row_id) n 
                from attributes 
                where kind=%s and attribute="topic" and value=%s
                """
            rec = self.db(cmd, self.messages.kind, self.name)
        else:
            cmd = 'select max(row_id) n from attributes where kind=%s'
            rec = self.db(cmd, self.messages.kind)
        if type(rec) == long:
            return 0
        row_id = rec.first()[0]
        return row_id or 0


    def put(self, message):
        """put a message in the topic"""
        return self.messages.put(
                Message(
                    topic = self.name,
                    timestamp = now(),
                    node = platform.node(),
                    body = json.dumps(message),
                    )
                )


    def send(self, *messages):
        """send list of messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.send('hey!', 'you!')
            [1L, 2L]
            >>> t.peek()
            u'hey!'
            >>> t.peek()
            u'hey!'
        """
        return [self.put(message) for message in messages]


    def _peek(self, newest=None):
        top_one = newest != None and newest or self.newest or 0
        db = self.db
        if self.last() > self.newest:
            if self.name:
                cmd = """
                    select min(row_id) as row_id 
                    from attributes 
                    where kind=%s and attribute="topic" and value=%s and row_id>%s
                    """
                rec = db(cmd, self.messages.kind, self.name, top_one)
            else:
                cmd = """
                    select min(row_id) as row_id 
                    from attributes where kind=%s and row_id>%s
                    """
                rec = db(cmd, self.messages.kind, top_one)
            if type(rec) == long:
                row_id = 0
            else:
                row_id = rec.first()[0]
            if row_id:
                message = self.messages.get(row_id)
                if message:
                    return row_id, self.name, json.loads(message.body)
        raise EmptyException


    def peek(self, newest=None):
        """
        return the next message but don't remove it

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.peek()
            u'hey!'
            >>> t.peek()
            u'hey!'
        """
        return self._peek(newest)[2]


    def _poll(self, newest=None):
        r = self._peek(newest)
        self.newest = r[0]
        return r


    def poll(self, newest=None):
        """
        peek at the next message and increment internal pointer

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.newest
            -1
            >>> t.poll()
            u'hey!'
            >>> t.newest
            1L
            >>> t.poll()
            u'you!'

            >>> raised = False
            >>> try:
            ...     t.poll()
            ... except EmptyException:
            ...     raised = True
            >>> raised
            True

            >>> t.newest = -1
            >>> t.poll()
            u'hey!'
        """
        return self._poll(newest)[2]


    def _pop(self):
        r = self._peek()
        row_id = r[0]
        self.messages.delete(row_id)
        if self.messages.db.rowcount > 0:
            self.newest = row_id
            return r
        else:
            # If we were unable to delete it then soneone else
            # has already deleted it between the time that
            # we saw it and the time we attempted to delete it.
            raise EmptyException


    def pop(self):
        """
        read next message and remove it from the topic

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.len()
            2L
            >>> t._peek()
            (1L, 'test_topic', u'hey!')
            >>> t.pop()
            u'hey!'
            >>> t.len()
            1L
            >>> t.pop()
            u'you!'
            >>> t.len()
            0L
            >>> t.newest = -1
            >>> raised = False
            >>> try:
            ...     t.pop()
            ... except EmptyException:
            ...     raised = True
            >>> raised
            True
        """
        return self._pop()[2]


    def len(self, newest=None):
        """
        return the number of messages in the topic

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.len()
            2L
        """
        if self.last() > self.newest:
            if self.name:
                cmd = """
                    select count(row_id) as n
                    from attributes
                    where kind=%s and attribute="topic" and value=%s and row_id>%s
                    """
                t = self.db(cmd, self.messages.kind, self.name, self.newest)
            else:
                cmd = """select count(row_id) as n
                    from attributes
                    where kind=%s and row_id>%s
                    """
                t = self.db(cmd, self.messages.kind, self.newest)
            n = t.first()[0] or 0L
            return n
        return 0L


    def __len__(self):
        """
        return the number of messages in a topic as an int
        (note: for large number of messages use t.len()

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> len(t)
            2
        """
        return self.len()


    def __iter__(self):
        """
        iterate through a topic

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> for m in t: print m
            hey!
            you!
        """
        return TopicIterator(self, self.newest)


    def wait(self, delay=1, timeout=15):
        """
        wait for a message to arrive and return it

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.wait()
            u'hey!'
            >>> t.wait()
            u'you!'
        """
        deadline = time.time() + timeout
        while True:
            try:
                msg = self.pop()
            except EmptyException:
                pass
            else:
                return msg
            time.sleep(delay)
            if time.time() > deadline:
                raise WaitException


    def listen(self, f, delay=1, meta=False):
        """
        observe but don't consume messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> def echo(m):
            ...     print m
            ...     return m == 'you!'
            >>> t.listen(echo)
            hey!
            you!
            2L

            >>> t1 = messages.topic('test_topic1')
            >>> t2 = messages.topic('test_topic2')
            >>> t3 = messages.topic(None)

            >>> t1.put('hey!')
            3L
            >>> t2.put('you!')
            4L
            >>> def echo(m):
            ...     print m
            ...     return m == 'you!'
            >>> t3.listen(echo)
            hey!
            you!
            2L

        """
        n = 0L
        done = False
        while not done:
            try:
                more_to_do = True
                while more_to_do:
                    try:
                        p = self._poll()
                    except EmptyException:
                        more_to_do = False
                    else:
                        if meta:
                            done = f(p)
                        else:
                            done = f(p[2])
                        n += 1
            except StopListening:
                return n
            else:
                time.sleep(delay)
        return n


    def join(self, jobs):
        """wait for responses from consumers"""
        return [
                Topic(
                    response_topic_name(self.name, job),
                    newest=job,
                    db=self.db,
                    ).wait() for job in jobs
                ]


    def call(self, *messages):
        """send messages and wait for responses"""
        return self.join(self.send(*messages))


    def handle(self, f, timeout=0, delay=1, one_pass=False):
        """respond to and consume messages

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> def echo(m):
            ...     if m == 'quit': raise StopHandling
            ...     print 'got', repr(m)
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.put('quit')
            3L
            >>> t.handle(echo)
            got u'hey!'
            got u'you!'
            2L
        """
        deadline = timeout and time.time() + timeout
        done = False
        n = 0L
        while not done:
            try:
                try:
                    more_to_do = True
                    while more_to_do:
                        try:
                            row, topic, message = self._pop()
                            result = f(message)
                            t = Topic(response_topic_name(topic, row), None, self.db)
                            t.send(result)
                            deadline = timeout and time.time() + timeout
                            n += 1
                        except EmptyException:
                            more_to_do = False
                        time.sleep(0)
                except StopHandling:
                    done = True 
                else:
                    time.sleep(delay)
            except KeyboardInterrupt:
                done = True
            if timeout and time.time() > deadline:
                done = True
        return n


    def process(self, f, timeout=1):
        """respond to and consume current messages only

            >>> messages = setup_test()
            >>> t = messages.get('test_topic')
            >>> def echo(m): print 'got', repr(m)
            >>> t.put('hey!')
            1L
            >>> t.put('you!')
            2L
            >>> t.process(echo)
            got u'hey!'
            got u'you!'
            2L
        """
        return self.handle(f, timeout, one_pass=True)

class Queues(object):
    """
    messages

        >>> messages = setup_test()
        >>> t = messages.get('test_topic')
        >>> t.put('hey!')
        1L
        >>> t.put('you!')
        2L
        >>> t.peek()
        u'hey!'
    """

    def __init__(self, db=None):
        self.db = db

    def get(self, name, newest=None):
        return Topic(name, newest, self.db)

    def topic(self, name, newest=None):
        return Topic(name, newest, self.db)

    def topics(self):
        cmd = """
            select distinct value
            from attributes
            where kind=%s and attribute="topic"
            order by value
            """
        kind = EntityStore(self.db, Message).kind
        return [a for a, in self.db(cmd, kind)]

    def stats(self):
        cmd = """
            select value, count(*) as count
            from attributes
            where kind=%s and attribute="topic"
            group by value
            """
        kind = EntityStore(self.db, Message).kind
        return self.db(cmd, kind)

    def __call__(self, name, newest=None):
        return Topic(name, newest, self.db)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

