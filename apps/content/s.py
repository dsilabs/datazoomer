
from zoom import *
from zoom.collect import *
from model import *


snippet_fields = Fields(
        TextField('Name', required),
        TextField('Variant'),
        MemoField('Body'),
        )


class Snippet(CollectionRecord):
    key = property(lambda a: a._id)
    when = property(lambda a: '%s by %s' % (how_long_ago(a.updated),a.updated_by))


class SnippetView(CollectionView):
    def __init__(self, collection):
        CollectionView.__init__(self, collection)

        # restore the menu
        system.app.menu = main_menu


class SnippetCollection(Collection):
    def __init__(self):
        Collection.__init__(self, 'Snippet', snippet_fields, Snippet, '/content/s')
        self.labels = 'Name', 'Variant', 'Impressions', 'Updated'
        self.columns = 'link', 'variant', 'impressions', 'when'


snippet_collection = SnippetCollection()
view = SnippetView(snippet_collection)
controller = CollectionController(snippet_collection)
