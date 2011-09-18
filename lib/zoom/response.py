"""HTTP responses for various common responses.
"""
__all__ = ['HTMLResponse','PNGResponse','XMLResponse','TextResponse','RedirectResponse','FileResponse']

class Response:
    def __init__(self,content):
        self.headers = {}
        self.content = content
    def render_headers(self):
        return (''.join(["%s: %s\n" % (header, value) for header, value in self.headers.items()]))+'\n'
    def render(self):
        return self.render_headers() + self.content

class PNGResponse(Response):
    def __init__(self,content):
        Response.__init__(self,content)
        self.headers['Content-type']  = 'image/png'
        self.headers['Cache-Control'] = 'no-cache'
    def render(self):
        doc = self.content
        self.headers['Content-length'] = ('%s' % len(doc))
        return self.render_headers() + doc

class HTMLResponse(Response):
    """
    Render an HTML response.

    >>> import response
    >>> response.HTMLResponse('test123').render()
    'Content-length: 7\\nContent-type: text/html\\nCache-Control: no-cache\\n\\ntest123'

    """
    def __init__(self,content='',printed_output=''):
        Response.__init__(self,content)
        self.content        = content
        self.printed_output = printed_output
        self.headers['Content-type']  = 'text/html'
        self.headers['Cache-Control'] = 'no-cache'
    def render(self):
        doc = self.content.replace('{*PRINTED*}',self.printed_output)
        self.headers['Content-length'] = ('%s' % len(doc))
        return self.render_headers() + doc

class XMLResponse(Response):
    def __init__(self,content=''):
        Response.__init__(self)
        self.content       = content
        self.headers['Content-type']  = 'text/xml'
        self.headers['Cache-Control'] = 'no-cache'

    def render(self):
        doc = '<?xml version="1.0"?>%s' % self.content
        self.headers['Content-length'] = ('%s' % len(doc))
        return self.render_headers() + doc

class TextResponse(Response):
    def __init__(self,content=''):
        Response.__init__(self,content)
        self.headers['Content-type']  = 'text'
        self.headers['Cache-Control'] = 'no-cache'

    def render(self):
        doc = '%s' % self.content
        self.headers['Content-length'] = ('%s' % len(doc))
        return self.render_headers() + doc

class RedirectResponse(Response):
    def __init__(self,url):
        Response.__init__(self,'')
        self.headers['Location']  = url

class FileResponse(Response):
    def __init__(self,filename,content=None):
        Response.__init__(self,'')
        if content:
            self.content = content
        else:            
            self.content = file(filename,'rb').read()
        import os
        (path,fileonly) = os.path.split(filename)
        self.headers['Content-type']  = 'application/octet-stream'
        self.headers['Content-Disposition'] = 'attachment; filename="%s"' % fileonly
        self.headers['Cache-Control'] = 'no-cache'
    def render(self):
        doc = self.content
        self.headers['Content-length'] = ('%s' % len(doc))
        return self.render_headers() + doc

if __name__=='__main__':
    import doctest
    doctest.testmod()
