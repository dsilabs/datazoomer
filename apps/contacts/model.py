
from zoom import *

def is_manager(a):
    return user.is_member(['managers'])

class MarkdownField(MemoField):
    def display_value(self):
        return markdown(self.value)
    
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
        ImageField('Photo')
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
    photo_img = property(lambda a: '<img alt="%s" src="%s">' % (a.name,a.photo and (a.url+'/image?name=photo') or '/static/images/no_photo.png'))

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
    columns = 'linked_name', 'title', 'photo_img'
    entity = Contact
    store = store(Contact)
    url = url_for_app('contacts')
    fields = contact_fields

