"""
    Enhanced JSON converters

    Handle extra types.
"""

import json
import datetime

def loads(text):
    def dhandler(obj):
        if '__type__' in obj:
            t = obj['__type__']
            if t == 'datetime':
                return datetime.datetime.strptime(obj['value'], '%Y-%m-%dT%H:%M:%S.%f')
            elif t == 'date':
                return datetime.datetime.strptime(obj['value'], '%Y-%m-%d').date()
        return obj                
    return json.loads(text, object_hook=dhandler)
    

def dumps(data, *a, **k):
    """Convert to json with support for date types"""
    def handler(obj):
        if isinstance(obj, datetime.datetime):
            return dict(__type__='datetime',value=obj.isoformat())
        elif isinstance(obj, datetime.date):
            return dict(__type__='date',value=obj.isoformat())
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
            
    unittest.main()
    #d = datetime.date.today()
    #print d
    #print dumps(d), type(dumps(d))
    #print loads(dumps(d)),type(loads(dumps(d)))
                    
    #d = datetime.datetime.now()
    #print d
    #print dumps(d), type(dumps(d))
    #print loads(dumps(d)),type(loads(dumps(d)))
    
    
    
    
    
    
    
    
