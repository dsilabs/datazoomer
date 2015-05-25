"""
    a database that does less
"""

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
            result = cursor.execute(sql, len(a)==1 and hasattr(a[0],'items') and a[0] or a)
        finally:
            if self.__debug:
                print 'SQL (%s): %s - %s<br>\n' % (time.time()-start, sql, args)

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = cursor.lastrowid
            return self.lastrowid

    def execute_many(self, sql, *a):
        cursor = self.cursor()

        if self.__debug:
            start = time.time()
        try:
            result = cursor.executemany(sql, *a)
        finally:
            if self.__debug:
                print 'SQL (%s): %s - %s<br>\n' % (time.time()-start, sql, a)

        if cursor.description:
            return Result(cursor)
        else:
            self.lastrowid = cursor.lastrowid
            return self.lastrowid


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


def get_mysql_log_state():
    for rec in db('show variables like "log"'):
        return rec[1]

def set_mysql_log_state(new_state):
    if new_state in ['ON','OFF']:
        db('SET GLOBAL general_log = %s;', new_state)


