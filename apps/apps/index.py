
from model import *
from zoom.fill import fill

css = load('style.css')
js = load('script.js')

simple_format = system.config.get('apps','simple_format','') in ['1']

apps_list_tpl = \
"""
<ul class="app-list">
%s
<div style="clear:both"></div>
</ul>
<div>
</div>
"""

app_info_tpl = \
"""
<li class="%(selectors)s">
    <div class="app-info">
        <div class="app-text">
            <div class="app-title">
                <a href="/apps/%(name)s">%(title)s</a>
            </div>
            <div class="app-description">
                %(descr)s<br>
                updated %(modified)s
            </div>
        </div>
        <div class="app-icon">
            <a href="/apps/%(name)s"><img src="/static/dz/icons/%(icon)s.png"></a>
        </div>
        <div style="clear:both"></div>
    </div>
    <div style="clear:both"></div>
</li>
"""

related_info_tpl = """
<br>
<table width=100%%><tr>
<td width=33%% valign=top>
<H2>User Groups</H2>
%s
</td></tr></table>
<br>
<br>
<H3>Activity Log</H3>
%s
"""

group_list_tpl = """
<input type=text style="height:25px;" name="name" size=20>
<input type=submit class="add-button button" class="add-button" value="Add" name="add_%s_button">
</form>
<br>
<table class="baselist grouplist" border=0 width=200px>
%s
</table>
"""

def groups_edit(name):

    def item_list(items, name, relation):
        count = 1
        lines = []
        for item, label in items:
            link  = link_to(label,'/groups',str(item))
            trash = trash_can(name, 'remove', str(label), 'remove_group') #'removegroup/'+label)
            style = count % 2 and 'light' or 'dark'
            lines.append('<tr class="%s"><td width=90%%>%s</td><td>%s</td></tr>' % (style, link, trash))
        url = url_for('/apps',name)
        return form(action=url) + \
            group_list_tpl % (relation,''.join(lines))

    id = db('select groupid from dz_groups where type="A" and name=%s','a_'+name)[0].GROUPID
    
    groups = dict((i.groupid,(i.groupid,i.name)) for i in db('select groupid, name from dz_groups'))
    subgroups = db("select * from dz_subgroups where groupid=%s", id)
    subgroup_items = [groups.get(i.subgroupid,(i.subgroupid,'%s missing'%i.subgroupid)) for i in subgroups]
    audit_log_list = browse(audit_log(name),labels=['User','Activity','Subject','Timestamp','When'])
    subgroup_list = item_list(subgroup_items, name, 'group')

    return related_info_tpl % (subgroup_list, audit_log_list)



class MyView(View):

    def index(self):
        def get_categories(apps, selector):
            items = ['Miscellaneous']
            for app in apps:
                if app.categories:
                    for category in app.categories:
                        items.append(category)
            items = sorted(set(items), key=lambda a:a.lower())
            return '<ul>%s</ul>' % ''.join('<li id="%s">%s</li>' % \
                    (selector+'-'+id_for(i),i) for i in items)

        installed_categories_list = get_categories(installed_apps,'installed')
        not_installed_categories_list = get_categories(uninstalled_apps,'uninstalled')

        apps = installed_apps
        if user.is_administrator:
            apps += uninstalled_apps

        content = apps_list_tpl % ''.join(app_info_tpl % a for a in installed_apps)

        installed_app_count = len(installed_apps)
        app_count = len(installed_apps) + len(uninstalled_apps)
        user_app_count = len(user_apps)

        selected_apps = content

        if simple_format and True:
            content = []
            content.append(html.tag('h2','Installed'))
            for app in sorted(installed_apps, key=lambda a:a.name.lower()):
                 content.append('<a href="/apps/%(id)s">%(name)s</a> ' % dict(id=id_for(app.name), name=app.name))
            content.append(html.tag('h2','Not Installed'))
            for app in sorted(uninstalled_apps, key=lambda a:a.name.lower()):
                content.append('<a href="/apps/%(id)s">%(name)s</a> ' % dict(id=id_for(app.name), name=app.name))
            return page(''.join(content), title='Apps')

        tpl = load('main_panel.html')
        content = fill('{{', '}}', tpl, locals().get)

        p = page('<content>', title='Apps', css=css, js=js)

        p.content = p.content.replace('<content>',content)
        return p


    def show(self, name):
        app = get_app(name)
        app_form.update(app)

        if app.installed:
            app_form.fields.append(ButtonField('Uninstall'))
        else:
            app_form.fields.append(ButtonField('Install'))

        content = app_form.edit()

        if app.installed:
            content += groups_edit(name)

        return page(content,title='App Details',css=css)


class MyController(Controller):

    def install_button(self,name):
        app = App(name=name)
        app.install()
        return home(name)


    def uninstall_button(self,name):
        app = App(name=name)
        app.uninstall()
        return home(name)


    def add_group_button(self, app, name):
        get_app(app).add_group(name)
        return home(app)


    def remove_group(self, app, name):
        get_app(app).remove_group(name)
        return home(app)

view = MyView()
controller = MyController()


