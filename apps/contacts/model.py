
from zoom import *
from zoom.collect import Collection, CollectionRecord

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

class ContactsContact(CollectionRecord):
    url = property(lambda self: url_for_page(self.key))
    href_id = property(lambda a: id_for(a.name))
    href = property(lambda a: url_for_page(a.href_id))
    title_line = property(lambda self: calc_title_line(self))
    mdbio = property(lambda self: markdown(self.bio).encode('utf-8'))
    photo_img = property(lambda a: '<img alt="%s" src="%s">' % (a.name,a.photo and (a.url+'/image?name=photo') or '/static/dz/images/no_photo.png'))

Contact = ContactsContact

class ContactsCollection(Collection):
    def __init__(self):
        Collection.__init__(self, 'Contact', contact_fields, Contact)
        self.labels = 'name', 'title', 'photo'
        self.columns = 'link', 'title', 'photo_img'
        self.url = url_for_app('contacts')
