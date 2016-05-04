"""

    simple collection example

"""
from zoom import *
import zoom.collect

# define a model (pick an app specifc name and a nickname)
class SampleContact(zoom.collect.CollectionRecord): pass # the app specific part
Contact = SampleContact # the nickname

statuses = [
    ('New', 'N'),
    ('Open', 'O'),
    ('Pending', 'P'),
    ('Closed', 'C'),
]

# define the fields (always include a name field)
contact_fields = Fields(
    TextField('Name', required, maxlength=80),
    TextField('Title', required, MinimumLength(3)),
    DateField('Date', format='%A %b %d, %Y'),
    RadioField('Status', values=statuses),
    EditField('Notes'),
)

# create the app
app = zoom.collect.Collection(
    'Contact',
    contact_fields,
    Contact,
    url='/sample/collection'
)
