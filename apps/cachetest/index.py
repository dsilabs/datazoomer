
import time
from zoom import *
from zoom.mvc import *
from zoom.cache import cached, clear_cache, Entry


actions = [
    ('Home','/' + system.app.name),
    ('View Cache','/%s/list' % system.app.name),
    ('Clear Cache','/%s/clear' % system.app.name),
    ]

class MyView(View):

    def index(self):
        content = markdown("""
A toy app to demonstrate the caching mechanism.

This is some content\n
* [go to cached content](cachetest/cached-page)\n
* [go to cached content with 3 second expire](cachetest/cached-page-with-expire)\n
* [go to parameterized cached content](cachetest/cached-page-with-params)
""")
        return page(content, title='Cache Tester', actions=actions)

    @cached
    def cached_page_content(self, first_name='', last_name=''):
        time.sleep(4)
        return markdown('Hello %s %s\n\nit usually takes a long time to generate this content\n\n' % (first_name, last_name))

    def cached_page(self):
        start_time = time.time()
        result = page(self.cached_page_content('Joe', last_name='Smith'), title='Cached Page', actions=actions)
        end_time = time.time()
        if end_time - start_time > 2:
            warning('slow page')
        else:
            message('cached page')
        return result

    @cached(expire=3)
    def cached_page_content_with_expire(self, first_name='', last_name=''):
        time.sleep(4)
        return markdown('Hello %s %s\n\nit usually takes a long time to generate this content\n\n' % (first_name, last_name))

    def cached_page_with_expire(self):
        start_time = time.time()
        result = page(self.cached_page_content_with_expire('Joe', last_name='Smith'), title='Cached Page', actions=actions)
        end_time = time.time()
        if end_time - start_time > 2:
            warning('slow page')
        else:
            message('cached page')
        return result

    @cached('test', user.username, expire=3)
    def cached_page_content_with_params(self, first_name='', last_name=''):
        time.sleep(4)
        return markdown('Hello %s %s\n\nit usually takes a long time to generate this content\n\n' % (first_name, last_name))

    def cached_page_with_params(self):
        start_time = time.time()
        result = page(self.cached_page_content_with_params('Joe', last_name='Smith'), title='Cached Page', actions=actions)
        end_time = time.time()
        if end_time - start_time > 2:
            warning('slow page')
        else:
            message('cached page')
        return result

    def clear(self):
        clear_cache('cached_page_content')
        message('cleared cache')
        return home()

    def list(self):
        entries = store(Entry)
        if entries:
            return page(browse(store(Entry)), actions=actions, title='Cache Contents')
        else:
            return page('cache is empty', title='No Cache', actions=actions)

view = MyView()

