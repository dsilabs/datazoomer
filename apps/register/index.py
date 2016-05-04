

from zoom import page, load_content, user, browse, load, system, home
from zoom.mvc import View, Controller, authorize
from zoom.html import ul

from model import (
    fields, Registration, registrations, get_errors, submit_registration,
    confirm_registration, delete_registration
)

class MyView(View):

    def index(self):

        if user.is_admin:
            labels = (
                'First Name',
                'Last Name',
                'Username',
                'Password',
                'Token',
                'Expires',
                'Action',
            )
            content = browse(registrations, labels=labels)
            return page(content, title='Registrations')

        messages = ul(get_errors(fields), Class='wrong')

        form = fields.edit()

        agreements = """
        By registering, I agree to the <dz:site_name> <a
        href="/terms.html">Terms of Use</a> and <a href="/privacy.html">Privacy
        Policy</a>.
        """

        content = load('registration.html')
        return page(
            content.format(fill=locals()),
            css=load('style.css'),
        )

class MyController(Controller):

    def register_now_button(self, *a, **k):
        if fields.validate(k):
            values = fields.evaluate()
            if values['PASSWORD'] == values['CONFIRM']:
                if submit_registration(values):
                    return page(load_content('step2.txt'))

    def confirm(self, token):
        result = confirm_registration(token)
        if user.is_admin:
            return home()
        return result

    @authorize('administrators')
    def delete(self, token):
        delete_registration(token)
        return home()

view = MyView()
controller = MyController()

