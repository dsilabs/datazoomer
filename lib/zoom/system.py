#!/usr/bin/env python
"""encapsulates system differences"""

import web
import os
from config import config

__all__ = ['System']

def get_site_name():
    return web.ctx['host'].split(':')[0]

class System:

    def dispatch(self):
        self.site_name = get_site_name()
        config.setup(self.path,self.site_name)
        self.site_path = os.path.join(os.path.abspath(self.path),self.site_name)
        self.theme_path = os.path.abspath(config.get('theme','path','../themes'))
        self.app_paths = [os.path.abspath(path) for path in config.get('apps','path','../apps').split(',')]

        import app
        result = app.app()
        for k,v in result.headers.iteritems():
            web.header(k,v)
        content = result.content

        web.header('Content-length',str(len(content)))
        return content

    def run(self,instance_path):
        self.path = os.path.abspath(instance_path)
        platform = web.application(('/.*',self.dispatch),globals())
        platform.run()

