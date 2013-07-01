
from zoom import *
from zoom.collect import *
from model import *


class Snippet(Record):
    key = property(lambda a: str(a._id))
    object_url = property(lambda a: '/content/s/'+a.key)
    url = object_url
    linked_name = property(lambda a: link_to(a.name, a.object_url))
    when = property(lambda a: '%s by %s' % (how_long_ago(a.updated),a.updated_by))
    #products_url = property(lambda a: '/products?m='+a.key)
    #item_count = property(lambda a: count_items(a.url))
    #description_markdown = property(lambda a: markdown(a.description))

snippet_fields = Fields(
        TextField('Name', required),
        TextField('Variant'),
        MemoField('Body'),
        )

class Collection:
    name_column = 'name'
    order = lambda t,a: (a.name, a.variant)
    can_edit = lambda a: True

    @classmethod
    def locate(cls, key):
        def scan(store, key):
            for rec in store:
                if rec.key == key:
                    message('found by brute force by Collection class')
                    return rec
        return (key.isdigit() and cls.store.get(key) or 
                cls.store.find(key=key) or 
                scan(cls.store,key))

class SnippetCollection(Collection):
    name = 'Snippets'
    item_name = 'Snippet'
    labels = 'Name', 'Variant', 'Impressions', 'Updated'
    columns = 'linked_name', 'variant', 'impressions', 'when'
    entity = Snippet
    store = store(Snippet)
    url = '/content/s'
    fields = snippet_fields

snippet_collection = SnippetCollection()

class SnippetView(CollectionView):
    def __init__(self, collection):
        CollectionView.__init__(self, collection)
        system.app.menu = main_menu

class SnippetController(CollectionController):
    pass

view = SnippetView(snippet_collection)
controller = SnippetController(snippet_collection)
