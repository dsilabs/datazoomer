
from model import *


class ForgotView(View):

    def index(self, email='', submit_button=''):
        return Page('index', dict(email=email).get)

    def step2(self):
        return Page('step2')
        
    def reset(self,token,**k):
        return process_reset_request(token)
        
    def expired(self):
        return Page('expired')
        
    def complete(self):
        return Page('complete')
        

class ForgotController(Controller):

    def submit_button(self, EMAIL):
        err = initiate_password_reset(EMAIL)            
        if err:
            error(err)
        else:            
            return home('step2')

    def reset_password_button(self, view, token, password="", confirm=""):
        return reset_password(token,password,confirm)
            
controller = ForgotController()
view = ForgotView()


        
