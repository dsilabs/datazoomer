
from zoom import *
from zoom.user import user_exists, deactivate_user
from zoom.log import logger

class Controller:
    def __call__(self,*a,**k):
        if request.method == 'POST':
            return self.POST(*a, **k)
        
def potential_attack(username):
    # If user has 5 successive failed login attempts account is locked
    log_entries = system.database('select * from log where user=%s order by timestamp desc limit 5', username)
    security_issues = [i for i in log_entries if i.status=='S']
    return len(security_issues) >= 5

class LoginController(Controller):
    def POST(self, USERNAME, PASSWORD, LOGIN_BUTTON='', url=''):
        
        if LOGIN_BUTTON:
            if user_exists(USERNAME):

                if potential_attack(USERNAME):
                    deactivate_user(USERNAME)
                    logger.security('user account deactivated')

                elif user.login(USERNAME, PASSWORD):
                    return redirect_to('/')
            else:
                logger.security('unknown username (%s)' % USERNAME)

            logger.security('failed login attempt', USERNAME)
            error('invalid username or password')

        else:
	        # API call
            if user.login(USERNAME, PASSWORD):
                return 'OK'
            else:
                return 'FAIL'

def fill(tag,*a,**k):
    if tag == 'username':
        return webvars.USERNAME
    elif tag == 'registration_link':
        return 'register' in user.apps and '<a href="register">New User?</a>' or ''
    elif tag == 'forgot_link':
        return 'forgot' in user.apps and '<br><strong>Help!</strong>&nbsp;&nbsp;<a href="forgot">I forgot my password</a>' or ''

def view(login_id='',*a,**k):
    page = Page(__name__, fill)
    if not login_id:
        focus = 'USERNAME' 
    else:
        focus = 'PASSWORD'
    page.js = """
        $(document).ready(function() {
            $("#%s").focus();
        });
    """ % focus
    return page

controller = LoginController()    



