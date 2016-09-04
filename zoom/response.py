# -*- coding: utf-8 -*-

"""
    zoom.response

    Various common web responses.
"""


from hashlib import md5

from .jsonz import dumps


class Response(object):
    """web response"""

    def __init__(self, content):
        self.status = '200 OK'
        self.headers = {}
        self.content = content

    def render_doc(self):
        """Renders the payload"""
        return self.content

    def render(self):
        """Renders the entire response"""

        def render_headers(headers):
            """bring headers together into one string"""
            return (''.join(["%s: %s\n" % (header, value) for header, value in
                             headers.items()]))

        doc = self.render_doc()
        length_entry = [('Content-length', '%s' % len(doc))]
        headers = render_headers(dict(self.headers.items() + length_entry))
        return ''.join([headers, '\n', doc])

    def render_wsgi(self):
        """Render the entire response"""
        doc = self.render_doc()
        length_entry = [('Content-length', '%s' % len(doc))]
        return self.status, self.headers.items() + length_entry, doc


class PNGResponse(Response):
    """PNG image response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/png'


class PNGCachedResponse(PNGResponse):
    """Cached PNG image response"""

    def __init__(self, content, age=86400):
        PNGResponse.__init__(self, content)
        self.headers['Cache-Control'] = 'max-age={}'.format(age)
        self.headers['ETag'] = md5(content).hexdigest()[:9]


class JPGResponse(Response):
    """JPG image response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/jpeg'


class GIFResponse(Response):
    """GIF image response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'image/gif'


class HTMLResponse(Response):
    """
    HTML response

    >>> import response
    >>> response.HTMLResponse('test123').render() == (
    ...     'X-FRAME-OPTIONS: DENY\\n'
    ...     'Content-type: text/html\\n'
    ...     'Content-length: 7\\n'
    ...     'Cache-Control: no-cache\\n\\n'
    ...     'test123'
    ... )
    True

    >>> response.HTMLResponse('test123').render_wsgi() == (
    ...    '200 OK',
    ...    [
    ...       ('X-FRAME-OPTIONS', 'DENY'),
    ...       ('Content-type', 'text/html'),
    ...       ('Cache-Control', 'no-cache'),
    ...       ('Content-length', '7')
    ...    ],
    ...    'test123'
    ... )
    True
    """

    def __init__(self, content='', printed_output=''):
        Response.__init__(self, content)
        self.printed_output = printed_output
        self.headers['Content-type'] = 'text/html'
        self.headers['Cache-Control'] = 'no-cache'
        self.headers['X-FRAME-OPTIONS'] = 'DENY'

    def render_doc(self):
        """Render HTML the payload including printed debugging output"""
        tpl = self.content.replace('{*PRINTED*}', self.printed_output)
        doc = tpl.encode('utf-8')
        return doc


class XMLResponse(Response):
    """XML response"""

    def __init__(self, content=''):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'text/xml'
        self.headers['Cache-Control'] = 'no-cache'

    def render_doc(self):
        doc = '<?xml version="1.0"?>%s' % self.content
        return doc


class TextResponse(Response):
    """Plan text response"""

    def __init__(self, content=''):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'text'
        self.headers['Cache-Control'] = 'no-cache'

    def render_doc(self):
        doc = '%s' % self.content
        return doc


class JavascriptResponse(TextResponse):
    """Javascript response"""

    def __init__(self, content):
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'application/javascript'


class JSONResponse(TextResponse):
    """JSON response"""

    def __init__(
        self,
        content,
        indent=4,
        sort_keys=True,
        ensure_ascii=False,
        **kwargs
    ):
        content = dumps(content, indent, sort_keys, ensure_ascii, **kwargs)
        TextResponse.__init__(self, content)
        self.headers['Content-type'] = 'application/json;charset=utf-8'


class CSSResponse(Response):
    """CSS response"""

    def __init__(self, content):
        Response.__init__(self, content)
        self.headers['Content-type'] = 'text/css;charset=utf-8'


class RedirectResponse(Response):
    """Redirect response"""

    def __init__(self, url):
        Response.__init__(self, '')
        self.status = '302 Found'
        self.headers['Location'] = url


class FileResponse(Response):
    """File download response"""

    def __init__(self, filename, content=None):
        Response.__init__(self, '')
        if content:
            self.content = content
        else:
            self.content = file(filename, 'rb').read()
        import os
        _, fileonly = os.path.split(filename)
        self.headers['Content-type'] = 'application/octet-stream'
        self.headers['Content-Disposition'] = \
                'attachment; filename="%s"' % fileonly
        self.headers['Cache-Control'] = 'no-cache'


class PDFResponse(FileResponse):
    """PDF file download response"""

    def __init__(self, filename, content=None):
        FileResponse.__init__(self, filename, content)
        self.headers['Content-type'] = 'application/pdf'
        del self.headers['Content-Disposition']

