
from zoom import *

class SignupEmail(Record): pass
signups = store(SignupEmail)

class MyController(Controller):

    def submit_button(self, email=None):
        if email:
            signup = SignupEmail(email=email)
            signups.put(signup)
            message('Thank you!')
            return home()
        else:            
            warning('Please enter your email address')

controller = MyController()


