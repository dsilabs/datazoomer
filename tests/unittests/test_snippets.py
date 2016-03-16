
import unittest
import MySQLdb
from zoom.system import system
from zoom.snippets import *
from zoom.database import Database

dbhost  = 'database'
dbname  = 'test'
dbuser  = 'testuser'
dbpass  = 'password'

class TestSnippets(unittest.TestCase):

    def setUp(self):
        system.database = Database(
            MySQLdb.Connect,
            host=dbhost,
            user=dbuser,
            passwd=dbpass,
            db=dbname)
        snippets.zap()

    def tearDown(self):
        system.database.close()

    def test_updates(self):

        snippets.put(Snippet(name='address', variant='', body='my addr'))
        snippets.put(Snippet(name='phone', variant='', body='my phone'))
        snippets.put(Snippet(name='twitter', variant='', body='my twitter'))
        snippets.put(Snippet(name='notice', variant='', body='my notice'))

        assert(len(snippets.all())==4)

        self.assertEqual(snippet('name'), '')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('address'), 'my addr')
        self.assertEqual(snippet('twitter'), 'my twitter')
        self.assertEqual(snippet('twitter'), 'my twitter')
        self.assertEqual(snippet('twitter'), 'my twitter')
        self.assertEqual(snippet('twitter'), 'my twitter')

        s = snippets.first(name='address')
        print s
        self.assertEqual(s.impressions, 5)

        s = snippets.first(name='twitter')
        print s
        self.assertEqual(s.impressions, 4)

        s = snippets.first(name='name')
        self.assertEqual(s, None)

    def test_many_updates(self):
        for name in ['one','two','three','four','five']:
            for variant in ['a','b','c','d','e','f','g']:
                snippets.put(Snippet(
                    name=name, 
                    variant=variant, 
                    body='my '+name))

        t = len(snippets.all())
        print snippets.all()

        c = 10
        for n in range(c):
            for name in sorted(['one','two','three','four'], reverse=True):
                for variant in ['a','b','c','d','e','f','g']:
                    self.assertEqual(snippet(name,variant),'my '+name)

        print snippets.all()

        s = snippets.first(name='three')
        self.assertEqual(s.impressions, c)

        self.assertEqual(t, len(snippets.all()))







