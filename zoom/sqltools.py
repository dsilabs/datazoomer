"""
    sqltools.py
    experimental!

    note: currently designed to work with mysql and cousins only
"""

import itertools
from math import ceil

__all__ = ['summarize']

def setup_test():
    """setup test"""
    # pylint: disable=invalid-name
    def create_test_tables(db):
        """create test tables"""
        db("""
        create table if not exists person (
            id int not null auto_increment,
            name      varchar(100),
            age       smallint,
            kids      smallint,
            salary    decimal(10,2),
            birthdate date,
            PRIMARY KEY (id)
            )
        """)

    def delete_test_tables(db):
        """drop test tables"""
        db('drop table if exists person')

    import MySQLdb
    from zoom.db import Database

    db = Database(
            MySQLdb.Connect,
            host='database',
            db='test',
            user='testuser',
            passwd='password')
    db.autocommit(1)
    delete_test_tables(db)
    create_test_tables(db)
    return db

# pylint: disable=trailing-whitespace
def summarize(table, dimensions, metrics=None):
    """
    summarize a table

    >>> from records import Record, RecordStore
    >>> from decimal import Decimal
    >>> db = setup_test()
    >>> class Person(Record): pass
    >>> class People(RecordStore): pass
    >>> people = People(db, Person)
    >>> put = people.put
    >>> id = put(Person(name='Sam', age=25, kids=1, salary=Decimal('40000')))
    >>> id = put(Person(name='Sally', age=55, kids=4, salary=Decimal('80000')))
    >>> id = put(Person(name='Bob', age=25, kids=2, salary=Decimal('70000')))
    >>> id = put(Person(name='Jane', age=25, kids=2, salary=Decimal('50000')))
    >>> id = put(Person(name='Alex', age=25, kids=3, salary=Decimal('50000')))
    >>> print people
    person
    _id name  age kids salary
    --- ----- --- ---- ---------
      1 Sam    25    1 40,000.00
      2 Sally  55    4 80,000.00
      3 Bob    25    2 70,000.00
      4 Jane   25    2 50,000.00
      5 Alex   25    3 50,000.00
    5 person records

    >>> print db(summarize('person', ['age']))
    age n
    --- -
    *   5
    25  4
    55  1

    >>> print db(summarize('person', ['age','kids']))
    age kids n
    --- ---- -
    *   *    5
    *   1    1
    *   2    2
    *   3    1
    *   4    1
    25  *    4
    55  *    1
    25  1    1
    25  2    2
    25  3    1
    55  4    1

    >>> print db(summarize('person', ['age','kids'], ['salary']))
    age kids n salary
    --- ---- - ----------
    *   *    5 290,000.00
    *   1    1  40,000.00
    *   2    2 120,000.00
    *   3    1  50,000.00
    *   4    1  80,000.00
    25  *    4 210,000.00
    55  *    1  80,000.00
    25  1    1  40,000.00
    25  2    2 120,000.00
    25  3    1  50,000.00
    55  4    1  80,000.00

    >>> people.zap()
    >>> print people
    Empty list
    """
    # pylint: disable=invalid-name
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

    metrics = metrics or []

    statement_tpl = 'select {dims}, {calcs} from {table} group by {cols}'
    d = [i.split()[:1][0] for i in dimensions]
    c = [i.split()[-1:][0] for i in dimensions]
    n = len(dimensions)
    lst = []

    for s in list(itertools.product([0, 1], repeat=n)):
        dims = ', '.join(
            [s[i] and d[i] + ' '+ c[i] or '"*" ' + c[i]
             for i, _ in enumerate(s)]
        )
        calcs = ', '.join(
            ['count(*) n'] + ['sum({}) {}'.format(m, m)
                              for m in metrics]
        )
        cols = ', '.join([str(n+1) for n, _ in enumerate(c)])
        lst.append(statement_tpl.format(**locals()))

    return '\nunion '.join(lst)

def sql_apply(table, dimensions, metrics, fns=None, where='where 1=1'):
    """Return a sql command (mysql)

    apply the function(s) for the given metrics for each sub-group (group by
    dimensions)

    aggregate the metrics for the given table by the dimensions filtered if
    necessary (where)

    >>> sql_apply('test.q1', ['date'], ['count_n']) == (
    ...     'select date, sum(count_n) as '
    ...     'count_n from test.q1 where 1=1 '
    ...     'group by 1;'
    ... )
    True

    >>> sql_apply(
    ...     'test.q1',
    ...     ['date', 'location', 'age_group'],
    ...     ['total_age','avg_age','total_score', 'avg_score'],
    ...     fns=['sum','avg']
    ... ) == (
    ...     'select date, location, age_group, sum(total_age) as total_age, '
    ...     'avg(avg_age) as avg_age, sum(total_score) as total_score, '
    ...     'avg(avg_score) as avg_score from test.q1 '
    ...     'where 1=1 group by 1,2,3;'
    ... )
    True
    """
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

    fns = fns or ['sum']

    if not hasattr(fns, '__iter__'):
        fns = [fns]
    fns = fns * int(ceil(len(metrics)+1/len(fns)))
    cmd = 'select {dims}, {calcs} from {table} {where} group by {cols};'
    dims = ', '.join(dimensions)
    calcs = ', '.join(
        ['{fn}({metric}) as {metric}'.format(fn=fn, metric=m)
         for m, fn in zip(metrics, fns)]
    )
    #cols = ','.join(map(str, range(1, len(dimensions)+1)))
    cols = ','.join(str(i+1) for i in range(len(dimensions)))
    return cmd.format(**locals())
