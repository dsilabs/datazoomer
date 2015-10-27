

from model import *

class MyView(View):

    title = 'User Settings'
    base_url = '/settings/user'
    preamble = """
<p>These settings allow an administrator or developer to override a subset of the system settings.  These overrides will be specific for the user setting the feature and will not impact other users of the system.</p>
    """

    def index(self, q="", **k):

        if route[-1:] == ['index']:
            return redirect_to(self.base_url)

        actions = ('Edit', 'user/edit'),
        load_user()
        content = user_settings_form.show()
        return page('{}{}'.format(self.preamble,content), title=self.title, actions=actions)

    def edit(self, reset_settings=False):
        if reset_settings:
            user_settings_form.initialize(user.settings.defaults)
        else:
            load_user()
        content = user_settings_form.edit()
        return page('{}{}'.format(self.preamble,content), title=self.title)

    def cancel(self):
        return redirect_to(base_url)

    def list(self):
        content = browse(user.settings.store.all(), labels=('Key','Value'))
        return page('{}{}'.format(self.preamble,content), title='All User Settings')

class MyController(Controller):

    def save_button(self):
        if user_settings_form.validate(data):
            save_user(user_settings_form)
            return redirect_to(view.base_url)

    def set_to_defaults_button(self):
        return redirect_to(url_for('user/edit', reset_settings=True))

    def reset_theme(self):
        save_user( (('theme_name', user.settings.defaults.get('theme_name')),) )
        return redirect_to(view.base_url)

view = MyView()
controller = MyController()

