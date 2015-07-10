
from zoom import *

class SignupEmail(Record): pass
signups = store(SignupEmail)

signup_form = Form(
        EmailField('Email', required, valid_email),
        ButtonField('Submit'),
        )

class MyController(Controller):

    def signup_form(self):
        return signup_form.edit()

    def index(self):
        message = """
        <p>Thanks for visiting.  <dz:site_name> is currently in development.  </p>
        <p>We\'re working on creating a great service and we hope you\'ll like it.</p>
        <p>Sign up and we\'ll let you know as soon as it\'s ready.</p><br>
        """
        return page(message + self.signup_form(), title='Sign Up')

    def thanks(self):
        return page('Thanks!  We\'ll keep you posted.<br><br>Please feel free to contact us at <dz:owner_email> if you have any questions.', title='Thank you!') 

    def submit_button(self, email=None):
        if signup_form.validate(data):
            signup = SignupEmail(signup_form)
            signups.put(signup)
            logger.info('%s signed up' % signup.email)
            logger.activity('signup', '<a href="mailto:{email}">{email}</a> signed up'.format(**signup))
            return home('thanks')

controller = MyController()

