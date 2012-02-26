"""Utilities"""

import web

# Handy data structures
from web.utils import storage, Storage, threadeddict, ThreadedDict

# Conversion functions
from web.net import htmlquote, htmlunquote, websafe

def unisafe(val):
    """
    Like web.websafe but without the HTML escaping
    """
    if val is None:
            return u''
    elif isinstance(val, str):
        val = val.decode('utf-8')
    elif not isinstance(val, unicode):
        val = unicode(val)
    return val

def kind(o):
    """
    returns a suitable table name for an object based on the object class
    """
    n = []
    for c in o.__class__.__name__:
        if c.isalpha() or c=='_':
            if c.isupper() and len(n):
                n.append('_')
            n.append(c.lower())
    return ''.join(n)

class Record(web.Storage):
    """
    A dict with attribute access to items, attributes and properties

        >>> class Foo(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> f = Foo(fname='Joe', lname='Smith')
        >>> f.full
        'Joe Smith'
        >>> f['full']
        'Joe Smith'
        >>> 'The name is %(full)s' % f
        'The name is Joe Smith'
        >>> print f
        <Foo {'lname': 'Smith', 'full': 'Joe Smith', 'fname': 'Joe'}>
        >>> f.attributes()
        ['lname', 'fname', 'full']

        >>> class FooBar(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> o = FooBar(a=2)
        >>> kind(o)
        'foo_bar'
        >>> o.a
        2
        >>> o['a']
        2
        >>> o.double = property(lambda o: 2*o.a)
        >>> o.double
        4
        >>> o['double']
        4
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

        >>> class Foo(Record):
        ...     full = property(lambda a: a.fname + ' ' + a.lname)
        ...
        >>> f = Foo(fname='Joe', lname='Smith')
        >>> f.full
        'Joe Smith'
        >>> f['full']
        'Joe Smith'
        >>> 'The name is %(full)s' % f
        'The name is Joe Smith'

        >>> o = Record(a=2)
        >>> o.a
        2
        >>> o['a']
        2
        >>> o.double = property(lambda o: 2*o.a)
        >>> o.double
        4
        >>> o['double']
        4
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """
    def __init__(self, **kv):
        for k in kv:
            setattr(self,k.lower(),kv[k])

    def attributes(self):
        return self.keys() + [k for k,v in self.__class__.__dict__.items() if hasattr(v,'__get__')]

    def valid(self):
        return 1

    def __getitem__(self, name):
        try:
            value = dict.__getitem__(self, name)
            if hasattr(value, '__get__'):
                return value.__get__(self)
            else:
                return value
        except KeyError, k:
            try:
                return self.__class__.__dict__[name].__get__(self)
            except KeyError, k:
                raise

    def __repr__(self):
        values = {}
        for k in self.attributes():
            if k not in values and not k.startswith('_'):
                values[k] = self[k]
        return '<%s %s>' % (self.__class__.__name__, dict.__repr__(values))


if __name__ == '__main__':
    import doctest
    doctest.testmod()


