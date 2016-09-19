# -*- coding: utf-8 -*-

"""
    zoom.jsonz

    JSON with extra converters
"""

import json
import datetime
from decimal import Decimal
from datetime import datetime, date


def loads(text):
    """load JSON from a string

    Provides support for extra types such as decimal, date and datetime.

    >>> loads('{"amount": {"__type__": "decimal", "value": "10.1"}}')
    {u'amount': Decimal('10.1')}

    >>> loads(
    ...     '{"timestamp": {"__type__": "datetime", '
    ...     '"value": "2015-01-01T10:40:10"}}'
    ... )
    {u'timestamp': datetime.datetime(2015, 1, 1, 10, 40, 10)}

    >>> loads(
    ...     '{"timestamp": {"__type__": "datetime", '
    ...     '"value": "2015-01-01T10:40:10.2342"}}'
    ... )
    {u'timestamp': datetime.datetime(2015, 1, 1, 10, 40, 10, 234200)}
    """

    def dhandler(obj):
        """handles extra converters"""
        # pylint: disable=invalid-name
        if '__type__' in obj:
            t = obj['__type__']
            if t == 'datetime':
                try:
                    return datetime.strptime(obj['value'],
                                             '%Y-%m-%dT%H:%M:%S.%f')
                except ValueError:
                    return datetime.strptime(obj['value'],
                                             '%Y-%m-%dT%H:%M:%S')
            elif t == 'date':
                return datetime.strptime(obj['value'], '%Y-%m-%d').date()
            elif t == 'decimal':
                return Decimal(str(obj['value']))
        return obj

    return json.loads(text, object_hook=dhandler)


def dumps(data, *a, **k):
    """Convert to json with support for date and decimal types

    >>> dumps('test')
    '"test"'

    >>> loads(dumps('test'))
    u'test'

    >>> loads(dumps(date(2015,1,1)))
    datetime.date(2015, 1, 1)

    >>> loads(dumps(datetime(2015, 1, 1, 10, 40, 10)))
    datetime.datetime(2015, 1, 1, 10, 40, 10)

    >>> loads(dumps(Decimal('20.40')))
    Decimal('20.40')
    """

    def handler(obj):
        """handles extra converters"""
        if isinstance(obj, datetime):
            return dict(__type__='datetime', value=obj.isoformat())
        elif isinstance(obj, date):
            return dict(__type__='date', value=obj.isoformat())
        elif isinstance(obj, Decimal):
            return dict(__type__='decimal', value=str(obj))
        else:
            msg = 'Object of type %s with value %s is not JSON serializable.'
            raise TypeError(msg % (type(obj), repr(obj)))

    return json.dumps(data, default=handler, *a, **k)
