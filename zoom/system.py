
import os
import web
import time
import types

from utils import threadeddict
from config import Config
from database import Database
from response import *

class NoApp:
    name = 'noapp'
    title = name

class System(threadeddict):


    def setup(self, instance_path, request):
        self.instance_path = instance_path
        self.config = config = Config()
        self.config.setup(instance_path, request.host)
        self.request = request
        self.server_name = request.host
        self.root = os.path.split(os.path.abspath(os.getcwd()))[0]
        self.uri = request.uri
        self.authentication = config.get('site','authentication','basic')
        self.them = config.get('theme','name','default')
        self.start_time = time.time()
        self.path = self.instance_path = os.path.abspath(config.instance_path)
        self.host = request.host
        self.theme = 'default'
        self.guest_username = config.get('site','guest','guest')
        self.warnings = []
        self.errors = []
        self.mesages = []
        self.app = NoApp()
        self.database = Database(config)


    def run(self):
    
        def load_app(name):
            #import numapp as app
            import app
            return app.app
            for path in self.app_paths:
                pathname = os.path.join(path, name, 'app.py')
                if os.path.exists(pathname):
                    mod = imp.load_source('app', pathname)
                    app = getattr(mod, 'app')
                    if app:
                        title = getattr(mod, 'title', name)
                        return title, app
    
        try:
            # Load and run the app that will handle the request
            request = self.request
            default_app = self.config.get('apps','index','content')
            target_app = request.route and request.route[0] or default_app
            app = load_app(target_app)
            result = app()
            if not isinstance(result, Response):
                if type(result) == types.StringType:
                    result = HTMLResponse(result)
                else:
                    result = HTMLResponse(str(result))
    
        except:
            import traceback
            result = TextResponse(traceback.format_exc())
            result.render()
    
        # Return the result
        for k,v in result.headers.iteritems():
            web.header(k,v)
        content = result.content
        web.header('Content-length',str(len(content)))
        return content


