"""
    record store

    EXPERIMENTAL!
"""

import datetime
from zoom.utils import Record

class ValidException(Exception): pass
class TypeException(Exception): pass

def kind(o):
    """
    returns the kind of object passed
    """
    n = []
    for c in o.__class__.__name__:
        if c.isalpha() or c=='_':
            if c.isupper() and len(n):
                n.append('_')
            n.append(c.lower())
    return ''.join(n)

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

    import MySQLdb, database, db

    db = db.Database(
            MySQLdb.Connect, 
            host='database',
            db='test',
            user='testuser',
            passwd='password')
    delete_test_tables(db)
    create_test_tables(db)
    return db


class RecordList(list):
    """
        A list with some convenience methods for Records
    """
    def __str__(self):
        """
        represent as a string 

            >>> db = setup_test()
            >>> class Person(Record): pass
            >>> class People(RecordStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Joe', age=20, birthdate=datetime.date(1992,5,5)))
            >>> id = people.put(Person(name='Samuel', age=25, birthdate=datetime.date(1992,4,5)))
            >>> id = people.put(Person(name='Sam', age=35, birthdate=datetime.date(1992,3,5)))
            >>> print people
            person
                id  age  name    birthdate   
            ------- ---- ------- ----------- 
                 1  20   Joe     1992-05-05  
                 2  25   Samuel  1992-04-05  
                 3  35   Sam     1992-03-05  
            3 records

        """
        if len(self)==0:
            return 'Empty list'
        title=['%s\n    id  ' % kind(self[0])]
        lines =['------- ']
        fmtstr = ['%6d  ']

        data_lengths = {}
        for rec in self:
            for field in self[0].keys():
                n = data_lengths.get(field, 0)
                m = len('%s' % rec.get(field, ''))
                if n < m:
                    data_lengths[field] = m

        fields = data_lengths.keys()
        d = data_lengths
        fields.sort(lambda a,b:not d[a] and -999 or not d[b] and -999 or d[a]-d[b])
        if '_id' in fields:
            fields.remove('_id')
            fields.insert(0, '_id')

        for field in fields[1:]:
            width = max(len(field),d[field])+1
            fmt = '%-' + ('%ds ' % width)
            fmtstr.append(fmt)
            title.append(fmt % field)
            lines.append(('-' * width) + ' ')
        fmtstr.append('')
        lines.append('\n')
        title.append('\n')
        t = []
        fmtstr = ''.join(fmtstr)

        for rec in self:
            values = [rec.get(key) for key in fields]
            t.append(''.join(fmtstr) % tuple(values))
        return ''.join(title) + ''.join(lines) + '\n'.join(t) + ('\n%s records' % len(self))

    def __init__(self, *a, **k):
        list.__init__(self, *a, **k)
        self._n = 0

    def __iter__(self):
        self._n = 0
        return self

    def next(self):
        if self._n >= len(self):
            raise StopIteration
        else:
            result = self[self._n]
            self._n += 1
        return result


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

    def rec_to_obj(self, names, rec):
        d = zip(names, rec)
        return self.record_class(dict((k=='id' and '_id' or k.lower(),v) for k,v in d if v != None))

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

        """
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

        result = None
        if len(q) > 1:
            result = RecordList()
            for rec in q:
                names = [d[0] for d in q.cursor.description]
                result.append(self.rec_to_obj(names,rec))

        elif len(q) == 1:
            rec = q.cursor.fetchone()
            if as_list:
                result = RecordList()
                names = [d[0] for d in q.cursor.description]
                result.append(self.rec_to_obj(names, rec))
            else:
                names = [d[0] for d in q.cursor.description]
                result = self.rec_to_obj(names, rec)

        return result


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

    def __iter__(self):
        cmd = 'select * from '+self.kind
        q = self.db(cmd)
        names = [d[0] for d in q.cursor.description]
        for rec in q:
            yield self.rec_to_obj(names, rec)

    def __getitem__(self, n):
        return self.all()[n]

    def __repr__(self):
        return str(self.all())

def records(klass=dict):
    return RecordStore(db, klass)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

