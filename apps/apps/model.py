
import stat
import time

from zoom import *

db = system.database

class LabelField(TextField):
    def edit(self): return self.show()

app_form = Form(
        LabelField('Name'),
        LabelField('Title'),
        LabelField('Location',name='DIR'),
        LabelField('Modified'),
        LabelField('Description'),
        #LabelField('Icon'),
        )

registered_apps = [rec.name[2:] for rec in db('select name from dz_groups where type="A"')]

class Apps:

    def all(self):
        return manager.apps

    def find(self, name):
        pass

def last_modified(app):
    file_stats = os.stat(app.dir)
    modified = tuple(time.localtime(file_stats[stat.ST_MTIME]))
    return how_long_ago(datetime.datetime(*modified[:7]))

def get_app(name):
    return App(manager.apps[name].__dict__)

def get_selectors(app):
    classes = []

    if app.categories:
        classes = [(app.installed and 'installed-' or 'uninstalled-') + id_for(c) for c in app.categories]
    else:
        classes = [(app.installed and 'installed-' or 'uninstalled-') + 'miscellaneous']

    if app.installed and 'a_'+app.name in user.groups:
        classes.append('your-apps')

    return ' '.join('select-%s' % c for c in classes)

class App(Entity): 

    descr = property(lambda a: a.description or a.name + ' application')
    icon_image = property(lambda a: '<img src="/static/dz/icons/%s">' % a.icon)
    modified = property(lambda a: last_modified(a))
    location = property(lambda a: a.dir)
    installed = property(lambda a: a.name in registered_apps)
    selectors = property(lambda a: get_selectors(a))
    #' '.join('category-'+id_for(i) for i in a.categories))

    def install(self):
        group_name = 'a_' + self.name

        cmd = 'insert into dz_groups (type,name,descr) values (\'A\',%s,%s)'
        db(cmd, group_name, group_name + ' application group')

        group_rec = db('select * from dz_groups where type="U" and name=%s', self.name)
        if group_rec:
            self.add_group(self.name)

    def uninstall(self):
        group_name = 'a_' + self.name

        rec = db('select groupid from dz_groups where type="A" and name=%s', group_name)
        if rec:
            id = rec[0].GROUPID
            db('delete from dz_groups where groupid=%s', id)
            db('delete from dz_subgroups where subgroupid=%s', id)
            db('delete from dz_members where groupid=%s', id)
            db('delete from dz_groups where groupid=%s', id)

    def add_group(self, group):
        group_rec = db('select * from dz_groups where type="A" and name=%s', 'a_'+self.name)
        if group_rec:
            group_id = group_rec[0].GROUPID
            subgroup_rec = db('select groupid from dz_groups where type="U" and name=%s', group)
            if subgroup_rec:
                subgroup_id = subgroup_rec[0].GROUPID
                rec = db('insert into dz_subgroups (groupid,subgroupid) values (%s,%s)', group_id, subgroup_id)
                audit('grant', group, self.name)
            else:
                error('unknown group %s' % group)
        else:
            error('unknown app %s' % self.name)

    def remove_group(self, group):
        group_rec = db('select * from dz_groups where type="A" and name=%s', 'a_'+self.name)
        if group_rec:
            group_id = group_rec[0].GROUPID
            subgroup_rec = db('select groupid from dz_groups where type="U" and name=%s', group)
            if subgroup_rec:
                subgroup_id = subgroup_rec[0].GROUPID
                rec = db('delete from dz_subgroups where groupid=%s and subgroupid=%s', group_id, subgroup_id)
                audit('revoke', group, self.name)
            else:
                error('unknown group %s' % group)
        else:
            error('unknown app %s' % self.name)


apps = sorted([App(a.__dict__) for a in manager.apps.values()], key=lambda a: a.title)
installed_apps = [app for app in apps if app.installed]
uninstalled_apps = [app for app in apps if not app.installed]
user_apps = [app for app in apps if app.installed and 'a_'+app.name in user.groups]

def audit(action, subject1, subject2):
    db('insert into audit_log (app,user,activity,subject1,subject2,timestamp) values (%s,%s,%s,%s,%s,%s)',
        'apps',
        user.login_id,
        action,
        subject1,
        subject2,
        now)

def audit_log(group):
    d = db('select * from audit_log where subject2=%s order by timestamp desc limit 10',group)
    items = [(r.user,r.activity,r.subject1,r.timestamp,how_long_ago(r.timestamp)) for r in d]
    return items
        
trash_tpl = """
<div class="trash">
<a href="%(link)s">
<img id="%(id)s" src="/themes/%(theme)s/images/%(kind)s.png" border=0 height=13px width=13px alt="%(kind)s">
</a>
</div>
"""

def trash_can(key, kind, action, *args, **keywords):
    link  = url_for(str(key), action, *args, **keywords)
    return trash_tpl % dict(id=name_for('remove_group_'+action+'_icon'), link=link, kind=kind, theme=system.theme)


