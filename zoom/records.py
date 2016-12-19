"""
    record store

    EXPERIMENTAL!
"""

import datetime
import decimal

# pylint: disable=unused-import
from zoom.utils import Record, RecordList, kind
from zoom.exceptions import TypeException

def setup_test():
    """set up test database"""
    # pylint: disable=invalid-name

    def create_test_tables(db):
        """create test tables"""
        db("""
        create table if not exists person (
            id int not null auto_increment,
            name      varchar(100),
            age       smallint,
            kids      smallint,
            birthdate date,
            PRIMARY KEY (id)
            )
        """)
        db("""
        create table if not exists account (
            account_id int not null auto_increment,
            name varchar(100),
            added date,
            PRIMARY KEY (account_id)
            )
        """)

    def delete_test_tables(db):
        """drop test tables"""
        db('drop table if exists person')
        db('drop table if exists account')

    from zoom.db import database

    db = database(
        'mysql',
        host='database',
        db='test',
        user='testuser',
        passwd='password'
    )
    delete_test_tables(db)
    create_test_tables(db)
    return db


def get_result_iterator(rows, cls):
    """returns an iterator that iterates over the rows and zips the names onto
    the items being iterated so they come back as dicts"""
    names = [d[0] == 'id' and '_id' or d[0] for d in rows.cursor.description]
    for rec in rows:
        yield cls((k, v) for k, v in zip(names, rec) if v != None)


class Result(object):
    """rows resulting from a method call"""
    # pylint: disable=too-few-public-methods
    def __init__(self, rows, cls=dict):
        self.rows = rows
        self.cls = cls

    def __iter__(self):
        return get_result_iterator(self.rows, self.cls)

    def __len__(self):
        return self.rows.cursor.rowcount

    def __repr__(self):
        return repr(list(self))

    def __str__(self):
        return str(RecordList(self))


class RecordStore(object):
    """
    stores records

        >>> db = setup_test()
        >>> class Person(Record): pass
        >>> class People(RecordStore): pass
        >>> people = People(db, Person)
        >>> people.kind
        'person'
        >>> joe = Person(name='Joe', age=20, birthdate=datetime.date(1992,5,5))
        >>> repr(joe) == (
        ...     "<Person {'name': 'Joe', 'age': 20, "
        ...     "'birthdate': datetime.date(1992, 5, 5)}>"
        ... )
        True
        >>> people.put(joe)
        1L
        >>> person = people.get(1L)
        >>> repr(person) == (
        ...     "<Person {'name': 'Joe', 'age': 20, "
        ...     "'birthdate': datetime.date(1992, 5, 5)}>"
        ... )
        True

        >>> sally = Person(name='Sally', kids=0,
        ...             birthdate=datetime.date(1992,5,5))
        >>> people.put(sally)
        2L

        >>> sally = people.find(name='Sally')
        >>> repr(sally) == (
        ...     "[<Person {'name': 'Sally', 'birthdate': "
        ...     "datetime.date(1992, 5, 5), 'kids': 0}>]"
        ... )
        True

        >>> sally = people.first(name='Sally')
        >>> repr(sally) == (
        ...     "<Person {'name': 'Sally', "
        ...     "'birthdate': datetime.date(1992, 5, 5), 'kids': 0}>"
        ... )
        True

        >>> sally.kids += 1
        >>> people.put(sally)
        2L

        >>> repr(people.first(name='Sally')) == (
        ...     "<Person {'name': 'Sally', "
        ...     "'birthdate': datetime.date(1992, 5, 5), 'kids': 1}>"
        ... )
        True

        >>> sally = people.first(name='Sally')
        >>> sally.kids += 1
        >>> people.put(sally)
        2L

        >>> repr(people.first(name='Sally')) == (
        ...     "<Person {'name': 'Sally', "
        ...     "'birthdate': datetime.date(1992, 5, 5), 'kids': 2}>"
        ... )
        True
        >>> sally = people.first(name='Sally')
        >>> sally.kids += 1
        >>> people.put(sally)
        2L

        >>> repr(people.first(name='Sally')) == (
        ...     "<Person {'name': 'Sally', "
        ...     "'birthdate': datetime.date(1992, 5, 5), 'kids': 3}>"
        ... )
        True


        >>> class Account(Record): pass
        >>> class Accounts(RecordStore): pass
        >>> accounts = Accounts(db, Account, key='account_id')
        >>> accounts.kind
        'account'

        >>> account = Account(name='Joe', added=datetime.date(1992,5,5))
        >>> repr(account) == (
        ...     "<Account {'name': 'Joe', 'added': datetime.date(1992, 5, 5)}>"
        ... )
        True
        >>> id = accounts.put(account)
        >>> id
        1L
        >>> accounts.put(Account(name='Sam', added=datetime.date(2001,1,1)))
        2L
        >>> accounts.put(Account(name='Sal', added=datetime.date(2001,1,1)))
        3L

        >>> account = accounts.get(1)
        >>> print accounts
        account
        account_id name added
        ---------- ---- ----------
                 1 Joe  1992-05-05
                 2 Sam  2001-01-01
                 3 Sal  2001-01-01
        3 account records

        >>> print accounts.first(name='Sam')
        Account
          account_id ..........: 2L
          name ................: 'Sam'
          added ...............: datetime.date(2001, 1, 1)

        >>> print accounts.find(added=datetime.date(2001, 1, 1))
        account
        account_id name added
        ---------- ---- ----------
                 2 Sam  2001-01-01
                 3 Sal  2001-01-01
        2 account records

        >>> accounts.delete(2L)
        [2L]
        >>> print accounts
        account
        account_id name added
        ---------- ---- ----------
                 1 Joe  1992-05-05
                 3 Sal  2001-01-01
        2 account records

        """

    def __init__(self, db, record_class=dict, name=None, key='id'):
        # pylint: disable=invalid-name
        self.db = db
        self.record_class = record_class
        self.kind = name or kind(record_class())
        self.key = key

    @property
    def id_name(self):
        return self.key == 'id' and '_id' or self.key

    def put(self, record):
        """
        stores a record

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> sally = Person(name='Sally', age=25)
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id
            1L
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> sally = people.get(id)
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> sally.age = 35
            >>> people.put(sally)
            1L
            >>> person = people.get(id)
            >>> person
            <Person {'name': 'Sally', 'age': 35}>
            >>> id = people.put({'name':'James', 'age':15})
            >>> id
            2L
            >>> people.get(id)
            <Person {'name': 'James', 'age': 15}>
        """

        table_attributes = self.get_attributes()
        keys = [k for k in record.keys() if k != '_id' and k in table_attributes]
        values = [record[k] for k in keys]
        datatypes = [type(i) for i in values]
        values = [i for i in values]
        valid_types = [
            str,
            unicode,
            long,
            int,
            float,
            datetime.date,
            datetime.datetime,
            bool,
            type(None),
            decimal.Decimal,
        ]

        # pylint: disable=star-args

        for atype in datatypes:
            if atype not in valid_types:
                raise TypeException('unsupported type <type %s>' % atype)

        if self.id_name in record:
            _id = record[self.id_name]
            set_clause = ', '.join('%s=%s' % (i, '%s') for i in keys)
            cmd = 'update %s set %s where %s=%d' % (
                self.kind,
                set_clause,
                self.key,
                _id
            )
            self.db(cmd, *values)
        else:
            names = ', '.join(keys)
            placeholders = ','.join(['%s'] * len(keys))
            cmd = 'insert into %s (%s) values (%s)' % (
                self.kind, names, placeholders)
            _id = self.db(cmd, *values)
            record['_id'] = _id

        return _id

    def get(self, keys):
        # pylint: disable=trailing-whitespace
        """
        retrives records

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(**{'name': 'Sam', 'age':15}))
            >>> sam = people.get(id)
            >>> sam
            <Person {'name': 'Sam', 'age': 15}>
            >>> people.put(Person(name='Jim',age=21))
            2L
            >>> print people
            person
            _id name age
            --- ---- ---
              1 Sam   15
              2 Jim   21
            2 person records

            >>> people.put(Person(name='Alice',age=29))
            3L
            >>> print people.get([1, 3])
            person
            _id name  age
            --- ----- ---
              1 Sam    15
              3 Alice  29
            2 person records

        """
        # pylint: disable=star-args

        if keys is None:
            return None

        if not isinstance(keys, (list, tuple)):
            keys = (keys, )
            cmd = 'select * from '+self.kind+' where ' + self.key + '=%s'
            as_list = 0
        else:
            keys = [long(key) for key in keys]
            cmd = 'select * from {} where {} in ({})'.format(
                self.kind,
                self.key,
                ','.join(['%s'] * len(keys))
            )
            as_list = 1

        if not keys:
            if as_list:
                return []
            else:
                return None

        rows = self.db(cmd, *keys)

        if as_list:
            return Result(rows, self.record_class)

        for rec in Result(rows, self.record_class):
            return rec

    def get_attributes(self):
        """
        get complete set of attributes for the record type

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> sam = Person(**{'name': 'Sam', 'age':15})
            >>> sam.keys()
            ['age', 'name']
            >>> id = people.put(sam)
            >>> people.get_attributes()
            ['name', 'age', 'kids', 'birthdate']

        """
        cmd = 'describe %s' % self.kind
        rows = self.db(cmd)
        return [rec[0] for rec in rows if rec[0] != 'id']

    def _delete(self, ids):
        if ids:
            spots = ','.join('%s' for _ in ids)
            cmd = 'delete from {} where {} in ({})'.format(
                self.kind, self.key, spots)
            self.db(cmd, *ids)
            return ids

    def delete(self, *args, **kwargs):
        """
        delete a record

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> joe = people.get(id)
            >>> id
            3L
            >>> bool(joe)
            True
            >>> joe
            <Person {'name': 'Joe', 'age': 25}>
            >>> people.delete(id)
            [3L]
            >>> joe = people.get(id)
            >>> joe
            >>> bool(joe)
            False

            >>> bool(people.find(name='Sally'))
            True
            >>> people.delete(name='Sallie')
            >>> bool(people.find(name='Sally'))
            True
            >>> people.delete()
            >>> people.delete(name='Sally')
            [1L]
            >>> bool(people.find(name='Sally'))
            False

            >>> db.close()
        """
        ids = []
        for key in args:
            if hasattr(key, 'get'):
                key = key.get(self.id_name)
            ids.append(key)
        if kwargs:
            ids.extend(self._find(**kwargs))
        return self._delete(ids)
        # if hasattr(key, 'get'):
        #     key = key.get(self.id_name)
        # cmd = 'delete from %s where %s=%s' % (self.kind, self.key, '%s')
        # self.db(cmd, key)

    def exists(self, keys=None):
        """
        tests for existence of a record

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id
            1L
            >>> sally = people.get(id)
            >>> sally
            <Person {'name': 'Sally', 'age': 25}>
            >>> people.exists(1L)
            True
            >>> people.exists(2L)
            False
            >>> people.exists([1L,2L])
            [True, False]
            >>> id = people.put(Person(name='Sam', age=25))
            >>> people.exists([1L,2L])
            [True, True]

        """
        # pylint: disable=star-args

        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
        slots = (','.join(['%s']*len(keys)))
        cmd = 'select distinct %s from %s where %s in (%s)' % (
            self.key, self.kind, self.key, slots)
        rows = self.db(cmd, *keys)

        found_keys = [rec[0] for rec in rows]
        if len(keys) > 1:
            result = [(key in found_keys) for key in keys]
        else:
            result = keys[0] in found_keys
        return result

    def all(self):
        """
        Retrieves all entities

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> repr(people.all()) == (
            ...     "[<Person {'name': 'Sally', 'age': 25}>, "
            ...     "<Person {'name': 'Sam', 'age': 25}>, "
            ...     "<Person {'name': 'Joe', 'age': 25}>]"
            ... )
            True

        """
        return RecordList(self)

    def zap(self):
        """
        deletes all entities of the given kind

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> repr(people.all()) == (
            ...     "[<Person {'name': 'Sally', 'age': 25}>, "
            ...     "<Person {'name': 'Sam', 'age': 25}>, "
            ...     "<Person {'name': 'Joe', 'age': 25}>]"
            ... )
            True

            >>> people.zap()
            >>> people.all()
            []

        """
        cmd = 'delete from '+self.kind
        self.db(cmd)

    def __len__(self):
        """
        returns number of entities

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> len(people)
            0
            >>> id = people.put(Person(name='Sam', age=15))
            >>> id = people.put(Person(name='Sally', age=25))
            >>> len(people)
            2

        """
        cmd = 'select count(*) cnt from '+self.kind
        return int(self.db(cmd).cursor.fetchone()[0])

    def _find(self, **kv):
        """
        Find keys that meet search critieria
        """
        items = kv.items()
        clause = ' and '.join('%s=%s' % (k, '%s') for k, v in items)
        cmd = ' '.join([
            'select distinct',
            self.key,
            'from',
            self.kind,
            'where',
            clause,
        ])
        result = self.db(cmd, *[v for _, v in items])
        return [i[0] for i in result]

    def find(self, **kv):
        """
        finds entities that meet search criteria

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> repr(people.find(age=25)) == (
            ...     "[<Person {'name': 'Sam', 'age': 25}>, "
            ...     "<Person {'name': 'Bob', 'age': 25}>]"
            ... )
            True
            >>> people.find(name='Sam')
            [<Person {'name': 'Sam', 'age': 25}>]
            >>> len(people.find(name='Sam'))
            1

        """
        items = kv.items()
        where_clause = ' and '.join('%s=%s' % (k, '%s') for k, v in items)
        cmd = 'select * from ' + self.kind + ' where ' + where_clause
        result = self.db(cmd, *[v for _, v in items])
        return Result(result, self.record_class)

    def first(self, **kv):
        """
        finds the first record that meet search criteria

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.first(age=5)
            >>> people.first(age=25)
            <Person {'name': 'Sam', 'age': 25}>

        """
        for item in self.find(**kv):
            return item

    def last(self, **kv):
        """
        finds the last record that meet search criteria

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.last(age=5)
            >>> people.last(age=25)
            <Person {'name': 'Bob', 'age': 25}>

        """
        rows = self._find(**kv)
        if rows:
            return self.get(rows[-1])
        return None

    def search(self, text):
        """
        finds records that match search text

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam Adam Jones', age=25))
            >>> id = people.put(Person(name='Sally Mary Smith', age=55))
            >>> id = people.put(Person(name='Bob Marvin Smith', age=25))
            >>> repr(list(people.search('smi'))) == (
            ...     "[<Person {'name': 'Sally Mary Smith', 'age': 55}>, "
            ...     "<Person {'name': 'Bob Marvin Smith', 'age': 25}>]"
            ... )
            True
            >>> list(people.search('bo smi'))
            [<Person {'name': 'Bob Marvin Smith', 'age': 25}>]
            >>> list(people.search('smi 55'))
            [<Person {'name': 'Sally Mary Smith', 'age': 55}>]

        """
        def matches(item, terms):
            """returns True if an item matches the given search terms"""
            values = [str(i).lower() for i in item.values()]
            return all(any(t in s for s in values) for t in terms)

        search_terms = list(set([i.lower() for i in text.strip().split()]))
        for rec in self:
            if matches(rec, search_terms):
                yield rec

    def filter(self, function):
        """
        finds records that satisfiy filter

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam Adam Jones', age=25))
            >>> id = people.put(Person(name='Sally Mary Smith', age=55))
            >>> id = people.put(Person(name='Bob Marvin Smith', age=25))
            >>> list(people.filter(lambda a: 'Mary' in a.name))
            [<Person {'name': 'Sally Mary Smith', 'age': 55}>]
            >>> repr(list(people.filter(lambda a: a.age < 40))) == (
            ...     "[<Person {'name': 'Sam Adam Jones', 'age': 25}>, "
            ...     "<Person {'name': 'Bob Marvin Smith', 'age': 25}>]"
            ... )
            True

        """
        for rec in self:
            if function(rec):
                yield rec

    def __iter__(self):
        """
        interates through records

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> for rec in people: print rec
            Person
              name ................: 'Sam'
              age .................: 25
            Person
              name ................: 'Sally'
              age .................: 55
            Person
              name ................: 'Bob'
              age .................: 25
            >>> sum(person.age for person in people)
            105


        """
        cmd = 'select * from '+self.kind
        rows = self.db(cmd)
        return get_result_iterator(rows, self.record_class)

    def __getitem__(self, index):
        """
        get item at index

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people[1]
            <Person {'name': 'Sally', 'age': 55}>
            >>> people[0]
            <Person {'name': 'Sam', 'age': 25}>
            >>> people[2]
            <Person {'name': 'Bob', 'age': 25}>
            >>> try:
            ...     people[3]
            ... except IndexError:
            ...     print 'out of range'
            out of range


        """
        return self.all()[index]

    def __str__(self):
        # pylint: disable=trailing-whitespace
        """
        format for people

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> print people
            person
            _id name  age
            --- ----- ---
              1 Sam    25
              2 Sally  55
              3 Bob    25
            3 person records

            >>> people.zap()
            >>> print people
            Empty list

        """
        return str(self.all())

    def __repr__(self):
        """
        unabiguous representation

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> repr(people) == (
            ...     "[<Person {'name': 'Sam', 'age': 25}>, "
            ...     "<Person {'name': 'Sally', 'age': 55}>, "
            ...     "<Person {'name': 'Bob', 'age': 25}>]"
            ... )
            True
            >>> people.zap()
            >>> people
            []

        """
        return repr(self.all())
