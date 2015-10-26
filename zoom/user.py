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
from auth import ctx, DataZoomerSaltedHash, BcryptDataZoomerSaltedHash

TWO_WEEKS = 14 * 24 * 60 * 60

def get_current_username():
    return \
        system.config.get('users','override','') or \
        system.session.login_id or \
        os.environ.get('REMOTE_USER',None) or \
        system.guest or \
        None

def authenticate(login_id, password):
    """ Authenticate the login """
    user_record = system.database("SELECT date_format(dtadd,'%%Y-%%m-%%d %%H:%%i:%%s'), password FROM dz_users WHERE loginid=%s and status='A';", login_id)
    if len(user_record)<>1: return False
    user_record = user_record[0]
    dtadd = lambda a: user_record[0]
    DataZoomerSaltedHash.salt_fn = dtadd
    BcryptDataZoomerSaltedHash.salt_fn = dtadd

    match, phash = ctx.verify_and_update(password, user_record[1])
    if match and phash:
        u = User(login_id)
        u.set_password(password, phash)
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

    >>> class User: pass
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

class User:
    link = property(lambda a: '<a href="/users/%s">%s</a>' % (a.username,a.username))

    def __init__(self, login_id=None):
        if login_id:
            self.initialize(login_id)
        self.is_developer = False
        self.is_administrator = False

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

    def set_password(self, password, phash=None):
        cmd = "UPDATE dz_users SET password=%s, dtupd=now() where loginid=%s"
        phash = phash is None and ctx.encrypt(password) or phash
        system.database(cmd, phash, self.login_id)

    def is_member(self, groups):
        return is_member(self, groups)

    def setup(self):
        return self.initialize()

    def initialize(self, login_id=None):

        if not login_id:
            login_id = get_current_username()

        select_user = "SELECT firstname, lastname, phone, loginid, password, email, userid, status FROM dz_users WHERE loginid=%s and status='A'"
        dataset = system.database(select_user,login_id)
        if not len(dataset):
            select_disabled_account = "SELECT firstname, lastname, phone, loginid, password, email, userid, status FROM dz_users WHERE loginid=%s and status<>'A'"
            dataset = system.database(select_disabled_account,login_id)
            if len(dataset) == 0:
                insert_user = "INSERT INTO dz_users (loginid,firstname,lastname,email,phone,status,dtupd,dtadd) values (%s,'','','','','A',%s,%s)"
                now = datetime.datetime.now()
                system.database(insert_user,login_id,now,now)
                dataset = system.database(select_user,login_id)
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
            raise Exception('Unable to intialize user.')

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
        self.is_anonymous = self.login_id == system.guest
        self.is_authenticated = not self.is_anonymous

        # determine default app
        if self.is_anonymous:
            self.default_app = system.index
        else:
            self.get_settings()
            if self.default_app not in self.apps:
                self.default_app = system.index

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
        from zoom import manager, EntityStore
        from settings import Settings, UserSystemSettings
        self.settings = Settings(
            EntityStore(system.db, UserSystemSettings),
            system.config,
            self.login_id   # hash this or something
          )
        get = self.settings.get
        self.theme = get('theme_name')
        self.default_app = get('home')
        self.profile = get('profile')

    def apply_settings(self):
        """apply the user context settings to the system"""
        if user.is_admin or user.is_developer:
            if hasattr(self, 'theme') and self.theme and self.theme<>system.theme:
                system.theme = self.theme
                system.set_theme(system.theme)
            if hasattr(self, 'profile') and self.profile<>system.profile:
                system.profile = self.profile

user = User()

#if __name__ != '__main__':
#    import os
#    user = User(get_current_username())
#
#else:
#    current_user = system.config.get('users','default','guest')


