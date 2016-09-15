"""
    zoom.api

    Accesses a datazoomer site via the API.
"""
import cookielib
import urllib
import urllib2

from zoom.jsonz import loads


def get_opener():
    """get a url opener"""
    cookie_jar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    opener.addheaders.append(('Accept', 'application/json'))
    return opener


def get_test_site():
    """get test site URL"""
    import os
    return os.environ.get('DATAZOOMER_TEST_SITE', 'http://localhost')


class API(object):
    """
        Connect to and interact with a datazoomer site.

        Note: request header specifies json but it's up to the app
              to decide whether or not to respect that.

        >>> test_site = get_test_site()
        >>> api = API(test_site, 'admin', 'admin')
        >>> api.get('ping')
        True
        >>> api.close()

    """

    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.opener = get_opener()
        values = urllib.urlencode(dict(USERNAME=username, PASSWORD=password))
        response = self.opener.open(site_url+'/login', values).read()
        if response != 'OK' and response != '{}':
            msg = 'Unable to login to {}\nresponse: {}\n'
            raise Exception(msg.format(site_url, response))

    def close(self):
        """close the connection"""
        self.opener.open(self.site_url+'/logout').read()

    def get(self, *a, **k):
        """get a response from the remote site"""
        values = urllib.urlencode(k)
        url = '/'.join([self.site_url]+list(a))+'?'+values
        response = self.opener.open(url).read()
        try:
            result = loads(response)
        except Exception:
            print 'JSON Conversion Failed: response was %s' % repr(response)
            result = response
        return result

    def post(self, *a, **data):
        """post data to the remote site"""
        url = '/'.join([self.site_url]+list(a))
        encoded = urllib.urlencode(data)
        response = self.opener.open(url, encoded).read()
        if response.lower() in ['ok', 'error']:
            result = dict(status=response.lower())
        else:
            try:
                result = loads(response)
            except Exception:
                msg = 'JSON Conversion Failed: response was %s'
                print msg % repr(response)
                result = response
        return result

    def __call__(self, *a, **k):
        """post data to the remote site"""
        return self.post(*a, **k)
