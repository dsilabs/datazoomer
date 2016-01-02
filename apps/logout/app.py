
import os
from zoom import user, redirect_to, warning,  logger

def app():
    as_api = os.environ.get('HTTP_ACCEPT','') == 'application/json'

    if not user.is_authenticated:
        if as_api:
            return '{"message": "not logged in"}'
        else:
            warning('You are not logged in')
    else:

        # save these because they are about to get wiped out
        username = user.username
        user_id = user.id

        user.logout()

        if as_api:
            logger.info('user %(username)s successfully logged out via api' % locals())
            return '{}'
        else:
            msg = '<a href="/users/%(user_id)s">%(username)s</a> logged out' % locals()
            logger.activity('session', msg)
            logger.info('user %(username)s successfully logged out' % locals())
    return redirect_to('/')


