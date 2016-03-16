"""
    Test the storage module
    
    Copyright (c) 2005-2012 Dynamic Solutions Inc. (support@dynamic-solutions.com)
    
    This file is part of DataZoomer.

    NOTE: the storage.py module is deprecated.  Use store.py instead.
"""

import zoom.storage
from zoom.storage import *
import unittest

# connect to test database
import MySQLdb
from zoom.database import Database
dbhost  = 'database'
dbname  = 'test'
dbuser  = 'testuser'
dbpass  = 'password'


class MyModel(Model):
    first_name = ''
    age = 0
    last_name  = ''
    active = False
    #_db = db

    def valid(self):
        return len(self.FIRST_NAME)>1


class TestModelPerformance(unittest.TestCase):
    def stest_put_performance(self):
        num_puts = 100
        time_allowed = 6
        import time, random
        start = time.time()
        for i in range(num_puts):
            o = MyModel(FIRST_NAME='Joe%s'%i,LAST_NAME='Smith%s'%i,age=random.randint(0,50))
            o.put()
        assert time.time()-start<time_allowed,'%d puts exceeded %.2fs (%.2fs)' % (num_puts,time_allowed,time.time()-start)

    def stest_get_performance(self):
        num_gets = 5000
        time_allowed = 2
        import time, random
        start = time.time()
        for i in range(num_gets):
            r = MyModel().get(100)
        assert time.time()-start<time_allowed,'%d gets exceeded %.2fs (%.2fs)' % (num_gets,time_allowed,time.time()-start)

    def stest_all_performance(self):
        iterations = 5000
        time_allowed = 2
        import time, random
        start = time.time()
        for i in range(iterations):
            r = MyModel().all()
        assert time.time()-start<time_allowed,'%d operations exceeded %.2fs (%.2fs)' % (iterations,time_allowed,time.time()-start)


class TestModel(unittest.TestCase):

    def setUp(self):
        db = Database(MySQLdb.Connect,host=dbhost,user=dbuser,passwd=dbpass,db=dbname)
        zoom.storage.db = db
        MyModel._db = db
        db.autocommit(1)
        delete_storage()
        create_storage()

    def tearDown(self):
        zoom.storage.db.close()

    def test_init(self):
        assert MyModel()

    def test_create(self):
        o = MyModel(FIRST_NAME='Herb',LAST_NAME='Smith')
        self.assertEqual(o.FIRST_NAME,'Herb')
        o.put()
        o.FIRST_NAME = 'HERB'
        assert o.put()
        o = MyModel()
        o.FIRST_NAME = 'JOE'
        o.LAST_NAME  = 'SMITH'
        assert o.put()

    def test_put(self):
        o = MyModel()
        o.FIRST_NAME = 'HERB'
        assert o.put()
        o = MyModel()
        o.FIRST_NAME = 'JOE'
        o.LAST_NAME  = 'SMITH'
        assert o.put()

    def test_get(self):
        o = MyModel()
        MyModel.get(5)

    def test_get_missing(self):
        self.assertEqual(None,MyModel().get(100000))

    def test_get_multiple(self):
        o = MyModel()
        o.FIRST_NAME = 'Herb'
        o.AGE = 50
        rec_one = o.put()
        assert rec_one
        o = MyModel()
        o.FIRST_NAME = 'JOE'
        o.LAST_NAME  = 'SMITH'
        o.AGE = 30
        assert o.put()
        o = MyModel()
        o.FIRST_NAME = 'SARAH'
        o.AGE = 41
        rec_three = o.put()
        assert rec_three
        o = MyModel()
        o.FIRST_NAME = 'WENDEL'
        o.LAST_NAME  = 'SMITH'
        o.AGE = 40
        assert o.put()
        result = MyModel.get([rec_one,rec_three])
        self.assertEqual(result[0].FIRST_NAME,'Herb')
        self.assertEqual(result[0].AGE,50)
        self.assertEqual(result[1].AGE,41)

    def test_get_all(self):
        o = MyModel()
        o.FIRST_NAME = 'HERB'
        assert o.put()
        o = MyModel()
        o.FIRST_NAME = 'JOE'
        o.LAST_NAME  = 'SMITH'
        assert o.put()
        o = MyModel()
        o.FIRST_NAME = 'SARAH'
        assert o.put()
        o = MyModel()
        o.FIRST_NAME = 'WENDEL'
        o.LAST_NAME  = 'SMITH'
        assert o.put()
        MyModel.all()

    def test_put_new_then_get(self):
        o = MyModel()
        o.FIRST_NAME = 'Herb'
        new_id = o.put()
        assert new_id
        self.assertEqual(o.FIRST_NAME,'Herb')
        del o
        r = MyModel().get(new_id)
        self.assertEqual(r.FIRST_NAME,'Herb')

    def test_dont_put_invalid_object(self):
        o = MyModel()
        o.LAST_NAME = 'Herb'
        assert not o.put()

    def test_kind(self):
        o = MyModel()
        self.assertEqual(o.kind(),'my_model')

    def test_find(self):
        MyModel(FIRST_NAME='Herb',REGION='A',AGE=15).put()
        MyModel(FIRST_NAME='Joe',REGION='A',AGE=10).put()
        MyModel(FIRST_NAME='James',REGION='A',AGE=20).put()
        MyModel(FIRST_NAME='Shirley',REGION='A',AGE=10).put()
        MyModel(FIRST_NAME='Shea',REGION='B',AGE=10).put()
        
        self.assertEqual(MyModel.find(FIRST_NAME='HERB')[0].FIRST_NAME,'Herb')
        result = MyModel.find(FIRST_NAME='Joe')
        self.assertEqual(result[0].FIRST_NAME,'Joe')
        self.assertEqual(MyModel.find(FIRST_NAME='SAM'),[])

        self.assertEqual(len(MyModel.find(REGION='A',AGE=10)),2)
        self.assertEqual(len(MyModel.find(REGION='A')),4)
        self.assertEqual(len(MyModel.find(AGE=10)),3)

        self.assertEqual(len(MyModel.find(FIRST_NAME=['Herb','Joe'])),2)

    def test_attributes(self):
        MyModel(FIRST_NAME='Joe',LAST_NAME='Smith',AGE=21).put()
        attributes = MyModel().attributes()
        assert 'first_name' in attributes
        assert 'last_name' in attributes
        assert 'age' in attributes
        assert len(attributes)==3

    def test_float(self):
        class TheModel(Model): pass
        import time
        TheModel(FIRST_NAME='Joe',LAST_NAME='Smith',EXPIRY=time.time()+10*60).put()
        attributes = TheModel().attributes()
        assert 'first_name' in attributes
        assert 'last_name' in attributes
        assert 'expiry' in attributes
        assert len(attributes)==3

    def test_instance(self):
        class TestCustomer(Model): pass
        class TestInvoice(Model): pass
        customer = TestCustomer(name='Joe Smith',credit_limit=100)
        assert customer
        customer_id = customer.put()
        assert customer_id
        invoice = TestInvoice(customer=customer,amount=25,items='here are the items')
        self.assertRaises(TypeException,invoice.put)
        invoice = TestInvoice(customer=customer_id,amount=25,items='here are the items')
        invoice_id = invoice.put()
        assert invoice_id
        invoice = TestInvoice.get(invoice_id)
        self.assertEqual(invoice.items,'here are the items')
        self.assertEqual(invoice.amount,25)
        customer = TestCustomer.get(invoice.customer)
        assert customer
        self.assertEqual(customer.name,'Joe Smith')


    def test_with_methods(self):
        class TheModel(Model): 
            def mymethod(self):
                return self.last_name.upper() + ',' + self.first_name.upper()
        import time
        TheModel(FIRST_NAME='Joe',LAST_NAME='Smith',EXPIRY=time.time()+10*60).put()
        attributes = TheModel().attributes()
        assert 'first_name' in attributes
        assert 'last_name' in attributes
        assert 'expiry' in attributes
        assert len(attributes)==3

    def test_zap_and_len(self):
        MyModel.zap()
        self.assertEqual(MyModel.len(),0)
        rec = MyModel()
        rec.FIRST_NAME = 'Fred'
        rec.put()
        self.assertEqual(MyModel.len(),1)
        MyModel.zap()
        self.assertEqual(MyModel.len(),0)

    def test_exists(self):
        MyModel.zap()
        self.assertEqual(MyModel.len(),0)
        rec = MyModel()
        rec.FIRST_NAME = 'Fred'
        new_id = rec.put()
        self.assertEqual(MyModel.exists(new_id),True)
        self.assertEqual(MyModel.len(),1)
        MyModel.zap()
        self.assertEqual(MyModel.len(),0)
        self.assertEqual(MyModel.exists(new_id),False)

    def test_update(self):
        MyModel.zap()
        rec = MyModel()
        rec.FIRST_NAME = 'Fred'
        rec.put()
        rec.FIRST_NAME = 'Herb'
        id = rec.put()
        self.assertEqual(MyModel.len(),1)
        o = MyModel.get(id)
        self.assertEqual(MyModel.get(id).FIRST_NAME,'Herb')

        rec.update(FIRST_NAME='Joey')
        rec.put()

    def test_sort(self):
        MyModel.zap()
        MyModel(FIRST_NAME='Joe',LAST_NAME='Smith',AGE=20).put()
        MyModel(FIRST_NAME='Adam',LAST_NAME='Jones',AGE=40).put()
        t = MyModel.all()
        t.sort(key=lambda obj: obj.FIRST_NAME)
        self.assertEqual(t[0].FIRST_NAME,'Adam')
        t.sort(key=lambda obj: obj.AGE)
        self.assertEqual(t[0].FIRST_NAME,'Joe')

    def test_case_agnostic(self):
        MyModel.zap()
        new_id = MyModel(FIRST_NAME='Joe',LAST_NAME='Smith').put()

        m = MyModel.get(new_id)
        self.assertEqual(hasattr(m,'first_name'),True)
        self.assertEqual(hasattr(m,'FIRST_NAME'),True)

        MyModel.zap()
        new_id = MyModel(FIRST_NAME='Joe',last_name='Smith').put()
        m = MyModel.get(new_id)
        self.assertEqual(hasattr(m,'last_name'),True)
        self.assertEqual(hasattr(m,'LAST_NAME'),True)

        m.update(Last_Name='Smithers',age=20)
        another_new_id = m.put()

        n = MyModel.get(another_new_id)
        assert hasattr(n,'last_name')
        self.assertEqual(n.last_name,'Smithers')

    def test_none(self):
        MyModel.zap()
        new_id = MyModel(FIRST_NAME='Joe',LAST_NAME='Smith',STATUS=None).put()

        m = MyModel.get(new_id)
        self.assertEqual(hasattr(m,'first_name'),True)
        assert hasattr(m,'first_name')
        assert m.first_name == 'Joe'
        assert m.status == None

    def test_bool(self):
        MyModel.zap()
        new_id = MyModel(FIRST_NAME='Joe',LAST_NAME='Smith',active=False).put()

        m = MyModel.get(new_id)
        self.assertEqual(hasattr(m,'first_name'),True)
        assert hasattr(m,'first_name')
        assert m.first_name == 'Joe'
        assert m.active == False

        m.active = True
        m.put()

        m2 = MyModel.get(new_id)
        assert m2.active == True

        m2.active = False
        m2.put()

        m3 = MyModel.get(new_id)
        assert m3.active == False


