"""
    a database that does less
"""

import timeit
import warnings
from exceptions import DatabaseException

ARRAY_SIZE = 1000

ERROR_TPL = """
  statement: {!r}
  parameters: {}
  message: {}
"""

def ResultIter(cursor, arraysize=ARRAY_SIZE):
    while True:
        results = cursor.fetchmany(arraysize)
        if not results:
            break
        for result in results:
            yield result


class Result(object):
    def __init__(self, cursor):
        self.cursor = cursor

    def __iter__(self):
        return ResultIter(self.cursor)

    def __len__(self):
        c = self.cursor.rowcount
        return c > 0 and c or 0

    def __str__(self):
        """nice for humans"""
        labels = [' %s '%i[0] for i in self.cursor.description]
        values = [[' %s ' % i for i in r] for r in self]
        allnum = [all(str(v[i][1:-1]).translate(None,'.').isdigit() for v in values) for i in range(len(labels))]
        widths = [max(len(v[i]) for v in [labels] + values) for i in range(len(labels))]
        fmt    = ' ' + ' '.join(['%' + (not allnum[i] and '-' or '') + '%ds' % w for i,w in enumerate(widths)])
        lines  = ['-' * (w) for w in widths]
        result = '\n'.join(fmt%tuple(i) for i in [labels] + [lines] + values)
        return result

    def __repr__(self):
        """useful and unabiguous"""
        return repr(list(self))

    def first(self):
        for i in self: return i


class Database(object):
    """
    database object

        >>> import MySQLdb
        >>> db = database(host='database', db='test', user='testuser', passwd='password')
        >>> db('drop table if exists person')
        0L
        >>> db(\"\"\"
        ...     create table if not exists person (
        ...     id int not null auto_increment,
        ...     name      varchar(100),
        ...     age       smallint,
        ...     kids      smallint,
        ...     birthdate date,
        ...     salary    decimal(8,2),
        ...     PRIMARY KEY (id)
        ...     )
        ... \"\"\")
        0L
        >>> for r in db('describe person'):
        ...     print r
        ('id', 'int(11)', 'NO', 'PRI', None, 'auto_increment')
        ('name', 'varchar(100)', 'YES', '', None, '')
        ('age', 'smallint(6)', 'YES', '', None, '')
        ('kids', 'smallint(6)', 'YES', '', None, '')
        ('birthdate', 'date', 'YES', '', None, '')
        ('salary', 'decimal(8,2)', 'YES', '', None, '')

        >>> db("insert into person (name, age) values ('Joe',32)")
        1L

        >>> db('select * from person')
        [(1L, 'Joe', 32, None, None, None)]

        >>> print db('select * from person')
          id   name   age   kids   birthdate   salary 
         ---- ------ ----- ------ ----------- --------
           1   Joe     32   None   None        None   

        >>> from decimal import Decimal
        >>> amt = Decimal('1234.56')
        >>> db("insert into person (name, salary) values ('Pat',%s)", amt)
        2L

        >>> for r in db('select * from person'):
        ...     print r
        (1L, 'Joe', 32, None, None, None)
        (2L, 'Pat', None, None, None, Decimal('1234.56'))

        >>> db('select * from person where id=%s', 2)
        [(2L, 'Pat', None, None, None, Decimal('1234.56'))]

        >>> t = list(db('select * from person where id=2'))[0][-1]
        >>> t
        Decimal('1234.56')
        >>> assert amt == t

        >>> db('select * from person where name in (%(buddy)s, %(pal)s)', {'buddy':'Pat', 'pal':'John'})
        [(2L, 'Pat', None, None, None, Decimal('1234.56'))]

        >>> db.execute_many("insert into person (name, salary) values (%s,%s)",
        ...     [['Alan', Decimal(5000)], ['Evan', Decimal(6000)]])
        3L
        >>> db.rowcount
        2L

        >>> q = db('select * from person')
        >>> db.rowcount
        4L

        >>> db('drop table person')
        0L
        >>> failed = False
        >>> try:
        ...     db('select * from person where id=2')
        ... except DatabaseException as e:
        ...     failed = True
        ...     print e
        <BLANKLINE>
          statement: 'select * from person where id=2'
          parameters: ()
          message: (1146, "Table 'test.person' doesn't exist")
        <BLANKLINE>

        >>> assert failed

        >>> try:
        ...     db('select * from not_a_table')
        ... except DatabaseException:
        ...     failed = True
        ...     print e
        <BLANKLINE>
          statement: 'select * from person where id=2'
          parameters: ()
          message: (1146, "Table 'test.person' doesn't exist")
        <BLANKLINE>
        >>> assert failed
    """

    def __init__(self, factory, *args, **keywords):
        """Initialize with factory method to generate DB connection
        (e.g. odbc.odbc, cx_Oracle.connect) plus any positional and/or
        keyword arguments required when factory is called."""
        self.__connection = None
        self.__factory = factory
        self.__args = args
        self.__keywords = keywords
        self.debug = False
        self.log = []

    def __getattr__(self, name):
        if self.__connection is None:
            self.__connection = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__connection, name)

    def __call__(self, sql, *a):
        cursor = self.cursor()

        start = timeit.default_timer()
        params = len(a)==1 and hasattr(a[0],'items') and a[0] or a
        try:
            result = cursor.execute(sql, params)
        except Exception as e:
            raise DatabaseException(ERROR_TPL.format(sql, a, e))
        else:
            self.rowcount = cursor.rowcount
        finally:
            if self.debug:
                self.log.append('  SQL ({:5.1f} ms): {!r} - {!r}'.format(
                    (timeit.default_timer() - start) * 1000,
                    sql,
                    a,
                ))

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = getattr(cursor, 'lastrowid', None)
            return self.lastrowid

    def execute_many(self, sql, *a):
        cursor = self.cursor()

        start = timeit.default_timer()
        try:
            result = cursor.executemany(sql, *a)
        except Exception as e:
            raise DatabaseException(ERROR_TPL.format(sql, a, e))
        else:
            self.rowcount = cursor.rowcount
        finally:
            if self.debug:
                self.log.append('  SQL ({:5.1f} ms): {!r} - {!r}'.format(
                    (timeit.default_timer() - start) * 1000,
                    sql,
                    a,
                ))

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = getattr(cursor, 'lastrowid', None)
            return self.lastrowid

    def use(self, name):
        """use another database on the same instance"""
        args = list(self.__args)
        keywords = dict(self.__keywords, db=name)
        return Database(self.__factory, *args, **keywords)

    def report(self):
        if self.log:
            return '  DB Queries\n --------------------\n{}\n'.format(
                '\n'.join(self.log))
        return ''


def database(engine='mysql', host='database', db='test', user='testuser', *a, **k):

    if engine == 'mysql':
        import MySQLdb
        db = Database(MySQLdb.connect, host=host, db=db, user=user, *a, **k)
        db.autocommit(1)
        return db

    elif engine == 'sqlite':
        import sqlite3
        db = Database(sqlite3.connect, database=db, *a, **k)
        return db

    elif engine == 'pymysql':
        import pymysql
        db = Database(pymysql.connect, host=host, db=db, user=user, charset='utf8', *a, **k)
        db.autocommit(1)
        return db

    elif engine == 'pymysql_back':
        """ pymysql engine with mysqldb/dz backwards compatibility

            This is mainly done for tests, running dz tests, unchanged, under pymysql
        """
        import pymysql
        from pymysql.converters import conversions
        from pymysql.constants import FIELD_TYPE
        from pymysql.cursors import Cursor
        class LegacyCursor(Cursor):
            def __getattribute__(self, name):
                r = object.__getattribute__(self, name)
                if name == 'lastrowid': r = long(r)
                return r

        mysqldb_compat = conversions.copy()
        mysqldb_compat[FIELD_TYPE.LONG] = long
        mysqldb_compat[FIELD_TYPE.LONGLONG] = long
        db = Database(pymysql.connect, host=host, db=db, user=user, conv=mysqldb_compat, charset='latin1', use_unicode=False, cursorclass=LegacyCursor, *a, **k)
        db.autocommit(1)

        return db

