
import cookielib
import urllib
import urllib2
from zoom.jsonz import loads, dumps

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders.append(('Accept','application/json'))

def get_test_site():
    import os
    return os.environ.get('DATAZOOMER_TEST_SITE', 'http://localhost')

class API:
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
        values = urllib.urlencode(dict(USERNAME=username, PASSWORD=password))
        response = opener.open(site_url+'/login', values).read()
        if response != 'OK':
            raise Exception('Unable to login to {}\nresponse: {}\n'.format(site_url, response))

    def close(self):
        opener.open(self.site_url+'/logout').read()

    def GET(self,*a,**k):
        values = urllib.urlencode(k)
        response = opener.open('/'.join([self.site_url]+list(a))+'?'+values).read()
        try:
            result = loads(response)
        except:
            print 'JSON Conversion Failed: response was %s' % repr(response)
            result = response
        return result

    def get(self, *a, **k):
        return self.GET(*a, **k)

    def post(self, *a, **data):
        url = '/'.join([self.site_url]+list(a))
        encoded = urllib.urlencode(data)
        response = opener.open(url, encoded).read()
        try:
            result = loads(response)
        except:
            print 'JSON Conversion Failed: response was %s' % repr(response)
            result = response
        return result

    def __call__(self, *a, **k):
        return self.post(*a, **k)

if __name__ == '__main__':

    api = API(test_site, 'admin', 'admin')

    connected = api.get('ping')
    print connected

    api.close()


