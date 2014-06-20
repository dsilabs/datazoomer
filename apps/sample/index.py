
from zoom import *

app_name = 'sample'
url = '/' + app_name

provinces = ['British Columbia','Alberta','Saskatchewan','Manitoba','Quebec','Ontario']
cities = ['Victoria','Prince George','Vancouver','Nanaimo','Edmonton']
large_hint = """This is a large hint. This is a large hint. This is a large hint. This is a large hint. This is a large hint. This is a large hint. This is a large hint. This is a large hint. This is a large hint.  """

my_form = Fields(
        Section('Personal',[
            TextField('Name',required,size=20,value='John Doe', hint='this is a hint'),
            TextField('Address',required,value='1234 Somewhere St', hint='this is a hint'),
            DateField('Birthdate',required),
            TextField('Other',required),
            PhoneField('Phone',value='123-456-7890'),
            PulldownField('Province',value='Alberta',options=provinces,hint=large_hint),
            CheckboxesField('Provinces',value=['Alberta','Quebec'],values=provinces, hint=large_hint * 4),
            MultiselectField('Cities',value=['Victoria','Vancouver'], options=cities, hint=large_hint * 4),
            CheckboxField('Notify Me', hint='this is a hint'),
            CheckboxField('Save Prefereces', value=True, hint='this is another hint'),
            RadioField('How Many',value='One',values=['One','Two','Three'], hint='this is a hint'),
            MemoField('Notes',hint='this is a hint'),
            ]),
        Section('Social',[
            TextField('Twitter',size=15,value='jdoe',hint='optional'),
            ]),
        ButtonField('Save'),
        )
small_form = Fields(
        TextField("Name",size=20),
        TextField("Address"),
        )

def load(filename):
    path = os.path.split(__file__)[0]
    pathname = os.path.join(path, filename)
    content = open(pathname, 'r').read()
    if filename[-3:] == '.md':
        return markdown(content)
    else:
        return content


tpl = load('sample.md')


def query(cmd, *a, **k):
    data = system.database(cmd, *a, **k)
    if data:
        names = [name.lower() for name in data[0].column_names()]
        return [names] + data.data
    return []

class MyView(View): 

    def index(self):
        actions = 'System Messages', 'Choose Theme'
        form1 = my_form.edit()
        form2 = my_form.show()
        form3 = small_form.edit()
        name = 'a value'
        data = browse(query('select userid id, loginid username, email, phone from dz_users limit 10'))
        return page(tpl, callback=locals().get, actions=actions)

    def choose_theme(self):
        return page(markdown('Themes\n====\nSomeday that button might enable you to choose a theme to view the sample page with.\n\n [back](/sample)'))

    def information(self):
        message('This is an informational messsage')
        return home('messages')

    def warning(self):
        warning('This is a warning messsage')
        return home('messages')

    def error(self):
        error('This is an error messsage')
        return home('messages')

    def system_messages(self, **data):
        msg = \
"""
System Messages
====

Messages
----
* [Information Messsage](information)
* [Warning Message](warning)
* [Error Message](error)

Exceptions
----
* [Developer Exception](/sample/developer_exception)
* [User Exception](/sample/user_exception)
* [Low System Error](/sample/system_error)

"""
        return page(markdown(msg))


class MyController(Controller):

    def save_button(self, **data):
        if my_form.validate(data):
            message('looks good!')
            return page('Form Variables\n====\nThe following data was posted\n\n<code>%s</code>\n\n[Return to Main Page](/sample)' % data)
            return redirect_to(url)
        else:
            warning('please try again')
            error('missing data?')

    def developer_exception(self, **data):
        raise Exception('This is what an error looks like to a developer')

    def user_exception(self, **data):
        from zoom.startup import FRIENDLY_ERROR_MESSAGE
        tpl = FRIENDLY_ERROR_MESSAGE + '\n\n<br><br><br><br>\n_(This is what an error looks like to a user)_'
        return page(tpl)

    def system_error(self, **data):
        from zoom.startup import SYSTEM_ERROR_TEMPLATE
        tpl = ''.join(SYSTEM_ERROR_TEMPLATE.splitlines()[2:]) 
        return tpl % 'This is what a system error looks like'

view = MyView()
controller = MyController()

