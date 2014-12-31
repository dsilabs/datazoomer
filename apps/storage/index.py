

from zoom import *

index_query = "select distinct kind from storage_entities union select distinct kind from entities"


class IndexView(View):

    def index(self,**k):
        entities = '<br>'.join([link_to(rec.kind,rec.kind,'browse') for rec in db(index_query)])
        return Page('<H1>Storage</H1><H3>Entities</H3><br>%s' % entities)
        
    def show(self, name):
        system.app.menu = (('index','Entities',''), ('show','Browse Data',name+'/browse'))
        labels = ['Attribute','Frequecy','Drop']
        items = db('select distinct attribute, count(*) as count from attributes where kind=%s group by 1 order by count, attribute',name)
        if not items:
            items = db('select distinct attribute, count(*) as count from storage_values where kind=%s group by 1 order by count, attribute',name)
        table = browse([(item.attribute,item.count,link_to('drop',name,'drop',item=item.attribute)) for item in items],attribute=name,labels=labels)
        return page(table, title=name)

    def browse(self, name):
        class UniModel(Model):
            _kind = name
            @classmethod
            def kind(cls):
                return cls._kind
            def keys(cls):
                return cls.attributes()

        system.app.menu = (('index','Entities',''), ('show','Attributes',name))
        items = UniModel.all()
        if not items:
            s = store(dict)
            s.kind = name
            items = s.all()

            for item in items:
                item['actions'] = '<a href="%s/delete">delete</a>' % item['_id']

        if len(items) == 1:
            footer_name = 'record'
        else:
            footer_name = 'records'
        footer = '%s %s' % (len(items), footer_name)

        a = db('select distinct attribute, count(*) as count from attributes where kind=%s group by 1 order by count, attribute',name)
        if not a:
            a = db('select distinct attribute, count(*) as count from storage_values where kind=%s group by 1 order by count, attribute',name)
        attributes = [i.attribute for i in a] + ['actions']

        return page(browse(items, columns=attributes, footer=footer), title='Entity: '+name)

    def drop(self,name,item):
        db('delete from storage_values where kind=%s and attribute=%s',name,item)
        db('delete from attributes where kind=%s and attribute=%s',name,item)
        return redirect_to('/storage/'+name)
        
class IndexController(Controller):

    def delete(self, name, key):

        class UniModel(Model):
            _kind = name
            @classmethod
            def kind(cls):
                return cls._kind
            def keys(cls):
                return cls.attributes()
        rec = UniModel.get(int(key))
        if not rec:
            s = store(dict)
            s.kind = name
            rec = s.get(key)
            if rec:
                s.delete(rec)
                if not s.get(key):
                    message('deleted %r' % key)
                else:
                    message('unable to delete %r' % key)
            else:
                message('unable to find %r' % key)
        else:
            message('delete not implemented for legacy models')
        return home('%s/browse' % name)


view = IndexView()
controller = IndexController()


