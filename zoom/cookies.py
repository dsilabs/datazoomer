
import Cookie


SESSION_COOKIE_NAME = 'dz4sid'
SUBJECT_COOKIE_NAME = 'dz4sub'


def get_cookies(raw_cookie):
    cookie = Cookie.SimpleCookie(raw_cookie)
    result = dict([(k, cookie[k].value) for k in cookie])
    return result


def make_cookie():
    return Cookie.SimpleCookie()


def add_value(cookie, name, value, lifespan, secure):
    cookie[name] = value
    cookie[name]['httponly'] = True
    cookie[name]['expires'] = lifespan # in seconds
    if secure:
        cookie[name]['secure'] = True


def get_value(cookie):
    _, v = str(cookie).split(':', 1)
    return v


def set_session_cookie(response, session_id, subject, lifespan, secure=True):
    ONE_YEAR = 365 * 24 * 60 * 60
    cookie = make_cookie()
    add_value(cookie, SESSION_COOKIE_NAME, session_id, lifespan, secure)
    add_value(cookie, SUBJECT_COOKIE_NAME, subject, ONE_YEAR, secure)
    k,v = str(cookie).split(':',1)
    response.headers[k] = v

