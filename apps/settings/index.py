

from model import *

class MyView(View):

    title = 'System Settings'

    def index(self, q="", **k):

        if route[-1:] == ['index']:
            return redirect_to('/settings')

        actions = 'Edit',
        load()
        content = system_settings_form.show()
        return page(content, title=self.title, actions=actions)

    def edit(self, reset_settings=False):
        if reset_settings:
            initialize()
        else:
            load()
        content = system_settings_form.edit()
        return page(content, title=self.title)

    def cancel(self):
        return redirect_to('/settings')

    def list(self):
        content = browse(system.settings.store.all(), labels=('Key','Value'))
        return page(content, title='All Settings')

class MyController(Controller):

    def save_button(self):
        if system_settings_form.validate(data):
            save(system_settings_form)
            return home()

    def set_to_defaults_button(self):
        return redirect_to(url_for('edit', reset_settings=True))

    def reset_theme(self):
        save( (('theme_name', get_defaults().get('theme_name')),) )
        return home()

view = MyView()
controller = MyController()

