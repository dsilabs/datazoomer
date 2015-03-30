
from model import *


INDEX_TEMPLATE = open('home.md').read()
INDEX_JS = """
    $(function(){
        $('#mymail').load('/flags/my_flags?icon=mail');
        $('#mystars').load('/flags/my_flags?icon=star');
        $('#myheart').load('/flags/my_flags?icon=heart');
    });
"""

class MyView(View):

    @authorize('admin', 'developers')
    def index(self):

        def row_actions(f):
            return '<a href="/{}/delete/{}">delete</a>'.format(
                    system.app.name, 
                    f._id)

        actions = "New",
        labels = "Title", "URL", "Link", "Icon", "Owner", "Actions"
        refresh_url = '/'+route[0]

        # current list of flags
        flag_list = browse(
                [dict(f, actions=row_actions(f)) for f in flags], 
                labels=labels)

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

        return page(
                markdown(INDEX_TEMPLATE %  locals()),
                title='Flags',
                actions=actions,
                js=INDEX_JS
                )

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

    def page_three(self):
        return page(lorem(), title='Page 3', subtitle='<dz:flag "Page 3">')

    def page_four(self):
        title = 'Page 4'
        return page(
                lorem(),
                title=title, 
                subtitle='<dz:flag icon="heart" "{}">'.format(title))


class MyController(Controller):

    def save_button(self, *a, **values):
        if flag_form.validate(values):
            self.toggle(**values)
            return home()

    def toggle(self, **values):

        logger.info(repr(values['ICON']))
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
            logger.info('invalid %s' % repr((values)))
            return 'invalid %s' % repr((values))
        return 'okay'

    def delete(self, key):
        flag = flags.get(key)
        if flag:
            flags.delete(flag)
        return home()


view = MyView()
controller = MyController()


