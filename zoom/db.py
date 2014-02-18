"""
    db

    a database module that does less
"""

import MySQLdb
import warnings

ARRAY_SIZE = 1000

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
        return self.cursor.rowcount

    def __repr__(self):
        return repr(list(self))


class Database(object):
    """
    database object

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

        >>> from decimal import Decimal
        >>> amt = Decimal('1234.56')
        >>> db("insert into person (name, salary) values ('Pat',%s)", amt)
        2L

        >>> for r in db('select * from person'):
        ...     print r
        (1L, 'Joe', 32, None, None, None)
        (2L, 'Pat', None, None, None, Decimal('1234.56'))

        >>> db('select * from person where id=2')
        [(2L, 'Pat', None, None, None, Decimal('1234.56'))]

        >>> t = list(db('select * from person where id=2'))[0][-1]
        >>> t
        Decimal('1234.56')
        >>> assert amt == t

        >>> db('drop table person')
        0L
        >>> failed = False
        >>> try:
        ...     db('select * from person where id=2')
        ... except MySQLdb.ProgrammingError, m:
        ...     failed = True
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
        self.__debug = 0

    def __getattr__(self, name):
        if self.__connection is None:
            self.__connection = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__connection, name)

    def __call__(self, sql, *a, **k):
        cursor = self.cursor()

        if self.__debug:
            start = time.time()
        try:
            result = cursor.execute(sql, a)
        finally:
            if self.__debug:
                print 'SQL (%s): %s - %s<br>\n' % (time.time()-start, sql, args)

        if cursor.description:
            return Result(cursor)
        else:
            return cursor.lastrowid
    

def database(engine='mysql', host='database', db='test', user='testuser', *a, **k):

    if engine == 'mysql':
        db = Database(MySQLdb.connect, host=host, db=db, user=user, *a, **k)
        db.autocommit(1)
        return db


