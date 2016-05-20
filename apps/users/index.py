
from model import *

class CollectionController(Controller):

    def update_button(self, id, *args, **data):
        if user_fields.validate(data):
            Users.update(id, **user_fields.evaluate())
            return redirect_to('/users/%s' % id)
        return Page('edit',dict(id=id, fields=user_fields.edit()).get)

    def delete(self,id,confirm=True):
        if confirm != True:
            item = Users.get(id)
            if item:
                name = item.get_full_name()
                item.delete()
                message('deleted %s'%name)
            return redirect_to('/users')

    def add_user_button(self, *a, **data):
        if new_user_form.validate(data):
            Users.insert(new_user_form)
            return home()

    def deactivate(self,id):
        account = Users.get(id)
        if account:
            account.deactivate()
            message('User account is deactivated')
        return redirect_to('/users/%s' % id)
        
    def activate(self,id):
        account = Users.get(id)
        if account:
            account.activate() 
            message('User account is activated')
        return redirect_to('/users/%s' % id)

    def save_password_button(self, id, *a, **data):
        if password_fields.validate(data):
            if data['PASSWORD'] == data['CONFIRM']:
                password = data['PASSWORD']
                username = get_username(id)
                user = ZoomUser(username)
                user.set_password(password)
                audit('set user password', username)
                if password_fields.evaluate()['RESEND_INVITATION'] == True:
                    recipients = [user.email]
                    tpl = load('welcome.md')
                    t = dict(
                            first_name = user.first_name,
                            username = username,
                            password = password,
                            site_name = site_name(),
                            site_url = site_url(),
                            admin_email = system.from_addr,
                            owner_name = owner_name(),
                            )
                    body = markdown(viewfill(tpl, t.get))
                    subject = 'Welcome - ' + site_name()
                    send(recipients, subject, body)
                    message('invitation sent')
                return redirect_to('/users/%s' % id)
            else:
                error('passwords do not match')

        
class CollectionView(View):

    def index(self, q='', showall=''):

        many_records = len(system.users) > 5

        options = Storage(index_recent=many_records)
        actions = []

        if q:
            title = 'Selected Users'
            users = Users.all()
            search_terms = list(set([i.lower() for i in q.strip().split()]))
        else:
            if options.index_recent and not showall:
                title = 'Recent Users'
                users = Users.recent()
                actions.append(('Show All',system.app.name + '/showall'))
            else:
                title = 'Users'
                users = Users.all()

        actions.append('New')

        items = []
        for user in users:
            if not q or matches(user.as_dict(), search_terms):
                item = dict(
                        username = link_to(user.loginid or user.userid,'/users/%s'%user.userid),
                        sort_by = user.loginid and user.loginid.lower(),
                        name = (user.firstname or '') +' '+ (user.lastname or ''),
                        email = user.email,
                        phone = user.phone,
                        registered = user.dtadd,
                        last_seen = how_long_ago(user.timestamp)
                        )
                items.append(item)

        user_count = len(items)
        if q:
            footer = '%s users found' % user_count
        elif user_count <> len(system.users):
            footer = '%s most recent users of %s total users' % (user_count, len(system.users))
        else:
            footer = '%s users' % user_count

        labels= self.labels
        return page(browse(items, labels=labels, footer=footer), title=title, search=q, actions=actions)
        
    def clear(self):
        return home()

    def showall(self):
        return redirect_to('/%s?showall=1' % system.app.name)

    def new(self):
        return page(new_user_form.edit(), title='Add New User')

    def cancel(self):
        return home()
        
    def show(self, id):
        from zoom.user import User
        from zoom.manager import manager

        user = Users.get(id)
        if user:
            user_fields.update(user.__dict__)
            edit_button = '<a id="edit-button" class=action href="/users/%s/edit">Edit</a>' % (id)
            password_button = '<a id="password-button" class=action href="/users/%s/password">Set Password</a>' % (id)
            deactivate_button = '<a id="deactiveate-button" class=action href="/users/%s/deactivate">Deactivate</a>' % (id)
            activate_button = '<a id=activate-button class=action href="/users/%s/activate">Activate</a>' % (id)
            delete_button = '<a id="delete-button" class=action href="/users/%s/delete">Delete</a>' % (id)
            if user.status == 'A':
                actions = deactivate_button
                status = ''
            else:
                actions = activate_button
                status = ('<div style="display:inline;padding-left:10px;font-size:0.8em;">(deactivated)</tab>')
            actions = delete_button + actions + password_button + edit_button + '<div style="clear:both"></div>'
            u = User(user['username'])

            activity_data = db('select id, timestamp, route, status, address, elapsed, message from log where user=%s and timestamp>=%s order by timestamp desc limit 50', user.username, today-26*one_week)
            labels = 'id', 'When', 'Route', 'Status', 'Address', 'Elapsed', 'Message'
            activity = browse([(
                link_to(a[0], abs_url_for('/info/system-log', a[0])),
                '<span title="%s">%s</span>' % (a[1], how_long_ago(a[1])),
                a[2],a[3],a[4],a[5],a[6][:40]) for a in activity_data], labels=labels)

            auth_data = db('select * from audit_log where (subject1=%s or subject2=%s) and timestamp>=%s order by timestamp desc limit 20', user.username, user.username, today-26*one_week)
            labels = 'id', 'App', 'User', 'Activity', 'Subject1', 'Subject2', 'Timestamp'
            auth_activity = browse([(a[0],a[1],a[2],a[3],a[4],a[5],a[6]) for a in auth_data], labels=labels)

            apps = [a.name for a in manager.apps.values() if a.name in (hasattr(u,'apps') and u.apps or [])]
            page = Page('show',dict(
                id=id,
                fields=user_fields.show(),
                full_name=user.get_full_name(),
                roles = ' &nbsp;'.join([link_to(g,'/groups/%s'%g) for g in sorted(hasattr(u,'roles') and u.roles or [])]),
                apps = ' &nbsp;'.join([link_to(g,'/apps/%s'%g) for g in sorted(apps)]),
                actions = actions,
                status = status,
                activity = activity,
                auth_activity = auth_activity,
                ).get)
            return page

    def edit(self, id):
        user = Users.get(id)
        user_fields.update(**user.__dict__)
        return Page('edit',dict(
            id=id,
            fields=user_fields.edit(),
            ).get)

    def delete(self,id,confirm=True):
        if confirm:
            user = Users.get(id)
            name = user.get_full_name()
            return Page("""
                <H1>Delete User</H1>
                Are you sure you want to delete <strong>%s</strong> ?<br><br>
                <dz:form confirm=False><dz:button label="Yes, I'm sure. Please delete." name=delete_button>&nbsp;&nbsp;<dz:link_to "cancel" "/users/{{id}}"></form>""" % name, dict(id=id).get)

    def password(self, id, generate=False, **data):
        user = Users.get(id)
        if generate:
            password = gen_password()
            password_fields.update(dict(PASSWORD=password, CONFIRM=password))
        return Page("""
            <H1>Set Password</H1>
            %s
            <div class=field>
              <div class=field_label>&nbsp;</div>
              <div class=field_edit>
                <a href="/users/%s/password?generate=1">generate a new password</a>
              </div>
            </div>
            <dz:form>
            %s
            <div class=field>
              <div class=field_label>&nbsp;</div>
              <div class=field_edit>
                <dz:button label="Save Password" name=save_password_button>&nbsp;&nbsp;<dz:link_to "cancel" "/users/%s"> 
              </div>
            </div>
            </form>
            """ % (TextField('Usename',value=user.username).show(), id, password_fields.edit(), id))

class UserView(CollectionView):
    collection_name = 'Users'
    collection_fields = user_fields
    item_name = 'User'
    labels = ['Username','Name','Email','Phone','Registered','Last Seen']

class UserController(CollectionController): pass

controller = UserController()
view = UserView()


