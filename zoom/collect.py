
from os import environ as env

from zoom import *

dumps = json.dumps


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


class CollectionView(View):
    def __init__(self, collection):
        self.collection = collection

    def index(self, *a, **k):
        if route[-1:] == ['index']:
            return redirect_to('/'+'/'.join(route[:-1]),**k)

        c = self.collection
        actions = c.can_edit() and ['New'] or []

        items = sorted(c.store, key=c.order)

        if env.get('HTTP_ACCEPT','') == 'application/json':
            return dumps([item for item in items])
        else:
            if len(items) != 1:
                footer_name = c.name
            else:
                footer_name = c.item_name
            footer = '%s %s' % (len(items), footer_name.lower())
            content = browse(items, labels=c.labels, columns=c.columns, fields=c.fields, footer=footer)
            return page(content, title=c.name, actions=actions)

    def show(self, key):
        c = self.collection
        actions = c.can_edit() and ['Edit', 'Delete'] or []
        record = c.locate(key)
        if record:
            c.fields.update(record)

            if 'updated' in record and 'updated_by' in record:
                memo = '<br><span class="meta" style="float:right"> updated %(updated)s by %(updated_by)s</span>' % record
            else:
                memo = ''
            return page(c.fields.show() + memo, title=c.item_name, actions=actions)
        else:
            return page('%s missing' % key)

    def new(self):
        c = self.collection
        if c.can_edit():
            form = Form(c.fields, ButtonField('Create', cancel=c.url))
            return page(form.edit(), title=c.item_name)

    def edit(self, key, **data):
        c = self.collection
        if c.can_edit():
            record = c.locate(key)
            if record:
                c.fields.update(record)
                c.fields.update(data)
                form = Form(c.fields, ButtonField('Save', cancel=record.url))
                return page(form.edit(), title=c.item_name)
            else:
                return page('%s missing' % key)

    def delete(self, key, confirm='YES'):
        c = self.collection
        if c.can_edit():
            if confirm == 'YES':
                c = self.collection
                record = c.locate(key)
                if record:
                    return page(delete_form(record[c.name_column], key), title='Delete %s' % c.item_name)


class CollectionController(Controller):

    def __init__(self, collection):
        self.collection = collection

    def create_button(self, *a, **data):
        c = self.collection
        if c.can_edit():
            if c.fields.validate(data):
                record = c.entity()
                record.update(c.fields)
                record.CREATED = now
                record.UPDATED = now
                record.owner = user.username
                record.created_by = user.username
                record.updated_by = user.username
                c.store.put(record)
                return redirect_to(c.url)

    def save_button(self, key, *a, **data):
        c = self.collection
        if c.can_edit():
            if c.fields.validate(data):
                record = c.locate(key)
                if record:
                    record.update(c.fields)
                    record.UPDATED = now
                    record.updated_by = user.username
                    c.store.put(record)
                    return redirect_to('%s/%s'%(c.url, key))

    def delete(self, key, CONFIRM='YES'):
        c = self.collection
        if c.can_edit():
            if CONFIRM != 'YES':
                record = c.locate(key)
                if record:
                    c.store.delete(record)
                    return redirect_to(c.url)


