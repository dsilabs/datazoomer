
from zoom import *

def view():
    db = system.database

    data = db('select address, max(timestamp) dt, count(*) as cnt from log where server=%s group by address order by cnt desc', request.server)
    labels = 'Address', 'Page Count', 'Last Seen'
    items = [(i.address,i.cnt,how_long_ago(i.dt)) for i in data]
    content = browse(items, labels=labels)
    return page(content, title='Addresses')
    
    
