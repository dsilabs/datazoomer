"""
    key value store
"""

import datetime
import decimal
from zoom.utils import Record, RecordList, kind
from zoom.tools import db


class ValidException(Exception): pass
class TypeException(Exception): pass


def create_storage(db):
    db("""
    create table if not exists entities (
        id int not null auto_increment,
        kind      varchar(100),
        PRIMARY KEY (id)
        )
    """)
    db("""
    create table if not exists attributes (
        id int not null auto_increment,
        kind      varchar(100),
        row_id    int not null,
        attribute varchar(100),
        datatype  varchar(30),
        value     text,
        PRIMARY KEY (id)
        )
    """)


def delete_storage(db):
    db('drop table if exists attributes')
    db('drop table if exists entities')


def setup_test():
    import MySQLdb, db as database

    db = database.Database(
            MySQLdb.Connect, 
            host='database',
            db='test',
            user='testuser',
            passwd='password')
    db.autocommit(1)
    delete_storage(db)
    create_storage(db)
    return db


class Entity(Record):
    """any thing that works like a dict will do"""
    pass


class EntityList(RecordList):
    """a list of Entities"""
    pass


def entify(rs, klass):
    """
    converts query result into an EntityList
    """
    entities = {}

    if hasattr(rs, 'data'): # maintain backward compatibility with
        rs = rs.data        # legacy database module

    for _, _, row_id, attribute, datatype, value in rs:

        if datatype == 'str':
            pass

        elif datatype == 'unicode' and isinstance(value, unicode):
            pass

        elif datatype == 'unicode':
            value = value.decode('utf8')

        elif datatype == "long":
            value = long(value)

        elif datatype == "int":
            value = int(value)

        elif datatype == 'float':
            value = float(value)

        elif datatype == 'decimal.Decimal':
            value = decimal.Decimal(value)

        elif datatype == "datetime.date":
            y = int(value[:4])
            m = int(value[5:7])
            d = int(value[8:10])
            value = datetime.date(y,m,d)

        elif datatype == "datetime.datetime":
            y = int(value[:4])
            m = int(value[5:7])
            d = int(value[8:10])
            hr = int(value[11:13])
            mn = int(value[14:16])
            sc = int(value[17:19])
            value = datetime.datetime(y,m,d,hr,mn,sc)

        elif datatype == 'bool':
            value = (value == '1' or value == 'True')

        elif datatype == 'NoneType':
            value = None

        elif datatype == 'instance':
            value = long(rec.id)

        else:
            raise TypeException,'unsupported data type: ' + repr(datatype)

        entities.setdefault(row_id, klass(_id=row_id))[attribute] = value

    return EntityList(entities.values())


class EntityStore(object):
    """
    stores entities

        >>> db = setup_test()

        >>> stuff = EntityStore(db)
        >>> stuff.put(dict(name='Joe', age=14))
        1L
        >>> stuff.put(dict(name='Sally', age=34))
        2L
        >>> stuff.put(dict(name='Sam', age=34))
        3L
        >>> stuff.find(name='Joe')
        [{'age': 14, '_id': 1L, 'name': 'Joe'}]
        >>> s = stuff.find(age=34)
        >>> print s
        dict
            id  age  name   
        ------- ---- ------ 
             2  34   Sally  
             3  34   Sam    
        2 records


        >>> db = setup_test()
        >>> class Person(Entity): pass
        >>> class People(EntityStore): pass
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

        >>> class Misc(EntityStore): pass
        >>> misc = Misc(db, dict)
        >>> config_info = dict(host='database', name='somename')
        >>> id = misc.put(config_info)
        >>> x = misc.put(dict(other='this',stuff='that'))
        >>> my_info = misc.get(id)
        >>> my_info
        {'host': 'database', '_id': 3L, 'name': 'somename'}
        >>> misc.get(x)
        {'_id': 4L, 'other': 'this', 'stuff': 'that'}

        >>> people = EntityStore(db, 'person')
        >>> people.klass
        <type 'dict'>
        >>> people.kind
        'person'
        >>> people.first(name='Sally')
        {'_id': 2L, 'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 3}
        >>> Person(people.first(name='Sally'))
        <Person {'name': 'Sally', 'birthdate': datetime.date(1992, 5, 5), 'kids': 3}>
        >>> EntityStore(db, 'person').first(name='Joe')['age']
        20
        >>> from utils import PY2
        >>> name = PY2 and unicode('somename') or str('somename')
        >>> id = misc.put(dict(host='database', name=name))
        >>> my_info = misc.get(id)
        >>> assert type(my_info['name'])==type(name)

    """

    def __init__(self, db, klass=dict):
        self.db = db
        self.klass = type(klass) == str and dict or klass
        self.kind = type(klass) == str and klass or kind(klass())

    def put(self, entity):
        """
        stores an entity

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
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
            >>> db.close()

        """
        def fixval(d):
            if type(d) == datetime.datetime:
                # avoids mysqldb reliance on strftime that lacks support for dates before 1900
                return "%02d-%02d-%02d %02d:%02d:%02d" % (d.year,d.month,d.day,d.hour,d.minute,d.second)
            if type(d) == decimal.Decimal:
                return str(d)
            else:
                return d                

        def get_type_str(v):
            t = repr(type(v))
            if 'type' in t:
                return t.strip('<type >').strip("'")
            elif 'class' in t:
                return t.strip('<class >').strip("'")
            else:
                return t

        db = self.db
    
        keys        = [k for k in entity.keys() if k <> '_id']
        values      = [entity[k] for k in keys]
        datatypes   = [get_type_str(v) for v in values]
        values      = [fixval(i) for i in values] # same fix as above
        valid_types = ['str','unicode','long','int','float','decimal.Decimal','datetime.date','datetime.datetime','bool','NoneType']

        for atype in datatypes:
            if atype not in valid_types:
                raise TypeException,'unsupported type <type %s>' % atype

        if '_id' in entity:
            id = entity['_id']
            db('delete from attributes where row_id=%s', id)
        else:
            db('insert into entities (kind) values (%s)', self.kind)
            id = entity['_id'] = db.lastrowid

        n = len(keys)
        lkeys = [k.lower() for k in keys]
        param_list = zip([self.kind]*n, [id]*n, lkeys, datatypes, values)
        cmd = 'insert into attributes (kind, row_id, attribute, datatype, value) values (%s,%s,%s,%s,%s)'
        db.cursor().executemany(cmd, param_list)

        return id


    def get(self, keys):
        """
        retrives entities

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(**{'name': 'Sam', 'age':15, 'salary': decimal.Decimal('100.00')}))
            >>> sam = people.get(id)
            >>> sam
            <Person {'name': 'Sam', 'age': 15, 'salary': Decimal('100.00')}>
            >>> db.close()

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

        cmd = 'select * from attributes where kind=%s and row_id in (%s)' % ('%s',','.join(['%s']*len(keys)))
        rs = self.db(cmd, self.kind, *keys)

        result = entify(rs, self.klass)

        if as_list:
            return result
        if result:
            return result[0]


    def get_attributes(self):
        """
        get complete set of attributes for the entity type

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> sam = Person(**{'name': 'Sam', 'age':15})
            >>> sam.keys()
            ['age', 'name']
            >>> id = people.put(sam)
            >>> people.get_attributes()
            ['name', 'age']
            >>> db.close()

        """
        # order by id desc so that newly introduced attributes appear at the end of the keys list
        cmd = 'select distinct attribute from attributes where kind=%s order by id desc'
        rs = self.db(cmd, self.kind)
        values = [rec[0] for rec in rs]
        return values


    def delete(self, key):
        """
        delete an entity

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
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
            >>> db.close()

        """
        if hasattr(key, 'get'):
            key = key['_id']
        cmd = 'delete from attributes where row_id=%s'
        self.db(cmd, key)
        cmd = 'delete from entities where id=%s'
        self.db(cmd, key)


    def exists(self, keys=None):
        """
        tests for existence of an entity

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
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
            >>> db.close()

        """
        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
        slots = (','.join(['%s']*len(keys)))
        cmd = 'select distinct row_id from attributes where row_id in (%s)' % slots
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
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]
            >>> db.close()

        """
        cmd = 'select * from attributes where kind="%s"' % (self.kind)
        return entify(self.db(cmd), self.klass)

    def zap(self):
        """
        deletes all entities of the given kind
        
            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]
            >>> people.zap()
            >>> people.all()
            []
            >>> db.close()

        """
        cmd = 'delete from attributes where kind=%s'
        self.db(cmd, self.kind)
        cmd = 'delete from entities where kind=%s'
        self.db(cmd, self.kind)

    def __len__(self):
        """
        returns number of entities

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> len(people)
            0
            >>> id = people.put(Person(name='Sam', age=15))
            >>> id = people.put(Person(name='Sally', age=25))
            >>> len(people)
            2
            >>> db.close()

        """
        cmd = 'select count(*) n from (select distinct row_id from attributes where kind=%s) a'
        r = self.db(cmd, self.kind)
        return int(list(r)[0][0])

    def _find(self, **kv):
        """
        Find keys that meet search critieria
        """
        db = self.db
        all_keys = []
        for field_name in kv.keys():
            value = kv[field_name]
            if value != None:
                if not isinstance(value, (list, tuple)):
                    wc = 'value=%s'
                    v = (value,)
                else:
                    wc = 'value in ('+','.join(['%s']*len(value))+')'
                    v = value
                cmd = 'select distinct row_id from attributes where kind=%s and attribute=%s and '+wc
                rs = db(cmd, self.kind, field_name.lower(), *v)
                all_keys.append([rec[0] for rec in rs])
        answer = set(all_keys[0])
        for keys in all_keys[1:]:
            answer = set(keys) & answer
        if answer:
            return list(answer)
        else:
            return []

    def find(self, **kv):
        """
        finds entities that meet search criteria

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.find(age=25)
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Bob', 'age': 25}>]
            >>> db.close()

        """
        return self.get(self._find(**kv))

    def first(self, **kv):
        """
        finds the first entity that meet search criteria

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.first(age=5)
            >>> people.first(age=25)
            <Person {'name': 'Sam', 'age': 25}>
            >>> db.close()

        """
        r = self._find(**kv)
        if r:
            return self.get(r[0])
        return None

    def last(self, **kv):
        """
        finds the last entity that meet search criteria

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.last(age=5)
            >>> people.last(age=25)
            <Person {'name': 'Bob', 'age': 25}>
            >>> db.close()

        """
        r = self._find(**kv)
        if r:
            return self.get(r[-1])
        return None

    def search(self, text):
        """
        search for entities that match text

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))

            >>> list(people.search('bob'))
            [<Person {'name': 'Bob', 'age': 25}>]

            >>> list(people.search(25))
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Bob', 'age': 25}>]

            >>> list(people.search('Bill'))
            []
            >>> db.close()

        """
        t = unicode(text).lower()
        for rec in self:
            if t in repr(rec.values()).lower():
                yield rec

    def __iter__(self):
        return self.all()

    def __getitem__(self, key):
        """
        return entities or slices of entities by position

            >>> db = setup_test()
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))

            >>> people[0]
            <Person {'name': 'Sam', 'age': 25}>

            >>> people[1]
            <Person {'name': 'Sally', 'age': 55}>

            >>> people[-1]
            <Person {'name': 'Bob', 'age': 25}>

            >>> people[0:2]
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Sally', 'age': 55}>]

            >>> people[::2]
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Bob', 'age': 25}>]

            >>> people[::-2]
            [<Person {'name': 'Bob', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>]

            >>> people[1:-1]
            [<Person {'name': 'Sally', 'age': 55}>]

            >>> try:
            ...     people[3]
            ... except IndexError, e:
            ...     print e
            Index (3) out of range

            >>> db.close()

        """
        n = len(self)
        if isinstance(key, slice):
            # get the start, stop, and step from the slice
            start, stop, step = key.indices(n)
            return [self[ii] for ii in xrange(start, stop, step)]
        elif isinstance(key, int):
            if key<0:
                key += n
            elif key >= n:
                raise IndexError, 'Index ({}) out of range'.format(key)
            cmd = 'select distinct row_id from attributes where kind="%s" limit %s,1' % (self.kind, key)
            rs = self.db(cmd)
            if rs:
                return self.get(list(rs)[0][0])
            else:
                return 'no records'
        else:
            raise TypeError, 'Invalid argument type'

    def __repr__(self):
        return repr(self.all())

    def __str__(self):
        return str(self.all())

Store = EntityStore

def store(klass=dict):
    return EntityStore(db, klass)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

