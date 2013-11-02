"""
    key value store
"""

import datetime
import decimal
from zoom.utils import Record
from zoom.tools import db

class ValidException(Exception): pass
class TypeException(Exception): pass

def create_tables(db):
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

def delete_tables(db):
    db('drop table if exists attributes')
    db('drop table if exists entities')


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


class Entity(Record):
    """any thing that works like a dict will do"""
    pass


class EntityList(list):
    """
    A list with some convenience methods for Entities
    """
    def __str__(self):
        """
        represent as a string 

            >>> import MySQLdb
            >>> from database import Database
            >>> db = Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Joe', age=20, birthdate=datetime.date(1992,5,5)))
            >>> id = people.put(Person(name='Samuel', age=25, birthdate=datetime.date(1992,4,5)))
            >>> id = people.put(Person(name='Sam', age=35, birthdate=datetime.date(1992,3,5)))
            >>> print people.all()
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
            for field in rec.keys():
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

    def __init__(self):
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


class EntityStore:
    """
    stores entities

        >>> import MySQLdb
        >>> from database import Database
        >>> db = Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
        >>> delete_tables(db)
        >>> create_tables(db)
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



    """

    def __init__(self, db, entity_class=dict):
        self.db = db
        self.entity_class = entity_class
        self.kind = kind(entity_class())

    def put(self, entity):
        """
        stores an entity

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
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

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(**{'name': 'Sam', 'age':15, 'salary': decimal.Decimal('100.00')}))
            >>> sam = people.get(id)
            >>> sam
            <Person {'name': 'Sam', 'age': 15, 'salary': Decimal('100.00')}>

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

        cmd = 'select * from attributes where kind=%s and row_id in (%s)' % ('%s',','.join(['%s']*len(keys)))
        entities = {}
        rs = db(cmd, self.kind, *keys)

        for rec in rs:
            row_id = rec.ROW_ID
            attribute = rec.ATTRIBUTE.lower()

            if rec.DATATYPE == "str":
                value = rec.VALUE

            elif rec.DATATYPE == 'unicode':
                value = rec.VALUE                

            elif rec.DATATYPE == "long":
                value = long(rec.VALUE)

            elif rec.DATATYPE == "int":
                value = int(rec.VALUE)

            elif rec.DATATYPE == 'float':
                value = float(rec.VALUE)

            elif rec.DATATYPE == 'decimal.Decimal':
                value = decimal.Decimal(rec.VALUE)

            elif rec.DATATYPE == "datetime.date":
                y = int(rec.VALUE[:4])
                m = int(rec.VALUE[5:7])
                d = int(rec.VALUE[8:10])
                import datetime
                value = datetime.date(y,m,d)

            elif rec.DATATYPE == "datetime.datetime":
                y = int(rec.VALUE[:4])
                m = int(rec.VALUE[5:7])
                d = int(rec.VALUE[8:10])
                hr = int(rec.VALUE[11:13])
                mn = int(rec.VALUE[14:16])
                sc = int(rec.VALUE[17:19])
                import datetime
                value = datetime.datetime(y,m,d,hr,mn,sc)

            elif rec.DATATYPE == 'bool':
                value = (rec.VALUE == '1' or rec.VALUE == 'True')

            elif rec.DATATYPE == 'NoneType':
                value = None

            elif rec.DATATYPE == 'instance':
                value = long(rec.id)

            else:
                raise TypeException,'unsupported data type' + repr(rec.__dict__)
                value = rec.VALUE

            #entities.setdefault(row_id, self.entity_class())[attribute] = value
            entities.setdefault(row_id, self.entity_class(_id=row_id))[attribute] = value

        #print entities

        if len(keys)>1:
            result = EntityList()
            for id in keys: 
                result.append(entities.get(id))
        else:
            if as_list:
                result = EntityList()
                result.append(entities.get(keys[0]))
            else:
                result = entities.get(keys[0])

        return result


    def get_attributes(self):
        """
        get complete set of attributes for the entity type

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> sam = Person(**{'name': 'Sam', 'age':15})
            >>> sam.keys()
            ['age', 'name']
            >>> id = people.put(sam)
            >>> people.get_attributes()
            ['name', 'age']

        """
        # order by id desc so that newly introduced attributes appear at the end of the keys list
        cmd = 'select distinct attribute from attributes where kind=%s order by id desc'
        rs = self.db(cmd, self.kind)
        values = [rec.ATTRIBUTE for rec in rs]
        return values


    def delete(self, key):
        """
        delete an entity

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
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

        """
        if hasattr(key, 'get'):
            key = key._id
        cmd = 'delete from attributes where row_id=%s'
        self.db(cmd, key)
        cmd = 'delete from entities where id=%s'
        self.db(cmd, key)


    def exists(self, keys=None):
        """
        tests for existence of an entity

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
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

        """
        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
        slots = (','.join(['%s']*len(keys)))
        cmd = 'select distinct row_id from attributes where row_id in (%s)' % slots
        rs = self.db(cmd, *keys)

        found_keys = [rec.ROW_ID for rec in rs]
        if len(keys)>1:
            result = [(key in found_keys) for key in keys]
        else:
            result = keys[0] in found_keys
        return result


    def all(self):
        """
        Retrieves all entities

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sally', age=25))
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Joe', age=25))
            >>> people.all()
            [<Person {'name': 'Sally', 'age': 25}>, <Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Joe', 'age': 25}>]

        """
        cmd = 'select distinct row_id from attributes where kind="%s"' % (self.kind)
        rs = self.db(cmd)
        keys = [rec.ROW_ID for rec in rs]
        return self.get(keys) or EntityList()

    def zap(self):
        """
        deletes all entities of the given kind
        
            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
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

        """
        cmd = 'delete from attributes where kind=%s'
        self.db(cmd, self.kind)
        cmd = 'delete from entities where kind=%s'
        self.db(cmd, self.kind)

    def __len__(self):
        """
        returns number of entities

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> len(people)
            0
            >>> id = people.put(Person(name='Sam', age=15))
            >>> id = people.put(Person(name='Sally', age=25))
            >>> len(people)
            2

        """
        cmd = 'select count(*) n from (select distinct row_id from attributes where kind=%s) a'
        r = self.db(cmd, self.kind)
        return int(r[0].N)

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
                all_keys.append([rec.ROW_ID for rec in rs])
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

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
            >>> people = People(db, Person)
            >>> id = people.put(Person(name='Sam', age=25))
            >>> id = people.put(Person(name='Sally', age=55))
            >>> id = people.put(Person(name='Bob', age=25))
            >>> people.find(age=25)
            [<Person {'name': 'Sam', 'age': 25}>, <Person {'name': 'Bob', 'age': 25}>]

        """
        return self.get(self._find(**kv))

    def first(self, **kv):
        """
        finds the first entity that meet search criteria

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
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

            >>> import MySQLdb, database
            >>> db = database.Database(MySQLdb.Connect, host='database',db='test',user='testuser',passwd='password')
            >>> delete_tables(db)
            >>> create_tables(db)
            >>> class Person(Entity): pass
            >>> class People(EntityStore): pass
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
        if n<0 or n>len(self)-1:
            raise Exception('Invalid value for n: %s' % n)
        cmd = 'select distinct row_id from attributes where kind="%s" limit %s,1' % (self.kind, n)
        rs = self.db(cmd)
        if rs:
            return self.get(rs[0].ROW_ID)

    def __repr__(self):
        return str(self.all())

Store = EntityStore

def store(klass=dict):
    return EntityStore(db, klass)

if __name__ == '__main__':
    import doctest
    doctest.testmod()

