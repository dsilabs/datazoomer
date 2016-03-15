"""
    entity storage (deprecated)
"""
# Copyright (c) 2005-2011 Dynamic Solutions Inc. (support@dynamic-solutions.com)
#
# This file is part of DataZoomer.
#
# DataZoomer is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DataZoomer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#  Simple Data Storage

import datetime
from system import system
from tools import db

from MySQLdb import IntegrityError

class ValidException(Exception): pass
class TypeException(Exception): pass

def create_storage():
    db("""
    create table if not exists storage_entities (
        id int not null auto_increment,
        kind      varchar(100),
        PRIMARY KEY (id)
        )
    """)
    db("""
    create table if not exists storage_values (
        id int not null auto_increment,
        kind      varchar(100),
        row_id    int not null,
        attribute varchar(100),
        datatype  varchar(30),
        value     text,
        PRIMARY KEY (id)
        )
    """)

def delete_storage():
    db('drop table if exists storage_values')
    db('drop table if exists storage_entities')

class EntityList(list):
    def __str__(self):
        if len(self)==0:
            return 'Empty list'
        title=['%s\n    id  '%self[0].kind()]
        lines =['------- ']
        fmtstr = ['%6d  ']
        fields = ['id']

        data_lengths = {}
        for rec in self:
            for field in self[0].attributes():
                n = data_lengths.get(field,0)
                m = len('%s'%rec.__dict__.get(field,''))
                if n < m:
                    data_lengths[field] = m

        fields = data_lengths.keys()
        d = data_lengths
        fields.sort(lambda a,b:not d[a] and -999 or not d[b] and -999 or d[a]-d[b])
        fields = ['id'] + fields

        for field in fields[1:]:
            width = max(len(field),d[field])+1
            fmt = '%-' + ('%ds ' % width)
            fmtstr.append(fmt)
            title.append(fmt % field)
            lines.append(('-' * width) + ' ')
        fmtstr.append('\n')
        lines.append('\n')
        title.append('\n')
        t = []
        fmtstr = ''.join(fmtstr)
        for rec in self:
            values = [rec.__dict__.get(key) for key in fields]
            t.append(''.join(fmtstr) % tuple(values))
        return ''.join(title) + ''.join(lines) + ''.join(t)


class Model(object):

    def __init__(self,parent=None,**kv):
        for k in kv:
            if k == '_id':
                setattr(self,'id',kv[k])
            elif k <> 'id':
                setattr(self,k.lower(),kv[k])

    def update(self,**kv):
        """Update existing attributes using passed key value pairs"""
        for update_key in kv:
            found = 0
            for key in self.__dict__:
                if key.lower() == update_key.lower():
                    self.__dict__[key] = kv[update_key]
                    found = 1
            if not found:
                self.__dict__[update_key] = kv[update_key]

    @classmethod
    def kind(cls):
        """Returns the model/entity type
        """
        n = []
        for c in cls.__name__:
            if c.isalpha() or c=='_':
                if c.isupper() and len(n):
                    n.append('_')
                n.append(c.lower())
        return ''.join(n)

    def put(self):
        def fixval(d):
            if type(d) == datetime.datetime:
                # avoids mysqldb reliance on strftime that lacks support for dates before 1900
                return "%02d-%02d-%02d %02d:%02d:%02d" % (d.year,d.month,d.day,d.hour,d.minute,d.second)
            else:
                return d                
    
        if not self.valid():
            return 0

        keys        = [i for i in self.__dict__.keys() if i<>'id']
        values      = [self.__dict__[i] for i in keys]
        datatypes   = [repr(type(i)).strip("<type >").strip("'") for i in values]
        values      = [fixval(i) for i in values] # same fix as above
        valid_types = ['str','unicode','long','int','float','datetime.date','datetime.datetime','bool','NoneType']

        for atype in datatypes:
            if atype not in valid_types:
                raise TypeException,'unsupported type <type %s>' % atype

        if hasattr(self,'id') and self.exists(self.id):
            db('delete from storage_values where row_id=%s',self.id)
        else:
            db('insert into storage_entities (kind) values (%s)',self.kind())
            self.id = db.lastrowid

        keys = [key.lower() for key in keys] # store attribute names as lower case
        param_list = zip([self.kind()]*len(keys),[self.id]*len(keys),keys,datatypes,values)

        cmd = 'insert into storage_values (kind,row_id,attribute,datatype,value) values (%s,%s,%s,%s,%s)'
        db.cursor().executemany(cmd,param_list)

        return self.id

    def key(self):
        return self.id

    def delete(self):
        cmd = 'delete from storage_values where row_id=%s'
        db(cmd,self.id)

    @classmethod
    def exists(cls,keys=None):
        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
        slots = (','.join(['%s']*len(keys)))
        cmd = 'select * from storage_entities where id in (%s)' % slots
        rs = db(cmd,*keys)

        found_keys = [rec.ID for rec in rs]
        if len(keys)>1:
            result = [(key in found_keys) for key in keys]
        else:
            result = keys[0] in found_keys
        return result

    @classmethod
    def get(cls,keys):
        if keys == None: return None
        if not isinstance(keys, (list, tuple)):
            keys = (keys,)
            as_list = 0
        else:
            as_list = 1
        keys = [long(key) for key in keys]

        if not keys:
            if as_list:
                return []
            else:
                return None

        cmd = 'select * from storage_values where kind=%s and row_id in (%s)' % ('%s',','.join(['%s']*len(keys)))
        entities = {}
        rs = db(cmd,cls.kind(),*keys)

        for rec in rs:
            row_id = rec.ROW_ID
            attribute = rec.ATTRIBUTE.lower()
            if rec.DATATYPE == "str":
                value = rec.VALUE
            elif rec.DATATYPE == 'unicode':
                value = rec.VALUE                
            elif rec.DATATYPE == "long":
                value = long(rec.VALUE)
            elif rec.DATATYPE == "int":
                value = int(rec.VALUE)
            elif rec.DATATYPE == 'float':
                value = float(rec.VALUE)
            elif rec.DATATYPE == "datetime.date":
                y = int(rec.VALUE[:4])
                m = int(rec.VALUE[5:7])
                d = int(rec.VALUE[8:10])
                import datetime
                value = datetime.date(y,m,d)
            elif rec.DATATYPE == "datetime.datetime":
                y = int(rec.VALUE[:4])
                m = int(rec.VALUE[5:7])
                d = int(rec.VALUE[8:10])
                hr = int(rec.VALUE[11:13])
                mn = int(rec.VALUE[14:16])
                sc = int(rec.VALUE[17:19])
                import datetime
                value = datetime.datetime(y,m,d,hr,mn,sc)
            elif rec.DATATYPE == 'bool':
                value = (rec.VALUE == '1' or rec.VALUE == 'True')
            elif rec.DATATYPE == 'NoneType':
                value = None
            elif rec.DATATYPE == 'instance':
#                print 'dzstore:','(id=%s name="%s" type=%s value=%s)'%(rec.id,attribute,repr(rec.DATATYPE),repr(rec.VALUE))
                value = long(rec.id)
            else:
                print 'dzstore:',rec.DATATYPE,'not supported (name="%s" type=%s value=%s id=%s)'%(attribute,repr(rec.DATATYPE),repr(rec.VALUE),rec.id)
                value = rec.VALUE
            entities.setdefault(row_id,cls(_id=row_id)).__dict__[attribute] = value

        if len(keys)>1:
            result = EntityList()
            for id in keys: result.append(entities.get(id))
#            result = [entities.get(id) for id in keys]
        else:
            if as_list:
                result = EntityList()
                result.append(entities.get(keys[0]))
            else:
                result = entities.get(keys[0])


        return result

    @classmethod
    def all(cls,limit=1000):
        cmd = 'select distinct row_id from storage_values where kind="%s" limit %s' % (cls.kind(),limit)
        rs = db(cmd)
        keys = [rec.ROW_ID for rec in rs]
        return cls.get(keys) or EntityList()

    @classmethod
    def zap(cls):
        cmd = 'delete from storage_values where kind=%s'
        db(cmd,cls.kind())
        cmd = 'delete from storage_entities where kind=%s'
        db(cmd,cls.kind())

    @classmethod
    def len(cls):
        cmd = 'select count(*) n from storage_entities where kind=%s'
        return db(cmd,cls.kind())[0].N

    @classmethod
    def find(cls,limit=1000,**kv):
        all_keys = []
        for field_name in kv.keys():
            value = kv[field_name]
            if not isinstance(value, (list, tuple)):
                wc = 'value=%s'
                v = (value,)
            else:
                wc = 'value in ('+','.join(['%s']*len(value))+')'
                v = value
            cmd = 'select distinct row_id from storage_values where kind=%s and attribute=%s and '+wc+' limit %s' % limit
            rs = db(cmd,cls.kind(),field_name.lower(),*v)
            all_keys.append([rec.ROW_ID for rec in rs])
        answer = set(all_keys[0])
        for keys in all_keys[1:]:
            answer = set(keys) & answer
        if answer:
            return cls.get(list(answer))
        else:
            return []

    @classmethod
    def attributes(cls):
        cmd = 'select distinct attribute from storage_values where kind=%s order by id desc'
        rs = db(cmd,cls.kind())
        values = [rec.ATTRIBUTE for rec in rs]
        return values

    def valid(self):
        return 1

    def __repr__(self):
        promt_len = 15
        return '\n'.join(['%s%s: %s' % (item[:promt_len], '.'*(promt_len-len(item)), self.__dict__[item]) for item in self.__dict__.keys()])

    def __getattr__(self,name):
        """Provide access to attributes, proxied attributes and calculated attributes"""
#        if name in self.__dict__:
#            return self.__dict__.get(name)
        if name.lower() in self.__dict__:
            return self.__dict__.get(name.lower())
#        elif hasattr(self.__class__,name):
#            return getattr(self.__class__,name)
        elif hasattr(self.__class__,name.lower()):
            return getattr(self.__class__,name.lower())
        elif hasattr(self.__class__,'get_'+name):
            method = getattr(self.__class__,'get_'+name)
            return method(self)
        else:
            raise AttributeError, name

    def __getitem__(self,key):
        return getattr(self,key)

