
from zoom import *
from zoom.user import user_exists, deactivate_user
from zoom.log import logger


class CustomUsernameField(TextField):
    def edit(self):
        return """
        <div class="form-group">
            <input class="form-control" placeholder="Username" id="USERNAME" name="username" type="text" value="%s">
        </div>
        """ % data.get('username','')


class CustomPasswordField(PasswordField):
    def edit(self):
        return """
        <div class="form-group">
            <input class="form-control" placeholder="Password" id="PASSWORD" name="password" type="password" value="">
        </div>
        """


class RememberMeField(TextField):
    def edit(self):
        return """
        <div class="checkbox">
            <label>
                <input name="remember_me" type="checkbox" value="Remember Me"> Remember Me
            </label>
        </div>
        """

class HiddenReferrerField(Hidden):
    def edit(self):
        return """
        <div class="form-group">
            <input class="form-control" placeholder="Redirect after login" id="REFERRER" name="REFERRER" type="hidden" value="%s">
        </div>
        """ % data.get('referrer','')

login_form = Fields(
    CustomUsernameField('Username', required, valid_username, size=20, value=data.get('username','')),
    CustomPasswordField('Password', required, size=20),
    HiddenReferrerField('Referrer'),
    RememberMeField('Remember Me'),
    )


def potential_attack(username):
    # If user has 5 successive failed login attempts account is locked
    log_entries = system.database('select * from log where user=%s order by timestamp desc limit 5', username)
    security_issues = [i for i in log_entries if i.status=='S']
    return len(security_issues) >= 5


class LoginController(Controller):

    def index(self):

        if request.method == 'POST' and 'LOGIN_BUTTON' not in data:
            username = data['USERNAME']
            password = data['PASSWORD']

            if user.login(username, password):
                return 'OK'
            else:
                return 'FAIL'

    def login_button(self):

        if login_form.validate(data):

            values = login_form.evaluate()

            username = values['USERNAME']
            password = values['PASSWORD']
            remember_me = values['REMEMBER_ME']

            as_api = os.environ.get('HTTP_ACCEPT','') == 'application/json'

            if user_exists(username):
                if potential_attack(username):
                    deactivate_user(username)
                    logger.security('user account (%s) deactivated' % username)
                elif user.login(username, password, remember_me):
                    if as_api:
                        logger.info('user %s successfully logged in via api' % username)
                        return '{}'
                    else:
                        username = user.username
                        user_id = user.id
                        msg = '<a href="/users/%(user_id)s">%(username)s</a> logged in' % locals()
                        logger.activity('session', msg)
                        logger.info('user %s successfully logged in' % username)

                        referrer = values.get('REFERRER')
                        if referrer:
                            return redirect_to(referrer)
                        return redirect_to('/'+user.default_app)
            else:
                logger.security('unknown username (%s)' % username)
            logger.security('failed login attempt', username)

            if as_api:
                return '{"message": "invalid username or password"}'
            else:
                error('invalid username or password')


def fill(tag,*a,**k):
    if tag == 'username':
        return data.get('USERNAME','')
    elif tag == 'referrer':
        return data.get('referrer','')
    elif tag == 'form':
        return login_form.edit()
    elif tag == 'registration_link':
        return 'register' in user.apps and '<a href="register">New User?</a>' or ''
    elif tag == 'forgot_link':
        return 'forgot' in user.apps and '<div style="margin-top:1em"><strong>Help!</strong>&nbsp;&nbsp;<a href="forgot">I forgot my password</a></div>' or ''

def view(login_id='',*a,**k):
    page = Page(__name__, fill)
    if not login_id:
        focus = 'username'
    else:
        focus = 'password'
    page.js = """
        $(document).ready(function() {
            $("#%s").focus();
        });
    """ % focus
    return page

controller = LoginController()



