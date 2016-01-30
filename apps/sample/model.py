
from zoom import *
from zoom.collect import *
from zoom.buckets import Bucket

# Useful classes and functions
#--------------------------------------------------------------


# Types and Constants - place types and constants here
#--------------------------------------------------------------


# Fields - place custom fields here
#--------------------------------------------------------------


# Validators - place custom validators here
#--------------------------------------------------------------


# Models - every collection needs a model, they go here
#--------------------------------------------------------------

class ContactsContact(CollectionRecord): pass
class ContactsItem(CollectionRecord): pass

Contact = ContactsContact
Item = ContactsItem


# Fields - every collection needs fields, they go here
#--------------------------------------------------------------

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
        ImagesField('Photo')
        )

item_fields = Fields(
        TextField('Name', required, maxlength=80),
        MemoField('Description'),
        #CurrencyField('Cost'),
        #CurrencyField('Price'),
        NumberField('Inventory'),
        )


# Collections
#--------------------------------------------------------------

class ItemCollection(Collection):
    def __init__(self, *a, **k):
        Collection.__init__(self, *a, **k)
        self.url = '/{}/page-of-stuff'.format(system.app.name)


