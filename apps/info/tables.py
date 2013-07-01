
from zoom import *

db = system.database

def rec_count(a):
    d = db('select count(*) from %s' % a.name)
    return d[0][0]

class TableRecord(Record):
    records = property(rec_count)

def view(table_name=None):

    if table_name:
        def rec_count(table_name):
            d = db('select count(*) from %s' % table_name)
            return d[0][0]

        data = db('describe %s'%table_name)
        labels = ['Field','Type','Null','Key','Default','Extra']
        items = [(i.FIELD,i.TYPE,i.NULL,i.KEY,i.DEFAULT,i.EXTRA) for i in data]
        content = browse(items, labels=labels)
        return page('<H2>%s</H2>%s' % (table_name, content), title='Tables')

        
    else:
            
        def show_table(table_name):
            return link_to(table_name,'tables/%s' % table_name)

        labels = 'Name', 'Records'

        data = [TableRecord(name=r[0]) for r in db('show tables')]

        content = browse(data, labels=labels, on_click='show')
        dbinfo = browse([
            ('Host', system.config.get('database','dbhost')),
            ('Database', system.config.get('database','dbname')),
            ('User', system.config.get('database','dbuser')),
            ('Host', db._Database__connection.get_host_info()),
            ('Server OS', db._Database__connection.get_server_info()),
        ],labels=['Property','Value'])
        return page('%s<H2>Database</H2>%s' % (content,dbinfo), title='Tables')

