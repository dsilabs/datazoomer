#!/usr/bin/env python
"""encapsulates system differences"""

import web

class WebpySystem:
    def dispatch(self):
        import app
        result = app.app()
        for k,v in result.headers.iteritems():
            web.header(k,v)
        content = result.content
        web.header('Content-length',str(len(content)))
        return result.content

    def run(self):
        platform = web.application(('/.*',self.dispatch),globals())
        platform.run()

def run():
    s = WebpySystem()
    s.run()

