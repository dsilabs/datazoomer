"""
    a database that does less
"""

import timeit

from zoom.exceptions import DatabaseException
from zoom.utils import ItemList


ARRAY_SIZE = 1000

ERROR_TPL = """
  statement: {!r}
  parameters: {}
  message: {}
"""


class Result(object):
    """database query result"""
    # pylint: disable=too-few-public-methods

    def __init__(self, cursor, array_size=ARRAY_SIZE):
        self.cursor = cursor
        self.array_size = array_size

    def __iter__(self):
        while True:
            results = self.cursor.fetchmany(self.array_size)
            if not results:
                break
            for result in results:
                yield result

    def __len__(self):
        # deprecate? - not supported by all databases
        count = self.cursor.rowcount
        return count > 0 and count or 0

    def __str__(self):
        """nice for humans"""
        labels = map(lambda a: '{0}'.format(*a), self.cursor.description)
        return str(ItemList(self, labels=labels))

    def __repr__(self):
        """useful and unabiguous"""
        return repr(list(self))

    def first(self):
        """return first item in result"""
        for i in self:
            return i


class Database(object):
    # pylint: disable=trailing-whitespace
    """
    database object

        >>> import MySQLdb
        >>> db = database(
        ...     host='database',
        ...     db='test',
        ...     user='testuser',
        ...     passwd='password'
        ... )
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
        id name age kids birthdate salary
        -- ---- --- ---- --------- ------
         1 Joe   32 None None      None

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

        >>> db('select * from person where name in (%(buddy)s, %(pal)s)',
        ...     {'buddy':'Pat', 'pal':'John'})
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
    # pylint: disable=too-many-instance-attributes

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
        self.rowcount = None
        self.lastrowid = None

    def __getattr__(self, name):
        if self.__connection is None:
            self.__connection = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__connection, name)

    def _execute(self, cursor, method, command, *args):
        """execute the SQL command"""
        start = timeit.default_timer()
        params = len(args) == 1 and \
                hasattr(args[0], 'items') and \
                args[0] or \
                args
        try:
            method(command, params)
        except Exception as error:
            raise DatabaseException(ERROR_TPL.format(command, args, error))
        else:
            self.rowcount = cursor.rowcount
        finally:
            if self.debug:
                self.log.append('  SQL ({:5.1f} ms): {!r} - {!r}'.format(
                    (timeit.default_timer() - start) * 1000,
                    command,
                    args,
                ))

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = getattr(cursor, 'lastrowid', None)
            return self.lastrowid

    def execute(self, command, *args):
        """execute a SQL command with optional parameters"""
        cursor = self.cursor()
        return self._execute(cursor, cursor.execute, command, *args)

    def execute_many(self, command, sequence):
        """execute a SQL command with a sequence of parameters"""
        # pylint: disable=star-args
        cursor = self.cursor()
        return self._execute(cursor, cursor.executemany, command, *sequence)

    def __call__(self, command, *args):
        return self.execute(command, *args)

    def use(self, name):
        """use another database on the same instance"""
        # pylint: disable=star-args
        args = list(self.__args)
        keywords = dict(self.__keywords, db=name)
        return Database(self.__factory, *args, **keywords)

    def report(self):
        """produce a SQL log report"""
        if self.log:
            return '  DB Queries\n --------------------\n{}\n'.format(
                '\n'.join(self.log))
        return ''

def database(
    engine='mysql',
    host='database',
    db='test',
    user='testuser',
    *a,
    **k
):
    """create a database object"""
    # pylint: disable=invalid-name

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
        db = Database(
            pymysql.connect,
            host=host,
            db=db,
            user=user,
            charset='utf8',
            *a,
            **k
        )
        db.autocommit(1)
        return db

    elif engine == 'pymysql_back':
        # pymysql engine with mysqldb/dz backwards compatibility
        # This is mainly done for tests, running dz tests, unchanged, under
        # pymysql
        import pymysql
        from pymysql.converters import conversions
        from pymysql.constants import FIELD_TYPE
        from pymysql.cursors import Cursor
        class LegacyCursor(Cursor):
            """MySQLdb combatible cursor"""
            def __getattribute__(self, name):
                r = object.__getattribute__(self, name)
                if name == 'lastrowid':
                    r = long(r)
                return r

        mysqldb_compat = conversions.copy()
        mysqldb_compat[FIELD_TYPE.LONG] = long
        mysqldb_compat[FIELD_TYPE.LONGLONG] = long
        db = Database(
            pymysql.connect,
            host=host,
            db=db,
            user=user,
            conv=mysqldb_compat,
            charset='latin1',
            use_unicode=False,
            cursorclass=LegacyCursor,
            *a,
            **k
        )
        db.autocommit(1)

        return db
