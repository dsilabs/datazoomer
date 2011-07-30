#!/usr/bin/env python
"""encapsulates system differences"""

import web

def app():
    import os
    from response import HTMLResponse
    e = repr(os.environ)
    return HTMLResponse('Hello, world.\n<br>' + e)

class WebpySystem:
    def dispatch(self):
        result = app()
        for k,v in result.headers.iteritems():
            web.header(k,v)
        content = result.content
        web.header('Content-length',str(len(content)))
        return result.content

    def run(self):
        platform = web.application(('/.*',self.dispatch),globals())
        platform.run()

class ApacheSystem:
    def dispatch(self):
        result = app()
        return result.render()

    def run(system_config_pathname='../sites/zoom.ini',hostname=None):
        import sys
        result = self.dispatch()
        sys.stdout.write(result)



