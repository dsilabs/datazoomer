"""Test fill module"""

from zoom.fill import *

import unittest
import datetime

today = datetime.datetime.today()

def date():
    return today

def upper(text):
    return text.upper()

def concat(text1,text2):
    return text1 + text2

def link_to(label,url,*a,**k):
    args = ' '.join(['"%s"' % i for i in a])
    keywords = ' '.join(['%s="%s"' % (n,v) for n,v in k.iteritems()])
    return '<a href="%s" %s %s>%s</a>' % (url,args,keywords,label)

def test(*a,**k):
    return repr(a)+' '+repr(k)

helpers = locals()

def filler(text,*args,**keywords):
    """A filler that raises an exception on unknown tag"""
    return helpers[text](*args,**keywords)

def filler2(text,*args,**keywords):
    """A filler that returns None on unknown tag"""
    if text in helpers:
        return helpers[text](*args,**keywords)

class TestFill(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(fill('foo bar <Z:Date> end',filler),'foo bar %s end' % today)

    def test_basic_with_extra_spaces(self):
        self.assertEqual(fill('foo bar <Z:Date > end',filler),'foo bar %s end' % today)
        self.assertEqual(fill('foo bar <Z:Date   > end',filler),'foo bar %s end' % today)

    def test_one_param(self):
        self.assertEqual(fill('foo bar <z:upper "Test"> end',filler),'foo bar TEST end')

    def stest_complex(self):
        self.assertEqual(fill("""foo <z:link_to label="This is some text" url="www.test.com" action="dothis"> bar""",filler),\
            'foo %s bar' % link_to(label='This is some text',url="www.test.com",action='dothis'))
        self.assertEqual(fill('foo <z:link_to "This is some text" action="dothis"> bar',filler),\
            'foo %s bar' % link_to('This is some text',action='dothis'))
            
    def test_no_quotes(self):
        def callback(tag,*args,**keywords):
            return '%s %s %s' % (tag,args,keywords)
        self.assertEqual(fill("""foo <z:test name=joe> bar""",callback),"foo test () {u'name': u'joe'} bar")                

    def test_missing(self):
        self.assertRaises(Exception,filler,('foo <z:missing> bar',filler))
        
    def test_surrounded(self):
        self.assertEqual(viewfill('{{name}}',dict(name='Joe').get),'Joe')
        self.assertEqual(viewfill('<p>{{name}}</p>',dict(name='Joe').get),'<p>Joe</p>')
        self.assertEqual(viewfill('Test\n<p>{{name}}</p>\nother',dict(name='Joe').get),'Test\n<p>Joe</p>\nother')
        
    def test_single_line_only(self):
        self.assertEqual(viewfill('Test\n<p>{{name}}</p>\nother',dict(name='Joe').get),'Test\n<p>Joe</p>\nother')
        self.assertEqual(viewfill('Test\n<p>{{name}}</p>\n{{phone}}\nother',dict(name='Joe',phone='1234567').get),'Test\n<p>Joe</p>\n1234567\nother')
        self.assertEqual(viewfill('Test\n{{name}}<br>{{name}}\n',dict(name='Joe',phone='1234567').get),'Test\nJoe<br>Joe\n')
        self.assertEqual(viewfill('{{name}} > {{name}} > {{phone}}',dict(name='Joe',phone='1234567').get),'Joe > Joe > 1234567')
        self.assertEqual(viewfill('{{name}}</p><br>{{name}}\n{{phone}}',dict(name='Joe',phone='1234567').get),'Joe</p><br>Joe\n1234567')
        self.assertEqual(viewfill('Test\n<p>{{name}}</p><br>{{name}}\n{{phone}}\nother',dict(name='Joe',phone='1234567').get),'Test\n<p>Joe</p><br>Joe\n1234567\nother')
        
    def test_none(self):
        self.assertEqual(fill('foo <z:missing> bar',filler2),'foo None bar')
        
    def test_multiple(self):
        self.assertEqual(fill('foo <!-- comm --> bar <Z:Date> and <z:link_to Static1 "static.com" default="YourSite"> <!--c2--> end',filler),\
                'foo <!-- comm --> bar %s and %s <!--c2--> end' % (date(),link_to('Static1','static.com',default='YourSite')))
        
    def test_comments(self):
        self.assertEqual(fill('foo <!-- comm --> bar <Z:Date> end',filler),'foo <!-- comm --> bar %s end' % date())

    def test_nested_comments(self):            
        self.assertEqual(fill('foo <!-- comm <!-- test --> --> bar <Z:Date> comment',filler),\
                'foo <!-- comm <!-- test --> --> bar %s comment' % filler('date'))
        
    def test_multiple_comments(self):            
        self.assertEqual(fill('foo <!-- comm --> bar <Z:Date>  another <!-- test --> comment',filler),\
                'foo <!-- comm --> bar %s  another <!-- test --> comment' % filler('date'))
        
