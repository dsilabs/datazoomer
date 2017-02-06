"""
    manages collections of things
"""

import os
from os import environ as env

from . import json
from .system import system
from .request import route
from .browse import browse
from .page import page
from .user import user
from .mvc import View, Controller
from .tools import now, redirect_to
from .utils import DefaultRecord, id_for
from .fields import Form, ButtonField, Hidden, Button, MarkdownText
from .helpers import link_to, error, url_for, url_for_page
from .store import EntityStore, store
from .response import PNGResponse
from .log import logger
from .exceptions import PageMissingException
from .buckets import Bucket
from .models import Attachment
from .response import JPGResponse, GIFResponse

dumps = json.dumps
duplicate_key_msg = "Record already exists"


def delete_form(name, key):
    """produce a delete form"""
    return Form(
        MarkdownText('Are you sure you want to delete **%s**?' % name),
        Hidden(name='CONFIRM', value='NO'),
        Button(
            'Yes, I''m sure.  Please delete.',
            name='DELETE_BUTTON',
            cancel='/'+'/'.join(route[:-1])
        )
    ).edit()


def locate(collection, key):
    """locate a record"""
    def scan(store, key):
        for rec in store:
            if rec.key == key:
                return rec
    return (
        key.isdigit() and
        collection.store.get(key) or
        collection.store.first(key=key) or
        scan(collection.store, key)
    )


def image_response(name, data):
    """provide an image response based on the file extension"""
    _, ext = os.path.splitext(name.lower())
    if ext == '.png':
        return PNGResponse(data)
    elif ext == '.jpg':
        return JPGResponse(data)
    elif ext == '.gif':
        return GIFResponse(data)


class CollectionView(View):

    def __init__(self, collection):
        self.collection = collection

    def index(self, q='', *a, **k):

        def matches(item, search_text):
            terms = search_text and search_text.split()
            f.update(item)
            v = repr(f.display_value()).lower()
            return terms and not any(t.lower() not in v for t in terms)

        if route[-1:] == ['index']:
            return redirect_to('/'+'/'.join(route[:-1]), **k)

        c = self.collection
        f = self.collection.fields
        actions = user.can('create', c) and ['New'] or []

        if q:
            msg = '%s searched %s with %r' % (user.link, c.name.lower(), q)
            logger.activity(system.app.name, msg)

        authorized = (i for i in c.store if user.can('read', i))
        matching = (i for i in authorized if not q or matches(i, q))
        filtered = (not q and hasattr(c, 'filter') and
                    c.filter and filter(c.filter, matching)) or matching
        items = sorted(filtered, key=c.order)

        if env.get('HTTP_ACCEPT', '') == 'application/json':
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
        """show a record"""
        def action_for(r, name):
            return name, '/'.join([r.url, id_for(name)])

        def actions_for(r, *names):
            return [action_for(r, n) for n in names]

        c = self.collection
        record = locate(c, locator)
        if record:
            user.authorize('read', record)

            actions = []
            if user.can('update', record):
                actions.append(action_for(record, 'Edit'))
            if user.can('delete', record):
                actions.append(action_for(record, 'Delete'))
            c.fields.initialize(c.entity(record))

            if 'updated' in record and 'updated_by' in record:
                memo = (
                    '<div class="meta" style="float:right">'
                    ' record updated %(updated)s by %(updated_by)s'
                    '</div>'
                    '<div style="clear:both"></div>'
                ) % record
            else:
                memo = ''
            return page(
                c.fields.show() + memo,
                title=c.item_name,
                actions=actions
            )
        else:
            raise PageMissingException

    def new(self):
        c = self.collection
        user.authorize('create', c)
        form = Form(c.fields, ButtonField('Create', cancel=c.url))
        return page(form.edit(), title='New '+c.item_name)

    def edit(self, key, **data):
        c = self.collection

        user.authorize('update', c)

        record = locate(c, key)
        if record:
            user.authorize('read', record)
            user.authorize('update', record)

            c.fields.initialize(record)
            c.fields.update(data)
            # attempt to go back to the listing if that is where we came from (if not from show method)
            cancel_url = (
                system.request.referrer and (len(route) - len(system.request.referrer.split('/')[3:])) > 1 and
                c.url or
                record.url
            )
            form = Form(c.fields, ButtonField('Save', cancel=cancel_url))
            return page(form.edit(), title=c.item_name)
        else:
            return page('%s missing' % key)

    def delete(self, key, CONFIRM='YES'):
        c = self.collection

        user.authorize('delete', c)

        if CONFIRM != 'NO':
            c = self.collection
            record = locate(c, key)
            if record:
                user.authorize('read', record)
                user.authorize('delete', record)
                return page(
                    delete_form(record[c.name_column], key),
                    title='Delete %s' % c.item_name
                )

    def image(self, key, name):
        record = self.collection.locate(key)
        if record:
            return PNGResponse(record[name])

    def list_images(self, key=None, value=None):
        """return list of images for an ImagesField value for this record"""
        attachments = store(Attachment)
        path = os.path.join(system.site.data_path, 'buckets')
        bucket = Bucket(path)
        t = [dict(
            name=a.attachment_name,
            size=a.attachment_size,
            item_id=a.attachment_id,
            url=url_for('get_image', item_id=a.attachment_id),
            ) for a in attachments.find(field_value=value)]
        return json.dumps(t)

    def get_image(self, *a, **k):  # pylint: disable=W0613
        """return one of the images from an ImagesField value"""
        item_id = k.get('item_id', None)
        path = os.path.join(system.site.data_path, 'buckets')
        bucket = Bucket(path)
        return image_response('house.png', bucket.get(item_id))


class CollectionController(Controller):

    def __init__(self, collection):
        self.collection = collection

    def create_button(self, *a, **data):  # pylint: disable=W0613
        c = self.collection

        user.authorize('create', c)

        if c.fields.validate(data):
            record = c.entity()
            record.update(c.fields)
            record.pop('key', None)
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
                record.owner_id = user.user_id
                record.created_by = user.username
                record.updated_by = user.username
                try:
                    # convert property to data attribute
                    # so it gets stored as data
                    record.key = record.key
                except AttributeError:
                    # can happen when key depends on database
                    # auto-increment value.
                    pass
                c.store.put(record)
                logger.activity(system.app.name, '%s added %s %s' %
                                (user.link, c.item_name.lower(),
                                 record.link))
                return redirect_to(c.url)

    def save_button(self, key, *a, **data):
        
        c = self.collection

        user.authorize('update', c)

        if c.fields.validate(data):
            record = locate(c, key)
            if record:
                user.authorize('update', record)
                record.update(c.fields)
                record.pop('key', None)
                if record.key != key and locate(c, record.key):
                    error(duplicate_key_msg)
                else:
                    record.updated = now
                    record.updated_by = user.username

                    # convert property to data attribute
                    # so it gets stored as data
                    record.key = record.key

                    c.store.put(record)
                    logger.activity(system.app.name, '%s edited %s %s' %
                                    (user.link, c.item_name.lower(),
                                     record.link))
                    return redirect_to(record.url)

    def delete(self, key, CONFIRM='YES'):
        c = self.collection

        user.authorize('delete', c)

        if CONFIRM == 'NO':
            record = locate(c, key)
            if record:
                user.authorize('delete', record)
                c.store.delete(record)
                logger.activity(system.app.name, '%s deleted %s %s' %
                                (user.link, c.item_name.lower(),
                                 record.link))
                return redirect_to(c.url)

    def delete_image(self, key, name):
        record = self.collection.locate(key)
        if record:
            del record[name]
            self.collection.store.put(record)
            return redirect_to(url_for(record.url, 'edit'))


    def add_image(self, *a, **k):
        """upload and associate a dropzone image with a record"""
        # k contains FieldStorage object containing filename and data
        from StringIO import StringIO
        from utils import Record
        dummy = Record(
                filename='dummy.png',
                file=StringIO('test'),
            )

        # put the uploaded image data in a bucket
        path = os.path.join(system.site.data_path, 'buckets')
        bucket = Bucket(path)
        f = k.get('file', dummy)
        name = f.filename
        data = f.file.read()
        item_id = bucket.put(data)

        # create an attachment record for this bucket
        c = self.collection
        field_name = k.get('field_name', 'unknown')
        field_value = k.get('field_value', 'unknown')
        attachment = Attachment(
            record_kind=c.store.kind,
            field_name=field_name,
            field_value=field_value,
            attachment_id=item_id,
            attachment_size=len(data),
            attachment_name=name,
            )
        attachments = store(Attachment)
        attachments.put(attachment)

        return item_id

    def remove_image(self, *a, **k):
        """remove a dropzone image"""
        # k contains item_id and filename for file to be removed
        item_id = k.get('id', None)

        # detach the image from the record
        if item_id:
            attachments = store(Attachment)
            key = attachments.first(attachment_id=item_id)
            if key:
                attachments.delete(key)

            # delete the bucket
            path = os.path.join(system.site.data_path, 'buckets')
            bucket = Bucket(path)
            items = bucket.keys()
            if item_id in bucket.keys():
                bucket.delete(item_id)
                return 'ok'
            return 'empty'


class CollectionRecord(DefaultRecord):
    key = property(lambda self: id_for(self.name))
    url = property(lambda self: url_for_page(route[1], self.key)) # not ideal, but works
    link = property(lambda self: link_to(self.name, self.url))

    def allows(self, user, action):
        return True


class Collection(object):

    name_column = 'name'
    view = CollectionView
    controller = CollectionController
    storage = EntityStore

    def __init__(self, item_name, fields, entity, url=None):

        def calc_url():
            return url_for_page(id_for(self.name))

        def calc_columns(fields):
            return [
                (n == 0 and 'link' or f.name.lower())
                for n, f in enumerate(fields.as_list())
            ]

        self.item_name = item_name
        self.name = item_name + 's'
        self.fields = fields
        self.entity = entity
        self.labels = [f.label for f in fields.as_list()]
        self.columns = calc_columns(fields)
        self.store = self.storage(system.db, entity)
        self.url = url or calc_url()
        self.filter = None  # attach callable here to filter browse list

    def can_edit(self, user=user):
        # legacy - use user.can('action', object) instead
        return user.is_member(['managers'])

    def order(self, item):
        return item.name.lower()

    def locate(self, key):
        def scan(store, key):
            for rec in store:
                if rec.key == key or rec.href_id == key:
                    return rec
        return key.isdigit() and self.store.get(key) or self.store.first(key=key) or scan(self.store, key)

    def __call__(self, *a, **k):
        """ calling the collection - my_collection_instance()

            to use a collection as an app
        """
        controller = self.controller and self.controller(self) or CollectionController(self)
        view = self.view and self.view(self) or CollectionView(self)
        return controller(*a, **k) or view(*a, **k)

    def __str__(self):
        return 'collection of ' + str(self.store)

    def allows(self, user, action):

        def is_manager(user):
            return user.is_member('managers')

        actions = {
            'create': is_manager,
            'read': is_manager,
            'update': is_manager,
            'delete': is_manager,
        }

        if action not in actions:
            raise Exception('action missing: {}'.format(action))

        return actions.get(action)(user)
