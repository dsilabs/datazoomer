
from zoom import *

db = system.database

def view(id='', status=None):
    if id:
        data = db('select * from log where id=%s and server=%s order by timestamp desc limit 100', id, request.server)
        if len(data) == 1:
            result = []
            for field in data[0].column_names():
                 result.append((field, '<pre>%s</pre>' % websafe(data[0].value_by_name(field))),)
            labels = ['Column', 'Value']
            return Page('<H1>Errors</H1>%s' % browse(result, labels=labels))

    if status:
        data = db('select * from log where server=%s and status=%s order by timestamp desc limit 100',request.server,status)
    else:
        data = db('select * from log where server=%s and status="E" order by timestamp desc limit 100',request.server)

    labels = ['ID','User','Address','Route','Status','Elapsed','How Long Ago','Message']
    items = [(
        link_to(i.id, route[-1], i.id),
        i.user,
        i.address,
        websafe(i.route),
        i.status,
        i.elapsed,
        '<span title="%s">%s</span>' % (i.timestamp, how_long_ago(i.timestamp)),
        websafe(i.message[:30]),
        ) for i in data]
    content = browse(items,labels=labels)
    return page(content, title='Errors')
    
        
