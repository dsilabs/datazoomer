# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import datetime

from system import system
from auth import validate_password, hash_password

from .exceptions import UnauthorizedException

TWO_WEEKS = 14 * 24 * 60 * 60 # in seconds

def get_current_username():
    return \
        system.config.get('users','override','') or \
        system.session.login_id or \
        os.environ.get('REMOTE_USER',None) or \
        system.guest or \
        None

def authenticate(username, password):
    """ Authenticate the login """
    user = system.users.first(loginid=username, status='A')
    if user:
        match, phash = validate_password(password, user.password, user.dtadd)
        # phash is only set if the password validates and the stored hash is not in the preferred scheme
        #  phash will be the hash of the password in the preferred scheme (avoid the cost of hashing it again)
        if match and phash:
            # avoided RecordStore here as it only supports a key of "id"
            update_user(user.userid, PASSWORD=phash)
        return match

def deactivate_user(username):
    return system.database('update dz_users set status="I" where loginid=%s', username)

def activate_user(username):
    return system.database('update dz_users set status="A" where loginid=%s', username)

def user_exists(username):
    return system.database('select * from dz_users where loginid=%s', username)

def get_groupid(group_name):
    rec = system.database('select * from dz_groups where name=%s', group_name)
    if rec:
        return rec[0].groupid

def get_groupname(group_id):
    rec = system.database('select * from dz_groups where groupid=%s', group_id)
    if rec:
        return rec[0].name

def get_userid(username):
    rec = system.database('select * from dz_users where loginid=%s', username)
    if rec:
        return rec[0].userid

def get_username(userid):
    rec = system.database('select * from dz_users where userid=%s', userid)
    if rec:
        return rec[0].loginid

def add_user(username, group_name):
    userid = get_userid(username)
    groupid = get_groupid(group_name)
    if userid and groupid:
        system.database('insert into dz_members (userid, groupid) values (%s,%s)', userid, groupid)

def create_user(**values):
    """
    Create a new user and add her to the users group
    """
    now = datetime.datetime.now()

    # copy some field names to be compatible with legacy table structure
    values['FIRSTNAME'] = values['FIRST_NAME']
    values['LASTNAME'] = values['LAST_NAME']
    values['LOGINID'] = values['USERNAME'].lower()
    values['DTUPD'] = values['DTADD'] = now
    values['STATUS'] = 'A'
    users = system.database.table('dz_users','USERID')
    id = users.insert(values)
    system.database('delete from dz_members where userid=%s',id) # make sure new users have no memberships
    add_user(values['LOGINID'], 'users')
    return id

def update_user(user_id, **values):
    """
    Update a user
    """
    now = datetime.datetime.now()

    # copy some field names to be compatible with legacy table structure
    if 'FIRST_NAME' in values:
        values['FIRSTNAME'] = values['FIRST_NAME']
    if 'LAST_NAME' in values:
        values['LASTNAME'] = values['LAST_NAME']
    if 'USERNAME' in values:
        values['LOGINID'] = values['USERNAME'].lower()
    values['DTUPD'] = now
    values['USERID'] = user_id
    users = system.database.table('dz_users','USERID')
    id = users.update(values)
    return id

def delete_user(user_id):
    system.database('delete from dz_members where userid=%s', user_id)
    system.database('delete from dz_users where userid=%s', user_id)

def using_old_passwords():
    return system.database('describe dz_users password')[0].TYPE == 'char(16)'

def is_member(user, groups):
    """Determines if a user is a member of a set of groups

    >>> class User(object): pass
    >>> joe = User()
    >>> joe.groups = ['g1']
    >>> is_member(joe, ['g2','g3'])
    False
    >>> joe.groups.append('g2')
    >>> is_member(joe, ['g2','g3'])
    True
    >>> is_member(joe, 'g2,g3')
    True
    >>> is_member(joe, 'g1,g3')
    True
    >>> is_member(joe, 'g4,g3,g6')
    False

    """
    if isinstance(groups, str):
        items = groups.split(',')
    else:
        items = groups
    return bool(set(items).intersection(user.groups))

class User(object):
    link = property(lambda a: '<a href="/users/%s">%s</a>' % (a.username,a.username))

    def __init__(self, login_id=None):
        self.groups = []
        self.username = None
        self.is_developer = False
        self.is_administrator = False
        self.theme = None
        self.profile = False
        if login_id:
            self.initialize(login_id)

    def login(self, login_id, password, remember_me=False):
        if authenticate(login_id, password):
            system.session.login_id = login_id
            if remember_me:
                system.session.lifetime = TWO_WEEKS
            self.initialize(login_id)
            return True

    def logout(self):
        system.session.destroy_session()
        return self.initialize()

    def set_password(self, password):
        user = system.users.first(loginid=self.username, status='A')
        if user:
            phash = hash_password(password, user.dtadd)
            cmd = (
                'update dz_users '
                'set password=%s, dtupd=now() '
                'where loginid=%s'
            )
            system.db(cmd, phash, self.username)

    def is_member(self, groups):
        return is_member(self, groups)

    def setup(self):
        return self.initialize()

    @property
    def link(self):
        return '<a href="/{app}/{user.user_id}">{user.username}</a>'.format(
            app=system.app.name,
            user=user
        )

    @property
    def is_disabled(self):
        return bool(self.status == 'D')

    def initialize(self, login_id=None):

        if not login_id:
            login_id = get_current_username()

        select_user = "select * from dz_users where loginid=%s and status='A'"
        dataset = system.database(select_user, login_id)
        if not len(dataset):
            select_disabled_account = "SELECT * FROM dz_users WHERE loginid=%s and status<>'A'"
            dataset = system.database(select_disabled_account, login_id)
            if len(dataset) == 0:
                # this is a new authenticated user that has been authenticated
                # by the OS (Windows usually) so add to the guests group
                insert_user = "insert into dz_users (loginid,firstname,lastname,email,phone,status,dtupd,dtadd) values (%s,'','','','','A',%s,%s)"
                now = datetime.datetime.now()
                system.database(insert_user, login_id, now, now)
                dataset = system.database(select_user, login_id)
                add_user(login_id, 'guests')

        if len(dataset):
            self.login_id   = login_id
            self.username   = login_id
            rec = dataset[0]
            self.first_name = rec.firstname
            self.last_name  = rec.lastname
            self.phone      = rec.phone
            self.email      = rec.EMAIL
            self.status     = rec.STATUS
            self.user_id    = self.id = rec.USERID
        else:
            raise Exception('Unable to initialize user.')

        # determine membership in groups
        self.groups    = self.get_groups()
        self.apps      = [item[2:] for item in self.groups if item[:2]=='a_']
        self.roles     = [item for item in self.groups if item[:2]!='a_']
        self.is_admin  = self.is_administrator = \
                system.administrator_group in self.groups or \
                self.is_member(system.administrators)
        self.is_manager = \
                system.manager_group in self.groups or \
                self.is_member(system.managers)
        self.is_developer = \
                self.is_member(system.developers)
        self.is_guest = self.is_anonymous = self.login_id == system.guest
        self.is_authenticated = not self.is_anonymous

        # determine default app
        if self.is_anonymous:
            self.default_app = system.index
        else:
            self.default_app = system.home
            if self.default_app not in self.apps:
                self.default_app = system.index

        self.get_settings()

    def get_groups(self,user_id=None):
        def get_memberships(group,memberships,depth=0):
            result = [group]
            if depth < 100:
                for g,s in memberships:
                    if group == s and g not in result:
                        result += get_memberships(g,memberships,depth+1)
            return result

        my_groups   = [rec[0] for rec in system.database('SELECT groupid FROM dz_members WHERE userid=%s',user_id or self.user_id)]
        sub_groups  = [(rec.GROUPID,rec.SUBGROUPID) for rec in system.database('SELECT subgroupid,groupid FROM dz_subgroups ORDER BY subgroupid')]
        memberships = []
        for group in my_groups:
            memberships += get_memberships(group,sub_groups)
        groups = my_groups + memberships

        named_groups = []
        for rec in system.database('SELECT groupid, name FROM dz_groups'):
            groupid = rec[0]
            name    = rec[1].strip()
            if groupid in groups:
                named_groups += [name]

        return named_groups

    def get_settings(self):
        """load and set the user/context settings"""
        self.settings = system.settings.user_settings(self, system.config)
        self.theme = self.settings.get('theme_name')
        self.profile = self.settings.get_bool('profile')

    def can(self, action, thing):
        """test to see if user can action a thing object.

        Object thing must provide allows(user, action) method.
        """
        return thing.allows(self, action)

    def authorize(self, action, thing):
        """authorize a user to perform an action on thing

        If user is not allowed to perform the action an exception is raised.
        Object thing must provide allows(user, action) method.
        """
        if not thing.allows(self, action):
            raise UnauthorizedException('Unauthorized')


user = User()

