"""
    Test the records module
"""

from zoom.records import Record, RecordStore
from zoom.db import database

import unittest
from decimal import Decimal

from datetime import date, time, datetime

class Person(Record): pass
class TestPerson(Record): pass


class TestRecordStore(unittest.TestCase):

    def __init__(self, *a, **k):
        unittest.TestCase.__init__(self, *a, **k)
        self.key = 'id'

    @property
    def id_name(self):
        return self.key == 'id' and '_id' or self.key

    def create_tables(self, db):
        db('drop table if exists person')
        db("""
        create table person (
            {key} int not null auto_increment,
            name      varchar(100),
            age       smallint,
            kids      smallint,
            birthdate date,
            done      boolean,
            PRIMARY KEY ({key})
            )
        """.format(key=self.key))

    def get_record_store(self):
        return RecordStore(self.db, Person, key=self.key)

    def setUp(self):
        params = dict(
            host='database',
            user='testuser',
            passwd='password',
            db='test',
        )
        self.db = database('mysql', **params)

        self.create_tables(self.db)

        self.people = self.get_record_store()

        self.joe_id = self.people.put(Person(name='Joe', age=50))
        self.sam_id = self.people.put(Person(name='Sam', age=25))
        self.people.put(Person(name='Ann', age=30))

    def tearDown(self):
        def delete_test_tables(db):
            """drop test tables"""
            db('drop table if exists person')
            db('drop table if exists account')

        self.people.zap()
        delete_test_tables(self.db)
        self.db.close()

    def test_put(self):
        jane_id = self.people.put(Person(name='Jane', age=25))
        person = self.people.get(jane_id)
        self.assertEqual(
            dict(person),
            {
                self.id_name: jane_id,
                'name': 'Jane',
                'age': 25,
            }
        )

    def test_get(self):
        joe = self.people.get(self.joe_id)
        self.assertEqual(
            dict(joe),
            #dict(_id=self.joe_id, name='Joe', age=50)
            {
                self.id_name: self.joe_id,
                'name': 'Joe',
                'age': 50,
            }
        )

    def test_get_missing(self):
        joe = Person(name='Joe', age=50)
        joe_id = self.people.put(joe)
        person = self.people.get(joe_id)
        self.assertEqual(None, self.people.get(joe_id + 1))

    def test_get_multiple(self):
        keys = [self.sam_id, self.joe_id]
        r = self.people.get(keys)
        sam = self.people.get(self.sam_id)
        joe = self.people.get(self.joe_id)
        sort_order = lambda a: keys.index(a[self.id_name])
        self.assertEqual(sorted(r, key=sort_order), [sam, joe])

    def test_get_put_get(self):
        sam = self.people.get(self.sam_id)
        self.assertEqual(sam.age, 25)
        self.assertEqual(len(self.people), 3)
        sam.age += 1
        self.people.put(sam)
        self.assertEqual(len(self.people), 3)
        person = self.people.get(self.sam_id)
        self.assertEqual(person.age, 26)

    def test_delete_by_entity(self):
        sam = self.people.get(self.sam_id)
        self.assert_(sam)
        self.people.delete(sam)
        sam = self.people.get(self.sam_id)
        self.assertEqual(None, sam)

    def test_delete_by_id(self):
        sam = self.people.get(self.sam_id)
        self.assert_(sam)
        self.people.delete(self.sam_id)
        sam = self.people.get(self.sam_id)
        self.assertEqual(None, sam)

    def test_none(self):
        al_id = self.people.put(Person(name='Al', age=None))
        al = self.people.get(al_id)
        # note, this behaviour is different than the Entity store
        # because in an EntityStore None is a storable value
        # whereas in a regular database table None is equivalant
        # to null and there is no way to distinguish None.
        self.assertEqual(getattr(al, 'age', None), None)

    def test_bool(self):
        al_id = self.people.put(Person(name='Al', done=False))
        al = self.people.get(al_id)
        self.assertEqual(al.done, False)
        al.done = True
        self.people.put(al)
        person = self.people.get(al_id)
        self.assertEqual(person.done, True)

    def test_kind(self):
        self.assertEqual(self.people.kind, 'person')
        self.assertEqual(RecordStore(self.db,TestPerson).kind, 'test_person')

    def test_len(self):
        self.assertEqual(3, len(self.people))

    def test_zap(self):
        self.assertEqual(3, len(self.people))
        self.people.zap()
        self.assertEqual(0, len(self.people))


class TestKeyedRecordStore(TestRecordStore):

    def __init__(self, *a, **k):
        TestRecordStore.__init__(self, *a, **k)
        self.key = 'person_id'


