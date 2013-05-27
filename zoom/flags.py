
from store import store
from zoom.utils import Record

def make_a_link(item):
    return '<a href="%(url)s">%(title)s</a>' % item

class Flag(Record):

    link = property(lambda a: make_a_link(a))

    def __init__(self, *a, **k):
        self.update(dict(url='', title='', icon=''))
        Record.__init__(self, *a, **k)

flags = store(Flag)

