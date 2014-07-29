"""
    expression generators

    experimental!
"""

class SearchTerm(object):
    def __init__(self, value):
        self.value = value
    #def __repr__(self):
        #return '%s%s' % (self.operator, repr(self.value))
    #def __repr__(self):
        #return '%s%s' % (self.operator, repr(self.value))
    def visit(self, visitor, *a, **k):
        return visitor(self, *a, **k)
class LessThan(SearchTerm): operator = '<'
class LessThanOrEqualTo(SearchTerm): operator = '<='
class GreaterThan(SearchTerm): operator = '>'
class GreaterThanOrEqualTo(SearchTerm): operator = '>='
class Equal(SearchTerm): operator = '=='
class NotEqual(SearchTerm): operator = '<>'
lt = LessThan
lte = LessThanOrEqualTo
gt = GreaterThan
gte = GreaterThanOrEqualTo
eq = Equal
ne = NotEqual

def sql_where(*a,**k):
    def visitor(term):
        return term.operator + repr(term.value)
    return ' and '.join('%s%s' % (k,v.visit(visitor)) for k,v in k.items())

def store_find(kind, *a,**k):
    def visitor(term, name):
        p = '(select row_id from entities where kind=%s and entity=%s and value%s%s)' 
        return p % (repr(kind), repr(name), term.operator, repr(term.value))
    return 'select * from entites where\n' + ' and\n'.join('  row_id in %s' % v.visit(visitor, k) for k,v in k.items())

class TestExpressions:
    """
    tests expressions

        >>> expr1 = dict(name=NotEqual('Joe'), age=NotEqual(3))
        >>> expr2 = dict(name=ne('Joe'), age=LessThan(3)) 

        >>> sql_where(**expr1)
        "age<>3 and name<>'Joe'"
        >>> sql_where(**expr2)
        "age<3 and name<>'Joe'"

        >>> print store_find('person', **expr1)
        select * from entites where
          row_id in (select row_id from entities where kind='person' and entity='age' and value<>3) and
          row_id in (select row_id from entities where kind='person' and entity='name' and value<>'Joe')

    """
    pass

