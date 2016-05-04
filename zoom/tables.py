"""
    key value store
"""

import datetime
from zoom.utils import Record
from zoom.store import ValidException, TypeException, Entity, EntityList, kind

def create_tables(db):
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

def delete_tables(db):
    db('drop table if exists person')

def setup_test():
    import MySQLdb, database
    #from system import system
    db = database.Database(
            MySQLdb.Connect, 
            host='database',
            db='test',
            user='testuser',
            passwd='password')
    delete_tables(db)
    create_tables(db)
    return db

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


    def __init__(self, db, entity_class=dict):
        self.db = db
        self.entity_class = entity_class
        self.kind = kind(entity_class())

    def put(self, entity):
        """
        stores an record

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


        keys        = [k for k in entity.keys() if k <> '_id']
        values      = [entity[k] for k in keys]
        datatypes   = [repr(type(i)).strip("<type >").strip("'") for i in values]
        values      = [i for i in values]
        valid_types = ['str','unicode','long','int','float','datetime.date','datetime.datetime','bool','NoneType']

        db = self.db

        for atype in datatypes:
            if atype not in valid_types:
                raise TypeException,'unsupported type <type %s>' % atype

        if '_id' in entity:
            id = entity['_id']
            sc = ', '.join('%s=%s' % (i,'%s') for i in keys)
            cmd = 'update %s set %s where id=%d' % (self.kind, sc, id)
            db(cmd, *values) 
        else:
            kc = ', '.join(keys)
            placeholders = ','.join(['%s'] * len(keys))
            cmd = 'insert into %s (%s) values (%s)' % (self.kind, kc, placeholders)
            db(cmd, *values)
            id = entity['_id'] = db.lastrowid

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

        """
        def rec_to_dict(rec):
            return self.entity_class(dict((k=='ID' and '_id' or k.lower(),v) for k,v in rec.as_dict().items() if v != None))

        if keys == None: return None

        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
            as_list = 0
        else:
            as_list = 1
        keys = [long(key) for key in keys]

        if not keys:
            if as_list:
                return []
            else:
                return None

        db = self.db

        cmd = 'select * from '+self.kind+' where id in (%s)' % (','.join(['%s']*len(keys)))
        q = db(cmd, *keys)

        if len(q) > 1:
            return [rec_to_dict(i) for i in q]
        elif len(q) == 1:
            if as_list:
                return [rec_to_dict(q[0])]
            else:
                return rec_to_dict(q[0])


    def get_attributes(self):
        """
        get complete set of attributes for the entity type

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
        values = [rec.FIELD for rec in rs if rec.FIELD != 'id']
        return values


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
        tests for existence of an entity

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

        found_keys = [rec.ID for rec in rs]
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
        cmd = 'select id from '+self.kind
        rs = self.db(cmd)
        keys = [rec.ID for rec in rs]
        return self.get(keys) or EntityList()

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
        return int(self.db(cmd)[0].CNT)

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
        return [i.ID for i in q]

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
        return self.get(self._find(**kv))

    def first(self, **kv):
        """
        finds the first entity that meet search criteria

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
        r = self._find(**kv)
        if r:
            return self.get(r[0])
        return None

    def last(self, **kv):
        """
        finds the last entity that meet search criteria

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

    def __iter__(self):
        return self.all()

    def __getitem__(self, n):
        return self.all()[n]

    def __repr__(self):
        return str(self.all())

def table(klass=dict):
    return RecordStore(db, klass)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

