"""

    simple collection example

"""
from zoom import *
import zoom.collect

# define a model (pick an app specifc name and a nickname)
class SampleContact(zoom.collect.CollectionRecord): pass # the app specific part
Contact = SampleContact # the nickname

# define the fields (always include a name field)
contact_fields = Fields(
    TextField('Name', required, maxlength=80),
    TextField('Title'),
    DateField('Date', format='%A %b %d, %Y'),
    EditField('Notes'),
)

# create the app
app = zoom.collect.Collection(
    'Contact',
    contact_fields,
    Contact,
    url='/sample/collection'
)
