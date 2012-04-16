

__all__ = ['System']

import os
import imp
import web
import timeit
import types

from utils import threadeddict
from config import Config
from database import Database
from response import *

class NoApp:
    name = 'noapp'
    title = name

def create_database(config):
    """Creates a database object"""

    engine = config.get('database', 'engine', 'mysql')

    if engine == 'mysql':
        params = dict(
                host = config.get('database', 'dbhost', 'localhost'),
                db = config.get('database', 'dbname', 'dzdev'),
                user = config.get('database', 'dbuser', 'dzadmin'),
                passwd = config.get('database', 'dbpass', ''),
                )
        import MySQLdb 
        db = Database(MySQLdb.Connect, **params)
        db.autocommit = True
        return db

    raise Exception('Unknown database engine %s' % repr(engine))

class System(threadeddict):

    elapsed_time = property(lambda a: timeit.default_timer() - a.start_time)


    def setup(self, instance_path, request):
        self.path = self.instance_path = os.path.abspath(instance_path)
        self.config = config = Config()
        self.host = request.host.split(':')[0]
        self.config.setup(instance_path, self.host)
        self.request = request
        self.server_name = request.host
        self.root = os.path.split(os.path.abspath(os.getcwd()))[0]
        self.uri = request.uri

        self.theme = config.get('theme', 'name', 'default')
        self.theme_path = config.get('theme', 'path', self.root + '/themes')

        self.start_time = timeit.default_timer()

        self.authentication = config.get('site', 'authentication', 'basic')
        self.guest_username = config.get('site', 'guest', 'guest')

        self.warnings = []
        self.errors = []
        self.mesages = []

        self.apps_path = config.get('apps','path','../apps')
        self.apps_paths = self.apps_path.split(';')
        self.default_app = self.config.get('apps','default','content')
        self.index_app = self.config.get('apps','index','content')
        self.home_app = self.config.get('apps','index','home')

        self.app = NoApp()
        self.database = create_database(config)

        self.username = 'anybody'

    def run(self):
    
        def locate_app(name):
            for path in self.apps_paths:
                path = os.path.abspath(os.path.join(self.instance_path, path, name))
                pathname = os.path.join(path, 'app.py')
                if os.path.exists(pathname):
                    return path
            raise Exception('Unable to locate app %s' % repr(name))

        def run_app(path):
            pathname = os.path.join(path, 'app.py')
            if os.path.exists(pathname):
                save_dir = os.getcwd()
                os.chdir(path)
                try:
                    self.internal_pathname = os.path.abspath(pathname)
                    mod = imp.load_source('app', pathname)
                    app = getattr(mod, 'app')
                    if app:
                        result = app()
                    else:
                        raise Exception('Unable to load app at %s' % repr(pathmame))
                finally:
                    os.chdir(save_dir)
            else:
                raise Exception('Unable to find app at %s' % repr(pathmame))
            return result
    
        try:
            # Determine which app should handle the request
            request = self.request
            self.target_app = request.route and request.route[0] or self.index_app or self.default_app

            # Locate the app that will handle the request
            app_path = locate_app(self.target_app)

            # Load the app
            result = run_app(app_path)

            # Prepare the response
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


