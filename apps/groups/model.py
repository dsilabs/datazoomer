
from zoom import *
import datetime
from zoom.log import audit

db = system.database

valid_group_name = RegexValidator('letters, numbers "-","_" and "." only', r'^[a-zA-Z0-9.\-_]+$')
is_group = Validator("invalid group", lambda a: a in get_group_names())

class AppsField(MemoField):
    def display_value(self): return self.value

class SupergroupsField(MemoField):
    def display_value(self): return ' '.join([link_to(i[1],i[1]) for i in self.value])

class AdministratorField(TextField):
    def display_value(self): return self.value and link_to(self.value, self.value) or ''

def group_name_available(group_name):
    # TODO: optimize this, remove dependency on route
    return not bool(db('select * from dz_groups where name=%s and groupid<>%s', group_name, route[1]))

name_available = Validator('group exists', group_name_available)

group_fields = Fields(
    TextField('Name', required, MinimumLength(3), valid_group_name, name_available, size=20),
    TextField('Description', size=60, default='', name='DESCR'),
    TextField('Group Administrators', is_group, default=system.administrator_group, name='ADMIN'),
    )

show_group_fields = Fields(
    TextField('Name', size=20),
    TextField('Description', size=60, default='', name='DESCR'),
    AdministratorField('Group Administrators', default=system.administrator_group, name='ADMIN'),
    SupergroupsField('Roles', name='SUPERGROUPS'),
    AppsField('Apps', name='APPS'),
    )

def get_user_names():
    return [a.loginid for a in system.database('select loginid from dz_users where status="A" order by loginid')]

def get_group_names():
    return [a.name for a in system.database('select name from dz_groups where name not like "a\_%%" order by name')]

def last_group_update(name):
    latest = None
    for entry in audit_log(name):
        if not latest or entry.timestamp > latest:
            latest = entry.timestamp
    return latest and how_long_ago(latest) or ''

def audit_log(group):
    """Retreive the most recent entries from the audit log"""
    query = """
        select * 
        from audit_log 
        where subject2=%s 
        union select * 
        from audit_log 
        where activity in ("add group","remove group","create group","delete group") and subject1=%s 
        order by timestamp desc 
        limit 10
    """
    return db(query, group, group)


def get_group_apps(group):
    def get_memberships(group, memberships, depth=0):
        result = [group]
        if depth < 100:
            for g, s in memberships:
                if group == s and g not in result:
                    result += get_memberships(g, memberships, depth+1)
        return result

    sub_groups  = [(rec.GROUPID, rec.SUBGROUPID) for rec in db('SELECT subgroupid, groupid FROM dz_subgroups ORDER BY subgroupid')]
    permissions = get_memberships(group, sub_groups)

    named_groups = []
    for rec in db('SELECT groupid, name FROM dz_groups order by name'):
        groupid = rec[0]
        name    = rec[1].strip()
        if groupid in permissions and name.startswith('a_'):
            if 'apps' in user.apps:
                named_groups += ['<a href="/apps/%(a)s">%(a)s</a>' % dict(a=name[2:])]
            else:
                named_groups += ['%(a)s' % dict(a=name[2:])]

    return ' '.join(named_groups)


class Group:
    def __init__(self,*a,**k):
        self.__dict__ = k
        members = db("select * from dz_members")
        subgroups = db("select * from dz_subgroups")

        users = dict((i.userid,(i.userid,i.loginid)) for i in db('select userid,loginid from dz_users'))
        groups = dict((i.groupid,(i.groupid,i.name)) for i in db('select groupid, name from dz_groups'))
        apps = [i.groupid for i in db('select groupid, name from dz_groups') if i.name[:2]=='a_']
        
        self.members  = [users.get(i.userid,(i.userid,str(i.userid))) for i in members if i.groupid==self.id]
        self.subgroups  = [groups.get(i.subgroupid,(i.subgroupid,'%s missing'%i.subgroupid)) for i in subgroups if i.groupid==self.id]
        self.supergroups = [groups.get(i.groupid,(i.groupid,'%s missing'%i.groupid)) for i in subgroups if i.subgroupid==self.id and i.groupid not in apps]
        self.apps = get_group_apps(self.id)

    def __getitem__(self,name):
        return self.__dict__.get(name)

    def delete(self):
        return Groups.delete(self.id) 
        
    def add_member(self,name):
        users = dict((i.loginid,i.userid) for i in db('select userid,loginid from dz_users'))
        if name in users:
            id = users[name]
            db('insert into dz_members (userid,groupid) values (%s,%s)',id,self.id)
            audit('add user',name,self.name)
        
    def remove_member(self,user_id):
        users = dict((i.userid,i.loginid) for i in db('select userid,loginid from dz_users'))
        db('delete from dz_members where userid=%s and groupid=%s',user_id,self.id)
        audit('remove user',users[int(user_id)],self.name)
        
    def add_subgroup(self,name):
        groups = dict((i.name,i.groupid) for i in db('select name,groupid from dz_groups'))
        if name in groups:
            id = groups[name]
            db('insert into dz_subgroups (groupid,subgroupid) values (%s,%s)',self.id,id)
            audit('add group',name,self.name)
        
    def remove_subgroup(self,subgroup_id):
        groups = dict((i.groupid,i.name) for i in db('select groupid, name from dz_groups'))
        db('delete from dz_subgroups where groupid=%s and subgroupid=%s',self.id,subgroup_id)
        audit('remove group',groups[int(subgroup_id)],self.name)
        
    def add_supergroup(self,name):
        groups = dict((i.name,i.groupid) for i in db('select name,groupid from dz_groups'))
        if name in groups:
            id = groups[name]
            db('insert into dz_subgroups (groupid,subgroupid) values (%s,%s)',id,self.id)
            audit('add membership',self.name,name)
        
    def remove_supergroup(self,supergroup_id):
        groups = dict((i.groupid,i.name) for i in db('select groupid, name from dz_groups'))
        db('delete from dz_subgroups where groupid=%s and subgroupid=%s',supergroup_id,self.id)
        audit('remove membership',self.name,groups[int(supergroup_id)])
        
class Groups:

    @classmethod
    def all(cls):
        return db("select * from dz_groups")

    @classmethod
    def user_groups(cls, groups=None):
        if groups:
            fmt = ','.join(['%s'] * len(groups))
            cmd = "select * from dz_groups where not name like 'a\_%%%%' and admin in (%s) order by name" % fmt
            return db(cmd, *groups)
        else:
            return db("select * from dz_groups where not name like 'a\_%%' order by name")

    @classmethod
    def get(cls,key):
        result = db('select * from dz_groups where groupid=%s',key)
        if result:
            group = Group(
                name=result[0].name,
                descr=result[0].descr,
                admin=result[0].admin,
                id=result[0].groupid)
            return group
        else:
            result = db('select * from dz_groups where name=%s',key)
            if result:
                group = Group(
                    name=result[0].name,
                    descr=result[0].descr,
                    admin=result[0].admin,
                    id=result[0].groupid)
                return group

    @classmethod
    def delete(self,id):
        name = db('select name from dz_groups where groupid=%s', id)[0]['NAME']
        result = db('delete from dz_members where groupid=%s',id)
        result = db('delete from dz_groups where groupid=%s',id)
        result = db('delete from dz_subgroups where groupid=%s',id)
        result = db('delete from dz_subgroups where subgroupid=%s',id)
        audit('delete group', name, '')

    @classmethod
    def update(cls, id, **values):
        values['GROUPID'] = id
        values['TYPE'] = 'U'
        table = db.table('dz_groups','GROUPID')
        table.update(values)
    
    @classmethod
    def insert(cls,**keywords):
        group_fields.update(**keywords)
        values = group_fields.evaluate()
        values['TYPE'] = 'U'
        values['NAME'] = values['NAME'].lower()
        table = db.table('dz_groups','GROUPID')
        id = table.insert(values)
        audit('create group', values['NAME'], '')
        return id
    

if __name__ == '__main__':
    print 'done'
    
    groups = Groups()
    print groups.all()
    
    group = groups.get(2)
    print group.members
    print group.subgroups
    print group.supergroups
    
    
    
