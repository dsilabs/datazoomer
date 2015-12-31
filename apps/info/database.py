
from zoom import *

db = system.database

def rec_count(a):
    d = db('select count(*) from %s' % a.name)
    return d[0][0]

class TableRecord(Record):
    records = property(rec_count)

def view(table_name=None):

    if table_name:

        data = db('describe %s'%table_name)
        labels = ['Field','Type','Null','Key','Default','Extra']
        items = [(i.FIELD,i.TYPE,i.NULL,i.KEY,i.DEFAULT,i.EXTRA) for i in data]
        description = browse(items, labels=labels, title='Fields')

        data = db('show index in %s'%table_name)
        items = data
        indices = browse(items, title='Indices')

        content = description + indices

        return page(content, title=table_name.capitalize() + ' Table')

        
    else:
            
        def show_table(table_name):
            return link_to(table_name,'database/%s' % table_name)

        labels = 'Name', 'Records'

        data = [TableRecord(name=r[0]) for r in db('show tables')]

        content = browse(data, labels=labels, on_click='show', title='Tables')
        dbinfo = browse([
            ('Host', system.config.get('database','dbhost')),
            ('Database', system.config.get('database','dbname')),
            ('User', system.config.get('database','dbuser')),
            ('Host', db._Database__connection.get_host_info()),
            ('Server OS', db._Database__connection.get_server_info()),
        ],labels=['Property','Value'])
        return page('%s%s' % (dbinfo, content), title='Database')

