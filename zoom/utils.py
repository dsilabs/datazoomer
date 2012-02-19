"""Utilities"""

import web

# Handy data structures
storage = web.storage
threadeddict = web.threadeddict

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

if __name__ == '__main__':
    import doctest
    doctest.testmod()


