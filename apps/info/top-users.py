
from zoom import *

db = system.database

def view():
    data = db('select user, max(timestamp) dt, count(*) as cnt from log where server=%s group by user order by cnt desc', request.server)
    labels = 'User', 'Page Count', 'Last Seen'
    items = [(i.user, i.cnt, how_long_ago(i.dt)) for i in data]
    content = browse(items, labels=labels)
    return page(content, title='Top Users')

