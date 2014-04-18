
from zoom import user, redirect_to, warning,  logger

def app():
    if not user.is_authenticated:
        warning('You are not logged in')
    else:
        user.logout()
        logger.info('user successfully logged out')
    return redirect_to('/')


