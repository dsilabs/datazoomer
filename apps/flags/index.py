
from model import *


INDEX_TEMPLATE = open('home.md').read()

class MyView(View):

    @authorize('admin', 'developers')
    def index(self):

        actions = "New",
        labels = "Title", "URL", "Link", "Icon", "Owner", ""
        refresh_url = '/'+route[0]

        # current list of flags
        flag_list = [i for i in flags]
        flag_list = browse(flags, labels=labels, on_delete='delete')

        # some example data
        items = [
                Record(title='Users', url='http://localhost/users'),
                Record(title='Groups', url='http://localhost/groups'),
                Record(title='Flags', url='http://localhost/flags'),
                ]

        for item in items:
            item['flags'] = ''
            for icon in ['mail','star','heart','thumbs-up','thumbs-down']:
                state = bool(flags.find(url=item.url, owner=user.username, icon=icon))
                item['flags'] += flag(item['title'], item['url'], icon=icon)
            
        test_list = browse(items , labels=('Title', 'URL', 'Flags'))

        # show page

        return page(markdown(INDEX_TEMPLATE %  locals()), title='Flags', actions=actions)

    def new(self):
        return page(flag_form.edit(), title='New Flag')

    def cancel(self):
        return home()

    def my_flags(self, n=None):
        icon = data.get('icon', None)
        n = data.get('n', None)
        return flag_list(icon, n)

    def show(self, name):
        filename = '%s.md' % name
        if os.path.exists(filename):
            return page(markdown(open(filename).read()))
        else:
            return page('%s missing' % name)


class MyController(Controller):

    def save_button(self, *a, **values):
        if flag_form.validate(values):
            self.toggle(**values)
            return home()

    def toggle(self, **values):
        if flag_form.validate(values):
            flagged = flags.first(url=values['URL'], owner=user.username, icon=values['ICON'])
            if flagged:
                flags.delete(flagged._id)
                return 'cleared'
            else:
                flagged = Flag(flag_form)
                flagged.user = user.username
                flagged.icon = values['ICON']
                flags.put(flagged)
                return 'set'
        else:
            return 'invalid %s' % repr((values))
        return 'okay'

    def delete(self, key):
        flag = flags.get(key)
        if flag:
            flags.delete(flag)
        return home()


view = MyView()
controller = MyController()


