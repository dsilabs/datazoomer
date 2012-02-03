
import web
import timer

class Request(web.threadeddict):

    def setup(self, context):
        self.update(self,
            path = context.path,
            host = context.host,
            home = context.home,
            uri = context.path,
            ip = context.ip,
            query = context.query,
            port = context.environ['SERVER_PORT'],
            server = context.environ.get('SERVER_NAME','localhost'),
            agent = context.environ.get('HTTP_USER_AGENT',''),
            method = context.method,
            route = context.path!='/' and context.path[1:].split('/') or [],
            data = web.input(),
            cookies = web.cookies(),
            )


