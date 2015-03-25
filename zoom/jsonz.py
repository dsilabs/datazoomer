"""
    Enhanced JSON converters

    Handle extra types.
"""

import json
import datetime
from decimal import Decimal

# simplejson (part of python 2.7+) supports Decimal as of v2.1
json_version = map(int,json.__version__.split('.')[:2])
json_support_decimal = json_version[0]>=2 and json_version[1]>=1

def loads(text):
    def dhandler(obj):
        if '__type__' in obj:
            t = obj['__type__']
            if t == 'datetime':
                return datetime.datetime.strptime(obj['value'], '%Y-%m-%dT%H:%M:%S.%f')
            elif t == 'date':
                return datetime.datetime.strptime(obj['value'], '%Y-%m-%d').date()
            elif t == 'decimal':
                return Decimal(str(obj['value']))
        return obj                
    return json.loads(text, object_hook=dhandler)
    

def dumps(data, *a, **k):
    """Convert to json with support for date types"""
    def handler(obj):
        if isinstance(obj, datetime.datetime):
            return dict(__type__='datetime',value=obj.isoformat())
        elif isinstance(obj, datetime.date):
            return dict(__type__='date',value=obj.isoformat())
        elif isinstance(obj, Decimal) and not json_support_decimal:
            return dict(__type__='decimal', value=float(str(obj)))
        else:
            raise TypeError, 'Object of type %s with value %s is not JSON serializable.' % (type(obj),repr(obj))
    return json.dumps(data, default=handler, *a, **k)


if __name__ == '__main__':
    import unittest
    
    class TestConvert(unittest.TestCase):
        
        def test_string(self):
            t = 'This is a test'
            tj = dumps(t)
            t2 = loads(tj)
            self.assertEqual(t,t2)
            
        def test_datetime(self):
            d = datetime.datetime.now()
            dj = dumps(d)
            d2 = loads(dj)
            self.assertEqual(d,d2)
            
        def test_date(self):
            d = datetime.date.today()
            dj = dumps(d)
            d2 = loads(dj)
            self.assertEqual(d,d2)

        def test_decimal(self):
            d = [22.32, u"22.32", Decimal('22.32'), Decimal(22.32)]
            exp = '[22.32, "22.32", {"__type__": "decimal", "value": 22.32}, {"__type__": "decimal", "value": 22.32}]'
            dj = dumps(d)
            d2 = loads(dj)
            if json_support_decimal:
                # otherwise ths will fail or can we determine what "type" the Decimal was constructed with?
                self.assertEqual(d,d2)
            if not json_support_decimal: self.assertEqual(dj, exp)
            
    unittest.main()

