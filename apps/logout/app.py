
from zoom import user, redirect_to, warning,  logger

def app():
    if not user.is_authenticated:
        warning('You are not logged in')
    else:
        username = user.username
        user_id = user.id
        user.logout()
        logger.info('user %(username)s successfully logged out' % locals())
        msg = '<a href="/users/%(user_id)s">%(username)s</a> logged out' % locals()
        logger.activity('session', msg)
    return redirect_to('/')


