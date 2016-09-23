"""
    Test the collect module
    
    Copyright (c) 2005-2012 Dynamic Solutions Inc. (support@dynamic-solutions.com)
    
    This file is part of DataZoomer.
"""

import os
import sys
import unittest
import difflib
import MySQLdb
from decimal import Decimal
from datetime import date, time, datetime

from zoom import (Entity, Fields, TextField, required,
                  DecimalField, url_for_page)
from zoom.browse import browse
from zoom.page import page
from zoom.system import system
from zoom.user import user
from zoom.db import Database
from zoom.collect import Collection, CollectionRecord
from zoom.exceptions import UnauthorizedException

VIEW_EMPTY_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
</tbody>
<tr><td colspan=3>None</td></tr>
</table>
<div class="footer">0 peoples</div>
</div>"""

VIEW_SINGLE_RECORD_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/joe">Joe</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
</tbody>
</table>
<div class="footer">1 people</div>
</div>"""

VIEW_TWO_RECORD_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/joe">Joe</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-2" class="dark">
<td nowrap><a href="/noapp//myapp/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">2 peoples</div>
</div>"""

VIEW_ALL_RECORDS_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/jim">Jim</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-2" class="dark">
<td nowrap><a href="/noapp//myapp/joe">Joe</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-3" class="light">
<td nowrap><a href="/noapp//myapp/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">3 peoples</div>
</div>"""

VIEW_NO_JOE_LIST = u"""<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">1 people</div>
</div>"""

VIEW_UPDATED_JOE_LIST = """<div class="baselist">

<table>
<thead><tr>
<th>Name</th>
<th>Address</th>
<th>Salary</th>
</tr></thead>
<tbody>
<tr id="row-1" class="light">
<td nowrap><a href="/noapp//myapp/jim">Jim</a></td>
<td nowrap>123 Somewhere St</td>
<td nowrap>40,000</td>
</tr>
<tr id="row-2" class="dark">
<td nowrap><a href="/noapp//myapp/sally">Sally</a></td>
<td nowrap>123 Special St</td>
<td nowrap>45,000</td>
</tr>
</tbody>
</table>
<div class="footer">2 peoples</div>
</div>"""

def assert_same(t1, t2):
    try:
        assert t1 == t2
    except:
        s1 = t1.splitlines()
        s2 = t2.splitlines()
        print('\n'.join(difflib.context_diff(s1, s2)))
        raise

class Person(CollectionRecord):
    url = property(lambda self: url_for_page('/myapp', self.key))
#class TestPerson(CollectionRecord): pass

# define the fields for the collection
person_fields = Fields(
    TextField('Name', required),
    TextField('Address'),
    DecimalField('Salary'),
)

class TestCollect(unittest.TestCase):

    def setUp(self):
        # setup the system and install our own test database
        system.setup(os.path.expanduser('~'))

        user.initialize('guest')
        user.groups = ['managers']
        params = dict(
            host='database',
            user='testuser',
            passwd='password',
            db='test',
        )
        self.db = Database(MySQLdb.Connect, **params)
        self.db.autocommit(1)
        system.db = self.db

        # create the test collection
        self.collection = Collection('People', person_fields, Person, url='/myapp')

        # so we can see our print statements
        self.save_stdout = sys.stdout
        sys.stdout = sys.stderr

    def tearDown(self):
        # remove our test data
        self.collection.store.zap()
        self.db.close()
        sys.stdout = self.save_stdout

    def test_insert(self):
        self.collection.store.zap()
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

        insert_record_input = dict(
            CREATE_BUTTON='y',
            NAME='Joe',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        )
        t = self.collection('new', **insert_record_input)
        t = self.collection()
        assert_same(VIEW_SINGLE_RECORD_LIST, t.content)

    def test_delete(self):
        self.collection.store.zap()
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

        joe_input = dict(
            CREATE_BUTTON='y',
            NAME='Joe',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        )
        t = self.collection('new', **joe_input)

        sally_input = dict(
            CREATE_BUTTON='y',
            NAME='Sally',
            ADDRESS='123 Special St',
            SALARY=Decimal('45000'),
        )
        t = self.collection('new', **sally_input)

        t = self.collection()
        assert_same(VIEW_TWO_RECORD_LIST, t.content)

        self.collection('delete', 'joe', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_NO_JOE_LIST, t.content)

        self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

    def test_update(self):
        self.collection.store.zap()
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

        joe_input = dict(
            CREATE_BUTTON='y',
            NAME='Joe',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        )
        t = self.collection('new', **joe_input)

        sally_input = dict(
            CREATE_BUTTON='y',
            NAME='Sally',
            ADDRESS='123 Special St',
            SALARY=Decimal('45000'),
        )
        t = self.collection('new', **sally_input)

        self.collection('joe', 'edit', **dict(
            SAVE_BUTTON='y',
            NAME='Jim',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        ))
        t = self.collection()
        assert_same(VIEW_UPDATED_JOE_LIST, t.content)

        self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_NO_JOE_LIST, t.content)

        self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

    def test_authorized_editors(self):
        self.collection.store.zap()
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

        joe_input = dict(
            CREATE_BUTTON='y',
            NAME='Joe',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        )
        t = self.collection('new', **joe_input)

        sally_input = dict(
            CREATE_BUTTON='y',
            NAME='Sally',
            ADDRESS='123 Special St',
            SALARY=Decimal('45000'),
        )
        t = self.collection('new', **sally_input)
        t = self.collection()
        assert_same(VIEW_TWO_RECORD_LIST, t.content)

        # only authorized users can edit collections
        user.groups = []
        with self.assertRaises(UnauthorizedException):
            self.collection('joe', 'edit', **dict(
                SAVE_BUTTON='y',
                NAME='Jim',
                ADDRESS='123 Somewhere St',
                SALARY=Decimal('40000'),
            ))
        t = self.collection()
        assert_same(VIEW_TWO_RECORD_LIST, t.content)

        user.groups = ['managers']
        self.collection('joe', 'edit', **dict(
            SAVE_BUTTON='y',
            NAME='Jim',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        ))
        t = self.collection()
        assert_same(VIEW_UPDATED_JOE_LIST, t.content)

        user.groups = []
        with self.assertRaises(UnauthorizedException):
            self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_UPDATED_JOE_LIST, t.content)

        user.groups = ['managers']
        self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_NO_JOE_LIST, t.content)

        self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)


    def test_private(self):

        class PrivatePerson(Person):
            def allows(self, user, action=None):

                def is_owner(user):
                    return user.user_id == self.owner_id

                def is_user(user):
                    return user.is_authenticated

                actions = {
                    'create': is_user,
                    'read': is_owner,
                    'update': is_owner,
                    'delete': is_owner,
                }

                return actions.get(action)(user)

        #def private(rec, user, action=None):
            #return rec.owner == user.user_id

        self.collection = Collection('People', person_fields, PrivatePerson, url='/myapp')
        self.collection.can_edit = lambda: True
        #self.collection.authorization = private

        self.collection.store.zap()
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

        # user one inserts two records
        joe_input = dict(
            CREATE_BUTTON='y',
            NAME='Jim',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        )
        t = self.collection('new', **joe_input)

        sally_input = dict(
            CREATE_BUTTON='y',
            NAME='Sally',
            ADDRESS='123 Special St',
            SALARY=Decimal('45000'),
        )
        t = self.collection('new', **sally_input)
        t = self.collection()
        assert_same(VIEW_UPDATED_JOE_LIST, t.content)

        # user two inserts one record
        user.initialize('admin')
        self.collection('new', **dict(
            CREATE_BUTTON='y',
            NAME='Joe',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        ))
        t = self.collection()
        assert_same(VIEW_SINGLE_RECORD_LIST, t.content)

        # user one can still only see theirs
        user.initialize('guest')
        t = self.collection()
        assert_same(VIEW_UPDATED_JOE_LIST, t.content)

        # user can't read records that belong to others
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe')

        # user can't edit records that belong to others
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'edit')

        # user can't do delete confirmation for records that belong to others
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'delete')

        # user can't update records that belong to others
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'edit', **dict(
                SAVE_BUTTON='y',
                NAME='Andy',
                ADDRESS='123 Somewhere St',
                SALARY=Decimal('40000'),
            ))

        # user can't delete records that belong to others
        with self.assertRaises(UnauthorizedException):
            self.collection('joe', 'delete', **{'CONFIRM': 'NO'})

        # switch back to owner and do the same operations
        user.initialize('admin')
        self.collection('joe')
        self.collection('joe', 'edit')
        self.collection('joe', 'delete')
        self.collection('joe', 'edit', **dict(
            SAVE_BUTTON='y',
            NAME='Andy',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        ))
        self.collection('andy', 'delete', **{'CONFIRM': 'NO'})


        user.initialize('guest')
        user.groups = ['managers']
        self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_NO_JOE_LIST, t.content)

        self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)


    def test_published(self):

        class PrivatePerson(Person):
            def allows(self, user, action=None):

                def is_owner(user):
                    return user.user_id == self.owner_id

                def is_user(user):
                    return user.is_authenticated

                actions = {
                    'create': is_user,
                    'read': is_user,
                    'update': is_owner,
                    'delete': is_owner,
                }

                return actions.get(action)(user)

        self.collection = Collection('People', person_fields, PrivatePerson, url='/myapp')
        self.collection.can_edit = lambda: True

        self.collection.store.zap()
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

        # user one inserts two records
        user.initialize('user')
        assert user.is_authenticated
        user.groups = ['managers']

        joe_input = dict(
            CREATE_BUTTON='y',
            NAME='Jim',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        )
        t = self.collection('new', **joe_input)

        sally_input = dict(
            CREATE_BUTTON='y',
            NAME='Sally',
            ADDRESS='123 Special St',
            SALARY=Decimal('45000'),
        )
        t = self.collection('new', **sally_input)
        t = self.collection()
        assert_same(VIEW_UPDATED_JOE_LIST, t.content)

        # user two inserts one record
        user.initialize('admin')
        self.collection('new', **dict(
            CREATE_BUTTON='y',
            NAME='Joe',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        ))
        t = self.collection()
        assert_same(VIEW_ALL_RECORDS_LIST, t.content)

        # user one can also see all
        user.initialize('user')
        t = self.collection()
        assert_same(VIEW_ALL_RECORDS_LIST, t.content)

        # guest can't read records
        user.initialize('guest')
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe')

        # authenticated user can read records that belong to others
        user.initialize('user')
        t = self.collection('joe')

        # user can't edit records that belong to others
        user.initialize('guest')
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'edit')

        # user can't edit records that belong to others
        user.initialize('user')
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'edit')

        # guest can't do delete confirmation for records that belong to others
        user.initialize('guest')
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'delete')

        # user can't do delete confirmation for records that belong to others
        user.initialize('user')
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'delete')

        # user can't update records that belong to others
        with self.assertRaises(UnauthorizedException):
            t = self.collection('joe', 'edit', **dict(
                SAVE_BUTTON='y',
                NAME='Andy',
                ADDRESS='123 Somewhere St',
                SALARY=Decimal('40000'),
            ))

        # user can't delete records that belong to others
        with self.assertRaises(UnauthorizedException):
            self.collection('joe', 'delete', **{'CONFIRM': 'NO'})

        # switch back to owner and do the same operations
        user.initialize('admin')
        self.collection('joe')
        self.collection('joe', 'edit')
        self.collection('joe', 'delete')
        self.collection('joe', 'edit', **dict(
            SAVE_BUTTON='y',
            NAME='Andy',
            ADDRESS='123 Somewhere St',
            SALARY=Decimal('40000'),
        ))
        self.collection('andy', 'delete', **{'CONFIRM': 'NO'})

        # guest can't delete
        user.initialize('guest')
        user.groups = ['managers']
        with self.assertRaises(UnauthorizedException):
            self.collection('delete', 'jim', **{'CONFIRM': 'NO'})

        # guest can't delete
        with self.assertRaises(UnauthorizedException):
            self.collection('delete', 'sally', **{'CONFIRM': 'NO'})

        # non-owner can't delete
        user.initialize('admin')
        user.groups = ['managers']
        with self.assertRaises(UnauthorizedException):
            self.collection('delete', 'jim', **{'CONFIRM': 'NO'})

        # non-owner can't delete
        with self.assertRaises(UnauthorizedException):
            self.collection('delete', 'sally', **{'CONFIRM': 'NO'})

        # owner can delete
        user.initialize('user')
        user.groups = ['managers']
        self.collection('delete', 'jim', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_NO_JOE_LIST, t.content)

        self.collection('delete', 'sally', **{'CONFIRM': 'NO'})
        t = self.collection()
        assert_same(VIEW_EMPTY_LIST, t.content)

