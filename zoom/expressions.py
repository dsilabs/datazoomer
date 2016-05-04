"""
    expression generators

    experimental and changing!
    do not use this for anything you care about!

    TODO: add aggregation classes (Min, Max, Count)

"""

class SearchTerm(object):

    def __init__(self, value):
        self.value = value

    def visit(self, visitor, *a, **k):
        return visitor(self, *a, **k)

class LessThan(SearchTerm): operator = '<'
class LessThanOrEqualTo(SearchTerm): operator = '<='
class GreaterThan(SearchTerm): operator = '>'
class GreaterThanOrEqualTo(SearchTerm): operator = '>='
class Equal(SearchTerm): operator = '=='
class NotEqual(SearchTerm): operator = '<>'
class Occurs(SearchTerm): operator = ' in '
lt = LessThan
lte = LessThanOrEqualTo
gt = GreaterThan
gte = GreaterThanOrEqualTo
eq = Equal
ne = NotEqual
occurs = Occurs


def sql_query(table, *a, **k):
    """
    generate a generic sql select statement

        >>> expr1 = dict(name=NotEqual('Joe'), age=NotEqual(3))
        >>> expr2 = dict(name=ne('Joe'), age=LessThan(3)) 

        >>> sql_query('people', **expr1)
        "select * from people where age<>3 and name<>'Joe'"
        >>> sql_query('people', **expr2)
        "select * from people where age<3 and name<>'Joe'"

        >>> where = sql_query

        >>> where('people', name=eq('Joe'), age=lt(3))
        "select * from people where age<3 and name=='Joe'"

        >>> where('people', 'id', name='Joe', age=lt(3))
        "select id from people where age<3 and name=='Joe'"

    """
    def visitor(term):
        return term.operator + repr(term.value)

    def express(k, v):
        if isinstance(v, SearchTerm):
            return '%s%s' % (k, v.visit(visitor)) 
        else:
            return '%s==%r' % (k, v)
    ec = a and ', '.join(a) or '*'
    wc = ' and '.join(express(k, v) for k,v in k.items())
    cmd = 'select %s from %s where %s' % (ec, table, wc)
    return cmd


def mysql_query(table, *a, **k):
    """
    generate a mysql query with a corresponding parameters list

        >>> mysql_query('people', name='Joe', age=lt(3))
        ('select * from people where age<%s and name==%s', [3, 'Joe'])

    """
    def visitor(term):
        return term.operator, term.value
    def express(k, v):
        if isinstance(v, SearchTerm):
            return (k, v.visit(visitor)) 
        else:
            return (k, ('==', v))
    pairs = list(express(k, v) for k,v in k.items())
    expr, values = (
        ' and '.join('%s%s%s' % (v[0], v[1][0], '%s') for v in pairs),
        [v[1][1] for v in pairs],
    )
    cmd = 'select %s from %s where %s'
    return cmd % (a and ','.join(a) or '*', table, expr), values


def store_query(kind, *a,**k):
    """
    generate a query for an EntityStore

        >>> print store_query('person', name='Joe', age=gt(25))
        select row_id from entites where
          row_id in (select row_id from entities where kind='person' and entity='age' and value>25) and
          row_id in (select row_id from entities where kind='person' and entity='name' and value='Joe')

    """
    p = '(select row_id from entities where kind=%s and entity=%s and value%s%s)' 
    def visitor(term, name):
        return p % (repr(kind), repr(name), term.operator, repr(term.value))
    def express(k, v):
        if isinstance(v, SearchTerm):
            return v.visit(visitor, k)
        else:
            return p % (repr(kind), repr(k), '=', repr(v))
    return 'select row_id from entites where\n' + ' and\n'.join('  row_id in %s' % express(k, v) for k,v in k.items())

