
from zoom import *
from zoom.fill import fill
from model import Groups, show_group_fields, group_fields, audit_log, get_user_names, get_group_names, last_group_update


def can_edit(group):
    return user.is_admin or group.admin in user.groups

class GroupFiller:
    def __init__(self, id):

        def item_list(items, app, relation):
            count = 1
            lines = []
            items.sort(key=lambda a: a[1])
            for item, label in items:
                link  = link_to(label,'/'+app+'/'+str(item))
                remove_url = url_for(str(id), relation, str(item), 'remove')
                trash = removal_icon(remove_url)
                lines.append('<tr><td>%s</td><td>%s</td></tr>' % ( link, trash))
            rows = ''.join(lines)

            button_name = 'ADD_' + relation.upper() + '_BUTTON'

            return form() + """
                <input type=text class="text_field" id=%(relation)s name=%(relation)s size=20>&nbsp;
                <input type=submit class="field_button" value="Add" name="%(button_name)s"></form><br>

                <div class="group_relationships_list">
                    <table>
                    %(rows)s
                    </table>
                </div>
                """ % locals()

        group = Groups.get(id)
        self.id = id
        self.members = self.subgroups = self.authorizations = 'nada' 
        self.fields = show_group_fields.show()
        self.name = 'name'
        self.members = item_list(group.members, 'users', 'member')
        self.subgroups = item_list(group.subgroups,'groups', 'subgroup')
        items = [(r.user,r.activity,r.subject1,r.subject2,r.timestamp,how_long_ago(r.timestamp)) for r in audit_log(group.name)]
        self.audit_log = browse(items,labels=['User','Activity','Subject1','Subject2','Timestamp','When'])
        self.relations = fill('{{','}}',"""
<table class="transparent" width=100%><tr>

<td width=33% valign=top>
<H2>Users</H2>
{{members}}
</td><td width=33% valign=top>

<H2>Includes</H2>
{{subgroups}}

</td><td width=33% valign=top>

</td></tr></table>

<br>
<br>
{{audit_log}}
        """,self)
        
    def __call__(self,name):
        return self.__dict__.get(name)

class CollectionController(Controller):

    def add_group_button(self, *a, **input):
        if group_fields.validate(input):
            id = Groups.insert(**group_fields.evaluate())
            return redirect_to(url_for('/groups/%s' % id))

    def delete(self, id, confirmed=False):
        if confirmed:
            group = Groups.get(id)
            if not(user.is_admin or group.admin in user.groups):
                return redirect_to('/groups')
            if group:
                group.delete()
                message('deleted %s' % group.name)
            return redirect_to(url_for('/groups'))

    def update_button(self, id, *a, **input):
        group = Groups.get(id)
        if not(user.is_admin or group.admin in user.groups):
            return redirect_to('/groups')
        if group_fields.validate(input):
            Groups.update(id, **group_fields.evaluate())
            return redirect_to(url_for('/groups/%s' % id))

    def add_member_button(self, group_id, member):
        group = Groups.get(group_id)
        if not(user.is_admin or group.admin in user.groups):
            return redirect_to('/groups')
        if member in get_user_names():
            Groups.get(group_id).add_member(member)
            return redirect_to(url_for('/groups/%s' % group_id))
        else:
            error('unknown username %s' % member)

    def add_subgroup_button(self, group_id, subgroup):
        group = Groups.get(group_id)
        if not(user.is_admin or group.admin in user.groups):
            return redirect_to('/groups')
        if subgroup in get_group_names():
            Groups.get(group_id).add_subgroup(subgroup)
            return redirect_to(url_for('/groups/%s'%group_id))
        else:
            error('unknown group  %s' % subgroup)

    def remove(self, group_id, relation, user_id):
        group = Groups.get(group_id)
        if not(user.is_admin or group.admin in user.groups):
            return redirect_to('/groups')
        if relation == 'member':
            Groups.get(group_id).remove_member(user_id)
        else:
            Groups.get(group_id).remove_subgroup(user_id)
        return redirect_to(url_for('/groups/%s'%group_id))

    def add_supergroup_button(self,group_id,name):
        group = Groups.get(group_id)
        if not(user.is_admin or group.admin in user.groups):
            return redirect_to('/groups')
        Groups.get(group_id).add_supergroup(name)
        return redirect_to(url_for('/groups/%s'%group_id))

    def supergroup(self,group_id,supergroup_id,action):
        group = Groups.get(group_id)
        if not(user.is_admin or group.admin in user.groups):
            return redirect_to('/groups')
        if action=='remove':
            Groups.get(group_id).remove_supergroup(supergroup_id)
        return redirect_to(url_for('/groups/%s'%group_id))

class CollectionView(View):

    def index(self):
        actions = 'New',
        items = [(
            link_to(group.name or 'missing','/groups/%s'%group.groupid),
            group.descr,
            group.admin or '',
            ) for group in Groups.user_groups(not user.is_admin and user.groups)]
        content =  browse(items, labels=self.labels, footer='%d groups' % len(items))

        # render content separately because markdown is slow for long tables
        p = page('<page_content>', title=self.collection_name, actions=actions)
        p.content = p.content.replace('<page_content>',content)

        return p
        
    def new(self):
        fields = self.collection_fields.edit()
        group_names = get_group_names()
        page = Page('new', locals().get)        

        page.js = """
        var known_group_names = %(group_names)s;

        $(function(){
            $( "#ADMIN" ).autocomplete({ source: known_group_names });
        })
        """ % locals()

        page.css = """ 
            .ui-menu-item { text-align: left; }
            div.content img.trash { border: none; margin: 0; }
            sdiv.content input { height: 30px; }
            """
        return page
        
    def show(self, id):     
        group = Groups.get(id)
        if not can_edit(group):
            return redirect_to('/groups')

        if group:
            show_group_fields.update(group.__dict__)

            user_names = get_user_names()
            group_names = get_group_names()

            if len(user_names) > 1000:
                user_names = [];

            js = """
            var known_user_names = %(user_names)s;
            var known_group_names = %(group_names)s;

            $(function(){
                $( "#member" ).autocomplete({ source: known_user_names });
                $( "#subgroup" ).autocomplete({ source: known_group_names });
            })
            """ % locals()

            page = Page('show', GroupFiller(id))
            page.js = js
            page.css = """ 
                .ui-menu-item { text-align: left; }
                div.content img.trash { border: none; margin: 0; }
                sdiv.content input { height: 30px; }
                """
            return page
        else:
            return Page(markdown('Groups\n====\nUnknown group'))

    def edit(self, id, **data):

        group = Groups.get(id)
        if not can_edit(group):
            return redirect_to('/groups')

        group_fields.update(data or group.__dict__)
        fields = group_fields.edit()
        group_names = get_group_names()

        page = Page('edit', locals().get)

        page.js = """
        var known_group_names = %(group_names)s;

        $(function(){
            $( "#ADMIN" ).autocomplete({ source: known_group_names });
        })
        """ % locals()

        page.css = """ 
            .ui-menu-item { text-align: left; }
            div.content img.trash { border: none; margin: 0; }
            sdiv.content input { height: 30px; }
            """
        return page

    def delete(self, id, confirmed=False):
        group = Groups.get(id)
        if not can_edit(group):
            return redirect_to('/groups')

        if not confirmed:
            group = Groups.get(id)
            name = group.name
            return Page("""
                <H1>Delete Group</H1>
                Are you sure you want to delete <strong>%s</strong> ?<br><br>
                <dz:form confirmed=True><dz:button label="Yes, I'm sure. Please delete." name="DELETE_BUTTON">&nbsp;&nbsp;<a href="/groups/%s">cancel</a></form>""" % (name,id))


class GroupView(CollectionView):
    collection_name = 'Groups'
    collection_fields = group_fields
    item_name = 'Group'
    labels = 'Group Name','Description','Administrators'

class GroupController(CollectionController): pass

controller = GroupController()
view = GroupView()


