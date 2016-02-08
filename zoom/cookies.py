
import Cookie


SESSION_COOKIE_NAME = 'dz4sid'
SUBJECT_COOKIE_NAME = 'dz4sub'


def get_cookies(raw_cookie):
    cookie = Cookie.SimpleCookie(raw_cookie)
    result = dict([(k, cookie[k].value) for k in cookie])
    return result


def set_session_cookie(response, request, lifespan, secure=True):
    cookie = Cookie.SimpleCookie()

    cookie[SESSION_COOKIE_NAME] = request.session_id
    cookie[SESSION_COOKIE_NAME]['httponly'] = True
    cookie[SESSION_COOKIE_NAME]['expires'] = 60 * lifespan

    cookie[SUBJECT_COOKIE_NAME] = request.subject
    cookie[SUBJECT_COOKIE_NAME]['httponly'] = True
    cookie[SUBJECT_COOKIE_NAME]['expires'] = 365 * 24 * 60 * 60

    if secure:
        cookie[SESSION_COOKIE_NAME]['secure'] = True
        cookie[SUBJECT_COOKIE_NAME]['secure'] = True

    k,v = str(cookie).split(':',1)
    response.headers[k] = v

