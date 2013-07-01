
from zoom import *

db = system.database

def view(id='', status=None):
    def error_link(id, status):
        if status in ['E','S','W']:
            new_route = route[1:] + [str(id)]
            return link_to(status, *new_route)
        return status

    if id:
        data = db('select * from log where id=%s and server=%s order by timestamp desc limit 100', id, request.server)
        if len(data) == 1:
            result = []
            for field in data[0].column_names():
                 result.append((field, '<pre>%s</pre>' % data[0].value_by_name(field)),)
            labels = ['Column', 'Value']
            return Page('<H1>Error Details</H1>%s' % browse(result, labels=labels))

    if status:
        data = db('select * from log where server=%s and status=%s order by timestamp desc limit 100',request.server,status)
    else:
        data = db('select * from log where server=%s order by timestamp desc limit 100',request.server)

    labels = ['ID','User','Address','Route','Status','Elapsed','Timestamp','How Long Ago']
    items = [(
        i.id,
        i.user,
        i.address,
        i.route,
        error_link(i.id, i.status),
        i.elapsed,
        i.timestamp,
        how_long_ago(i.timestamp),
        ) for i in data]
    content = browse(items,labels=labels)
    return page(content, title='System Log')
    
        
