

from zoom import *

def is_manager(a):
    return user.is_member(['managers'])

def get_url(f):
    if len(route) == 1:
        return '/contacts/302/photo'
    else:
        return '/' + '/'.join(route[:3] + [f.name.lower()])

class MarkdownField(MemoField):
    def display_value(self):
        return markdown(self.value)
    
class ImageField(SimpleField):
    size = maxlength = 40
    _type = 'file'
    css_class = 'image_field'

    def display_value(self):
        url = self.url(self)
        return '<img src="%(url)s">' % locals()

    def edit(self):
        input = tag_for(
            'input', 
            name = self.name,
            id = self.id,
            size = self.size,
            maxlength=self.maxlength,
            Type = self._type,
            Class = self.css_class,
        )
        delete_link = '<a href="delete_%s">delete %s</a>' % (self.name.lower(), self.label.lower())
        if self.value:
            input += '<br>' + delete_link + ' <br>' + self.display_value()
        return layout_field( self.label, ''.join([input,self.render_msg(),self.render_hint()]) )

    def requires_multipart_form(self):
        return True

    def assign(self, value):
        try:
            try:
                self.value = value.value
            except AttributeError:
                self.value = value
        except AttributeError:
            self.value = None

    def evaluate(self):
        return self.value and {self.name: self.value} or {}

contact_fields = Fields(
        TextField('Name', required, maxlength=80),
        TextField('Title'),
        TwitterField('Twitter'),
        EmailField('Email'),
        TextField('Company'),
        URLField('Company URL'),
        PhoneField('Phone', hint='provided for convenience only'),
        TextField('City'),
        TextField('Province/State'),
        TextField('Country'),
        MarkdownField('Bio', hint='contact\'s short bio'),
        ImageField('Photo', url=get_url)
        )

class DefaultRecord(Record):
    def __getitem__(self, name):
        try:
            return Record.__getitem__(self, name)
        except KeyError:
            return ''

class ContactsContact(DefaultRecord):
    key = property(lambda self: id_for(self.name))
    url = property(lambda self: url_for_page(self.key))
    href_id = property(lambda a: id_for(a.name))
    href = property(lambda a: url_for_page(a.href_id))
    link = property(lambda self: link_to(self.name, self.url))
    linked_name = property(lambda self: is_manager(self.key) and self.link or self.name)
    title_line = property(lambda self: calc_title_line(self))
    mdbio = property(lambda self: markdown(self.bio).encode('utf-8'))

Contact = ContactsContact

class Collection:
    name_column = 'name'
    order = lambda t,a: a.name.lower()
    can_edit = is_manager

    @classmethod
    def locate(cls, key):
        def scan(store, key):
            for rec in store:
                if rec.key == key or rec.href_id == key:
                    return rec
        return key.isdigit() and cls.store.get(key) or cls.store.find(key=key) or scan(cls.store,key)

    @classmethod
    def match(cls, text):
        result = []
        t = text.lower()
        for rec in cls.store:
            if t in repr(rec.values()).lower():
                result.append(rec)
        return result

class ContactsCollection(Collection):
    name = 'Contacts'
    item_name = 'Contact'
    labels = 'name', 'title', 'photo'
    columns = 'linked_name', 'title', 'photo'
    entity = Contact
    store = store(Contact)
    url = url_for_app('contacts')
    fields = contact_fields

