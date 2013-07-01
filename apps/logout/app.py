
from zoom import user, redirect_to, warning

def app():
    if not user.is_authenticated:
        warning('You are not logged in')
    else:
        user.logout()
    return redirect_to('/')


