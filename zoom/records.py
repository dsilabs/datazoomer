"""
    record store

    EXPERIMENTAL!
"""

import datetime
from zoom.utils import Record, RecordList, kind

class ValidException(Exception): pass
class TypeException(Exception): pass

def setup_test():
    def create_test_tables(db):
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
    
    def delete_test_tables(db):
        db('drop table if exists person')

    import MySQLdb, db

    db = db.Database(
            MySQLdb.Connect, 
            host='database',
            db='test',
            user='testuser',
            passwd='password')
    db.autocommit(1)
    delete_test_tables(db)
    create_test_tables(db)
    return db


def ResultIter(q, cls):
    names = [d[0] == 'id' and '_id' or d[0] for d in q.cursor.description]
    for rec in q:
        yield cls((k,v) for k,v in zip(names,rec) if v != None)


class Result(object):
    def __init__(self, q, cls=dict):
        self.q = q
        self.cls = cls

    def __iter__(self):
        return ResultIter(self.q, self.cls)

    def __len__(self):
        return self.q.rowcount

    def __repr__(self):
        return repr(list(self))


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
        >>> joe
        <Person {'name': 'Joe', 'age': 20, 'birthdate': datetime.date(1992, 5, 5)}>
        >>> people.put(joe)
        1L
        >>> person = people.get(1L)
        >>> person
        <Person {'name': 'Joe', 'age': 20, 'birthdate': datetime.date(1992, 5, 5)}>

        >>> sally = Person(name='Sally', kids=0, birthdate=datetime.date(1992,5,5))
        >>> people.put(sally)
        2L

        >>> sally = people.find(name='Sally')
        >>> sally
        [<Person {'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 0}>]

        >>> sally = people.first(name='Sally')
        >>> sally
        <Person {'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 0}>

        >>> sally.kids += 1
        >>> people.put(sally)
        2L

        >>> people.first(name='Sally')
        <Person {'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 1}>

        >>> sally = people.first(name='Sally')
        >>> sally.kids += 1
        >>> people.put(sally)
        2L

        >>> people.first(name='Sally')
        <Person {'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 2}>
        >>> sally = people.first(name='Sally')
        >>> sally.kids += 1
        >>> people.put(sally)
        2L

        >>> people.first(name='Sally')
        <Person {'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 3}>
        """


    def __init__(self, db, record_class=dict):
        self.db = db
        self.record_class = record_class
        self.kind = kind(record_class())


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


        keys        = [k for k in record.keys() if k <> '_id']
        values      = [record[k] for k in keys]
        datatypes   = [repr(type(i)).strip("<type >").strip("'") for i in values]
        values      = [i for i in values]
        valid_types = ['str','unicode','long','int','float','datetime.date','datetime.datetime','bool','NoneType']

        db = self.db

        for atype in datatypes:
            if atype not in valid_types:
                raise TypeException,'unsupported type <type %s>' % atype

        if '_id' in record:
            id = record['_id']
            sc = ', '.join('%s=%s' % (i,'%s') for i in keys)
            cmd = 'update %s set %s where id=%d' % (self.kind, sc, id)
            db(cmd, *values) 
        else:
            kc = ', '.join(keys)
            placeholders = ','.join(['%s'] * len(keys))
            cmd = 'insert into %s (%s) values (%s)' % (self.kind, kc, placeholders)
            _id = db(cmd, *values)
            id = record['_id'] = _id

        return id


    def get(self, keys):
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
                id  age  name  
            ------- ---- ----- 
                 1  15   Sam   
                 2  21   Jim   
            2 records


        """
        if keys == None: return None

        if not isinstance(keys, (list, tuple)):
            keys = (keys, )
            cmd = 'select * from '+self.kind+' where id=%s'
            as_list = 0
        else:
            keys = [long(key) for key in keys]
            cmd = 'select * from '+self.kind+' where id in (%s)' % (','.join(['%s']*len(keys)))
            as_list = 1

        if not keys:
            if as_list:
                return []
            else:
                return None

        rs = self.db(cmd, *keys)

        if as_list:
            return Result(rs, self.record_class)

        for rec in Result(rs, self.record_class): return rec


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
        rs = self.db(cmd)
        return [rec[0] for rec in rs if rec[0] != 'id']


    def delete(self, key):
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
            >>> joe = people.get(id)
            >>> joe
            >>> bool(joe)
            False

        """
        if hasattr(key, 'get'):
            key = key._id
        cmd = 'delete from %s where id=%s' % (self.kind, '%s')
        self.db(cmd, key)


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
        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
        slots = (','.join(['%s']*len(keys)))
        cmd = 'select distinct id from %s where id in (%s)' % (self.kind, slots)
        rs = self.db(cmd, *keys)

        found_keys = [rec[0] for rec in rs]
        if len(keys)>1:
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
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]

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
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]
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
        #TODO: add set values
        db = self.db
        all_keys = []
        items = kv.items()
        wc = ' and '.join('%s=%s'%(k,'%s') for k,v in items)
        cmd = 'select distinct id from '+self.kind+' where '+wc
        q = db(cmd, *[v for k,v in items])
        return [i[0] for i in q]

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
            >>> people.find(age=25)
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Bob', 'age': 25}>]
            >>> people.find(name='Sam')
            [<Person {'name': 'Sam', 'age': 25}>]

        """
        all_keys = []
        items = kv.items()
        wc = ' and '.join('%s=%s'%(k,'%s') for k,v in items)
        cmd = 'select * from '+self.kind+' where '+wc
        q = self.db(cmd, *[v for k,v in items])
        return Result(q, self.record_class)

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
        r = self._find(**kv)
        if r:
            return self.get(r[-1])
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
            >>> list(people.search('smi'))
            [<Person {'name': 'Sally Mary Smith', 'age': 55}>, <Person {'name': 'Bob Marvin Smith', 'age': 25}>]
            >>> list(people.search('bo smi'))
            [<Person {'name': 'Bob Marvin Smith', 'age': 25}>]
            >>> list(people.search('smi 55'))
            [<Person {'name': 'Sally Mary Smith', 'age': 55}>]

        """
        def matches(item, terms):
            v = [str(i).lower() for i in item.values()]
            return all(any(t in s for s in v) for t in terms)
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
            >>> list(people.filter(lambda a: a.age < 40))
            [<Person {'name': 'Sam Adam Jones', 'age': 25}>, <Person {'name': 'Bob Marvin Smith', 'age': 25}>]

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
        q = self.db(cmd)
        return ResultIter(q, self.record_class)

    def __getitem__(self, n):
        """
        gets nth item

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
        return self.all()[n]

    def __str__(self):
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
                id  age  name   
            ------- ---- ------ 
                 1  25   Sam    
                 2  55   Sally  
                 3  25   Bob    
            3 records
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
            >>> people
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Sally', 'age': 55}>, <Person {'name': 'Bob', 'age': 25}>]
            >>> people.zap()
            >>> people
            []

        """
        return repr(self.all())

def records(klass=dict):
    return RecordStore(db, klass)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

