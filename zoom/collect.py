
from os import environ as env
from zoom import *
from zoom.response import PNGResponse
from zoom.log import logger
from exceptions import PageMissingException

dumps = json.dumps
duplicate_key_msg = "There is an existing record with that name or key already in the database"

class Text:
    def __init__(self, text):
        self.value = text

    def edit(self):
        return markdown('%s\n' % self.value)

    def evaluate(self):
        return {}


def delete_form(name, key):
    return Form(
            Text('Are you sure you want to delete **%s**?' % name),
            Hidden(name='CONFIRM', value='NO'),
            Button('Yes, I''m sure.  Please delete.', name='DELETE_BUTTON', cancel='/'+'/'.join(route[:-1]))
            ).edit()

def locate(c, key):
    def scan(store, key):
        for rec in store:
            if rec.key == key:
                return rec
    return key.isdigit() and c.store.get(key) or \
            c.store.first(key=key) or \
            scan(c.store,key)

class CollectionView(View):
    def __init__(self, collection):
        self.collection = collection

    def index(self, q='', *a, **k):
        def matches(item, search_text):
            f.update(item)
            v = repr(f.display_value()).lower()
            return search_text and not any(t.lower() not in v for t in search_text.split())

        if route[-1:] == ['index']:
            return redirect_to('/'+'/'.join(route[:-1]),**k)

        c = self.collection
        f = self.collection.fields
        actions = c.can_edit() and ['New'] or []

        if q:
            logger.activity(system.app.name, '%s searched %s with %r' % (user.link, c.name.lower(), q))

        items = sorted((i for i in c.store if not q or matches(i,q)), key=c.order)

        if env.get('HTTP_ACCEPT','') == 'application/json':
            return dumps([item for item in items])
        else:
            if len(items) != 1:
                footer_name = c.name
            else:
                footer_name = c.item_name
            footer = '%s %s' % (len(items), footer_name.lower())
            content = browse(
                    [c.entity(i) for i in items],
                    labels=c.labels,
                    columns=c.columns,
                    fields=c.fields,
                    footer=footer)
            return page(content, title=c.name, actions=actions, search=q)

    def clear(self):
        return redirect_to('/' + '/'.join(route[:-1]))

    def show(self, locator):
        def action_for(r, name):
            return name, '/'.join([r.url, id_for(name)])

        def actions_for(r, *names):
            return [action_for(r, n) for n in names]

        c = self.collection
        record = locate(c, locator)
        if record:
            actions = c.can_edit() and actions_for(record, 'Edit', 'Delete') or []
            c.fields.initialize(c.entity(record))

            if 'updated' in record and 'updated_by' in record:
                memo = '<div class="meta" style="float:right"> record updated %(updated)s by %(updated_by)s</div><div style="clear:both"></div>' % record
            else:
                memo = ''
            return page(c.fields.show() + memo, title=c.item_name, actions=actions)
        else:
            raise PageMissingException

    def new(self):
        c = self.collection
        if c.can_edit():
            form = Form(c.fields, ButtonField('Create', cancel=c.url))
            return page(form.edit(), title='New '+c.item_name)

    def edit(self, key, **data):
        c = self.collection
        if c.can_edit():
            record = locate(c, key)
            if record:
                c.fields.initialize(record)
                c.fields.update(data)
                form = Form(c.fields, ButtonField('Save', cancel=record.url))
                return page(form.edit().decode('utf8'), title=c.item_name)
            else:
                return page('%s missing' % key)

    def delete(self, key, confirm='YES'):
        c = self.collection
        if c.can_edit():
            if confirm != 'NO':
                c = self.collection
                record = locate(c, key)
                if record:
                    return page(delete_form(record[c.name_column], key), title='Delete %s' % c.item_name)

    def image(self, key, name):
        record = self.collection.locate(key)
        if record:
            return PNGResponse(record[name])




class CollectionController(Controller):

    def __init__(self, collection):
        self.collection = collection

    def create_button(self, *a, **data):
        c = self.collection
        if c.can_edit():
            if c.fields.validate(data):
                record = c.entity()
                record.update(c.fields)
                record.pop('key',None)
                try:
                    key = record.key
                except AttributeError:
                    key = None
                if key and locate(c, record.key) is not None:
                    error(duplicate_key_msg)
                else:
                    record.created = now
                    record.updated = now
                    record.owner = user.username
                    record.created_by = user.username
                    record.updated_by = user.username
                    try:
                        record.key = record.key # property to attribute for storage
                    except AttributeError:
                        pass # can happen when key depends on database auto-increment value
                    c.store.put(record)
                    logger.activity(system.app.name, '%s added %s %s' % (user.link, c.item_name.lower(), record.linked_name))
                    return redirect_to(c.url)

    def save_button(self, key, *a, **data):
        c = self.collection
        if c.can_edit():
            if c.fields.validate(data):
                record = locate(c, key)
                if record:
                    record.update(c.fields)
                    record.pop('key',None)
                    if record.key <> key and locate(c, record.key):
                        error(duplicate_key_msg)
                    else:
                        record.updated = now
                        record.updated_by = user.username
                        record.key = record.key # property to attribute for storage
                        c.store.put(record)
                        logger.activity(system.app.name, '%s edited %s %s' % (user.link, c.item_name.lower(), record.linked_name))
                        return redirect_to(record.url)

    def delete(self, key, CONFIRM='YES'):
        c = self.collection
        if c.can_edit():
            if CONFIRM == 'NO':
                record = locate(c, key)
                if record:
                    c.store.delete(record)
                    logger.activity(system.app.name, '%s deleted %s %s' % (user.link, c.item_name.lower(), record.linked_name))
                    return redirect_to(c.url)

    def delete_image(self, key, name):
        record = self.collection.locate(key)
        if record:
            del record[name]
            self.collection.store.put(record)
            return redirect_to(url_for(record.url,'edit'))


class CollectionRecord(DefaultRecord):
    key = property(lambda self: id_for(self.name))
    url = property(lambda self: url_for_page(route[1], self.key)) # not ideal, but works
    link = property(lambda self: link_to(self.name, self.url))


class Collection(object):

    def is_manager(self):
        return user.is_member(['managers'])

    name_column = 'name'
    sort_by = lambda t,a: a.name_column
    can_edit = is_manager
    order = lambda t,a: a[a.sort_by].lower()

    def __init__(self, item_name, fields, entity):
        self.item_name = item_name
        self.name = item_name + 's'
        self.fields = fields
        self.entity = entity
        self.labels = [f.label for f in fields.as_list()]
        self.columns = [(n==0 and 'link' or f.name.lower()) for n,f in enumerate(fields.as_list())]
        self.store = store(entity)
        self.url = '/{}/{}'.format(system.app.name, id_for(self.name))

    def locate(self, key):
        def scan(store, key):
            for rec in store:
                if rec.key == key or rec.href_id == key:
                    return rec
        return key.isdigit() and self.store.get(key) or self.store.first(key=key) or scan(self.store, key)

    def __call__(self, *a, **k):
        # To use a Collection as an app
        controller = CollectionController(self)
        view = CollectionView(self)
        return controller(*a, **k) or view(*a, **k)





