"""
Database

NOTES:
Allows a block of data to be read using a layout that makes it act like
it has columns.

Some of this code is based on the Lazy DB code by John B. Dell'Aquila found
in the Python Cookbook.

TODO:
1.  Use fetchmany() instead of fetchall()

"""

__all__ = ['Database', 'Table', 'Columns', 'Column']

import string
import decimal
import time
import datetime
import warnings

warnings.filterwarnings('ignore','Unknown table.*')
norm = string.maketrans('','')
nonprintable = string.translate(norm,norm,string.letters+string.punctuation+string.digits+' ')

#===========================================================
class Column:
    def __init__(self,name,type,size=0,precision=0,position=0,rawtype=None):
        self.name      = name
        self.type      = type
        self.size      = size
        self.precision = precision
        self.position  = position
        self.rawtype   = rawtype
        self.label     = name.capitalize()
        self.maxlength = size
        self.visible   = 1
        self.readOnly  = 0
        self.select    = None
        self.default   = None

    def __repr__(self):
        type = self.type
        if type in ['NUMERIC','FLOAT','CURRENCY']:
            t = '%-3s %-15s %s(%d,%d)' % (self.position,self.name,self.type,self.size,self.precision)
        elif type == 'CHAR':
            t = '%-3s %-15s %s(%d)' % (self.position,self.name,self.type,self.size)
        else:
            t = '%-3s %-15s %s' % (self.position,self.name,self.type)
        return t

    def valid(self,value):
        if self.type == 'DATE':
           try:
               date = str.split(value,'-')
               newdate = datetime.datetime(int(date[0]),int(date[1]),int(date[2]))
               return (1,newdate,'ok')
           except:
               return (0,value,'Invalid Date')
        elif self.type=="NUMERIC":
           try:
               num = int(value)
               return (1,value,'ok')
           except:
               try:
                   num = float(value)
                   return (1,value,'ok')
               except:
                   return  (0,value,'Invalid Numeric Format')
        else:
            return (1,value,"ok")

class Columns(list):
    def __init__(self,cols=None):
        if cols:
            for col in cols:
                self.append(col)

    def drop(self,names=[]):
        if names:
            return Columns([column for column in self if not column.name in names])
        else:
            return Columns([column for column in self])

    def keep(self,names=[]):
        if names:
            return Columns([column for column in self if column.name in names])
        else:
            return Columns([column for column in self])

    def names(self,drop=[]):
        return [column.name for column in self if not (column.name[0]=='_' or column.name in drop)]

    def column(self,name):
        for column in self:
            if column.name == name:
                return column
        return None

    def __str__(self):
        names = ['name','type','size','precision','position','rawtype']
        fmtstr = []
        title = []
        lines = []
        for name in names:
            width = len(name)
            for column in self:
                width = max(width,len(str(column.__dict__[name])))
            fmt = '%-' + ('%ds ' % width)
            fmtstr.append(fmt)
            title.append(fmt % name)
            lines.append(('-' * width) + ' ')
        fmtstr.append( '\n')
        lines.append('\n')
        title.append('\n')
        t = []
        for column in self:
            t.append(''.join(fmtstr) % (column.name,column.type,column.size,column.precision,column.position,column.rawtype))
        return ''.join(title) + ''.join(lines) + ''.join(t)

#===========================================================
class Database:
    """Lazy proxy for database connection"""

    def __init__(self, factory, *args, **keywords):
        """Initialize with factory method to generate DB connection
        (e.g. odbc.odbc, cx_Oracle.connect) plus any positional and/or
        keyword arguments required when factory is called."""
        self.__connection = None
        self.__factory = factory
        self.__args = args
        self.__keywords = keywords
        self.__ptype = {
                0:'NUMERIC',
                2:'NUMERIC',
                3:'NUMERIC',
                5:'NUMERIC',
                7:'CHAR',
                8:'NUMERIC',
                10:'DATE',
                12:'DATE',
                246:'DECIMAL',
                252:'TEXT',
                253:'CHAR',
                254:'CHAR',
                }
        self.debug = 0

    def __getattr__(self, name):
        if self.__connection is None:
            self.__connection = self.__factory(*self.__args, **self.__keywords)
        return getattr(self.__connection, name)

    def query(self,sql,args=None):
        return Query(self,sql,args)

    def table(self,name,indexname=None):
        return Table(self,name,indexname)

    def temporary_table(self,name=None,indexname=None):
        return Cursor(self,name,indexname)

    def row_count(self,dataset):
        return dataset.cursor.rowcount

    def close(self):
        if self.__connection:
            self.__connection.close()
            self.__connection = None

    def __call__(self, sql, *args, **keywords):
        """Run a SQL statement.  If the command generates a data result
        the return value will be a dataset, otherwise it will be the
        cursor return value (whatever that is!)."""
        cursor = self.cursor()

        if self.debug:
            start = time.time()
        try:
            result = cursor.execute(sql, args)
        finally:
            if self.debug:
                print 'SQL (%s): %s - %s<br>\n' % (time.time()-start, sql, args)

        if cursor.description:
            return RecordSet(self, cursor)
        else:
            self.lastrowid = cursor.lastrowid
            return result

    def execute(self, sql, params=None):
        """Execute sql query and return results. Optional keyword
        args are '%' substituted into query beforehand."""
        if self.debug:
            print 'SQL: ', sql, 'Params:', params
        cursor = self.cursor()
        result = cursor.execute(sql,params)
        self.lastrowid = cursor.lastrowid # In case it was an insert
        return result

    def column_definition(self, col):
        if col.type == 'CHAR':
            return '%s CHAR(%s)' % (col.name,col.size)
        elif col.type == 'TEXT':
            return '%s TEXT' % (col.name)
        elif col.type == 'DECIMAL':
            return '%s DECIMAL(%s,%s)' % (col.name,col.size,col.precision)
        elif col.type == 'NUMERIC':
            return '%s NUMERIC(%s,%s)' % (col.name,col.size,col.precision)
        elif col.type == 'DATE':
            return '%s DATE' % (col.name)
        else:
            raise 'Unknown type ' + col

    def value_expression(self, col, value):
        def sstr(text):
            t = text.translate(norm,nonprintable)
            t = t.replace('%','%%')
            return "%s" % t
        if col.type in ['CHAR','TEXT']:
            return sstr('%s' % value)
        elif col.type == 'NUMERIC' or col.type == 'DECIMAL':
            return str(value)
        elif col.type == 'DATE':
            return value
            if isinstance(value,str):
                return "'"+value+"'"
            else:
                return value.strftime("'%Y-%m-%d'")
        else:
            raise 'Unknown type ' + repr(col)

    def value_list(self, columns, values):
        cols = columns.keep(values.keys())
        t = [self.value_expression(col,values[col.name]) for col in columns if col.name in values]
        return t

    def insert_record(self, tablename, columns, values):
        """Inserts values from a dictionary into a table"""
        columns_specified = columns.keep(values.keys())
        names = ','.join(columns_specified.names())
        vals  = self.value_list(columns_specified,values)
        places = ','.join(['%s'] * len(vals))
        cmd = 'insert into %s (%s) values (%s)' % (tablename, names, places)
        self.execute(cmd,vals)
        return self.lastrowid

    def update_record(self, tablename, indexname, columns, values):
        columns_specified = columns.keep(values.keys()).drop(indexname)
        names_list = columns_specified.names()
        values_list = self.value_list(columns_specified,values)
        places_list = ['%s'] * len(values_list)
        assignments = ','.join(['%s=%s' % (k,v) for (k,v) in zip(names_list,places_list)])
        key = values[indexname]
        cmd = 'update %s set %s where %s=%s' % (tablename,assignments,indexname,'%s')
        args = values_list + [key]
        self.execute(cmd,args)
        return 1

    def create_table(self, name, columns):
        struct = [self.column_definition(col) for col in columns]
        return self('CREATE TABLE %s ( %s )' % (name,', '.join(struct)))

    def create_temporary_table(self, name, columns):
        struct = [self.column_definition(col) for col in columns]
        return self('CREATE TEMPORARY TABLE %s ( %s )' % (name,', '.join(struct)))

    def drop_table(self, name):
        return self('DROP TABLE IF EXISTS %s' % name)

    def table_names(self):
        return [rec[0] for rec in self.query('show tables')]

    def create_columns(self, description):  # May have to override this method for other database types
        ptype = self.__ptype 

        columns  = Columns()
        pos = 0
        for item in description:
            name    = item[0].upper()
            rawtype = item[1]
            maxw    = item[2]
            size    = item[4] - item[5]
            prec    = item[5]

            try:
                newtype = ptype[rawtype]
            except:
                raise 'Error converting type %s in column %s' % (rawtype,name)

            if newtype == 'CHAR':
                if item[3]==0:
                    newtype = 'MEMO'
                else:
                    size = item[3]
                precision = 0

            elif rawtype==5:
                size = item[4]

            if newtype == 'MEMO':
                size = 0

            columns.append( Column(name,newtype,size,prec,pos,rawtype) )
            pos += 1

        return columns


class RecordSet:
    """Wrapper for table based"""

    def __init__(self,db,cursor):
        self.db = db
        self.cursor = cursor
        self.rowcount = cursor.rowcount
        self.reset()

    def reset(self):
        self.columns = self.db.create_columns(self.cursor.description)
        self.columnMap = {}
        for name,n in zip(self.columns.names(), xrange(10000)):
            self.columnMap[name] = n
        self.data    = [list(x) for x in self.cursor.fetchall()]

    def __getitem__(self, n):
        return Record(self,self.data[n])

    def __len__(self):
        return int(self.rowcount)

    def __str__(self):
        title=[]
        lines =[]
        fmtstr = []
        for field in self.cursor.description:
            width = max(field[2],len(field[0]))+1
            fmt = '%-' + ('%ds ' % width)
            fmtstr.append(fmt)
            title.append(fmt % field[0])
            lines.append(('-' * width) + ' ')
        fmtstr.append('\n')
        lines.append('\n')
        title.append('\n')
        t = []
        for rec in self.data:
            t.append(''.join(fmtstr) % tuple(rec))
        return ''.join(title) + ''.join(lines) + ''.join(t)

class Query(RecordSet):
    def __init__(self,db,sql,args=None):
        self.sql     = sql
        self.args    = args
        self.cursor  = db.cursor()
        RecordSet.__init__(self,db,self.cursor)
    def reset(self):
        try:
            self.cursor.execute(self.sql,self.args)
            self.rowcount = self.cursor.rowcount
        except:
            raise 'SQL Error: %s' % self.sql
        RecordSet.reset(self)

class Table(Query):
    def __init__(self, db, tablename, indexname=''):
        self.tablename = tablename
        self.indexname = indexname
        self.pointer   = -1
        self.lastrowid = 0

        sql       = 'SELECT * FROM %s' % tablename
        Query.__init__(self,db,sql)

    def valid_record(self, data):
        errors = {}
        return errors

    def new_record(self):
        n=[]
        for item in self.columns.names():
            n = n + [""]
        return Record(self, n)

    def reset(self):
        Query.reset(self)
        self.pointer -1

    def get_record(self):
        self.pointer = self.pointer + 1
        try:
            return self.__getitem__(self.pointer)
        except:
            return None

    def insert(self,rec):
        return self.insert_record(rec)

    def insert_record(self,rec):
        recdict = {}
        if isinstance(rec,Record):
            for item in rec._column_names_:
                if rec._data_[rec._map_[item]]!=None:
                    recdict[item] = rec._data_[rec._map_[item]]
        elif isinstance(rec,dict):
            recdict = rec
        else:
            recdict = rec.__dict__

        self.db.insert_record(self.tablename,self.columns,recdict)
        self.lastrowid = self.db.lastrowid
        return self.lastrowid

    def delete(self,key):
        cmd = "delete from %s where %s=%s" % (self.tablename,self.indexname,'%s')
        self.db(cmd,key)

    def update_record(self,rec):
        recdict = {}
        if isinstance(rec,Record):
          for item in rec._column_names_:
              if rec._data_[rec._map_[item]]!=None:
                 recdict[item] = rec._data_[rec._map_[item]]
        elif isinstance(rec,dict):
            recdict = rec
        else:
            recdict = rec.__dict__
        self.db.update_record(self.tablename,self.indexname,self.columns,recdict)

    def update(self,rec):
        return self.update_record(rec)

    def seek(self,key):
        cmd = 'select * from %s where %s=%s' % (self.tablename,self.indexname,'%s')
        result = self.db(cmd,key)
        if result:
            return result[0]
        else:
            return None

    def locate(self,**keywords):
        where_clause_fields = []
        where_clause_values = []
        for key in keywords:
            where_clause_fields.append(key)
            where_clause_values.append(keywords[key])

        cmd = 'select * from %s where %s' % (self.tablename,' AND '.join(['%s=%s' % (field,'%s') for field in where_clause_fields]))
        return self.db(cmd,*where_clause_values)

class Cursor(Table):

    def __init__(self,db,name=None,indexname=None):
        def random_name():
            import random
            return "t"+str(int(random.random()*1000000000))
        self.created = 0
        if name==None:
           self.temporary = 1
           tablename = random_name()
        else:
           self.temporary = 0
           tablename = name
        Table.__init__(self,db,tablename,indexname)

    def reset(self):
        if self.created:
            Query.reset(self)
        self.pointer -1

    def insert_record(self,rec):
          def create_columns(rec):
                 if type(rec)!=type({}):
                    newrec = {}
                    for item in rec.__dict__['_column_names_']:
                        newrec[item] = rec.__dict__['_data_'][rec.__dict__['_map_'][item]]
                    rec = newrec
                 size=0
                 prec=0
                 ntype=''
                 columns = Columns()
                 pos = 0
                 for item in rec:
                     name = item
                     if type(rec[item])==type("") and len(rec[item])<300:
                        ntype = 'CHAR'
                        size = len(rec[item])
                     elif type(rec[item])==type(""):
                        ntype = 'MEMO'
                     elif type(rec[item])==type(1):
                        ntype = 'NUMERIC'
                        size = len(str(rec[item]))
                     elif type(rec[item])==type(1.0):
                        ntype = 'NUMERIC'
                        size = len(str(rec[item]))
                        prec = len(str.split(str(rec[item]),'.')[0])
                     elif type(rec[item])==type(decimal.Decimal(1)):
                        ntype = 'DECIMAL'
                        size = len(str(rec[item]))
                        prec = len(str.split(str(rec[item]),'.')[0])
                     elif type(rec[item])==type(datetime.datetime(1,1,1)) or \
                          type(rec[item])==type(date(1,1,1)):
                        ntype = 'DATE'
                     columns.append( Column(name,ntype,size,prec,pos) )
                     pos += 1
                 return columns

          if self.created == 0:
             columns = create_columns(rec)
             if self.temporary==1:
                self.db.create_temporary_table(self.tablename,columns)
             else:
                self.db.create_table(self.tablename,columns)
             self.created=1
             self.reset()
          Table.insert_record(self,rec)

class Record:
    """Wrapper for data row. Provides access by
    column name as well as position."""

    def __init__(self, recordset, rowData):
        class RecordData:
            def __init__(self,rs,rowData):
                self.rs      = rs
                self.data    = rowData
                self.columns = rs.columns
            def __getitem__(self,n):
                if type(n) == type(''):
                    n = self.rs.columnMap[n]
                if self.columns[n].type == 'DECIMAL' and self.data[n]:
                    return decimal.Decimal(self.data[n])
                else:
                    return self.data[n]
            def __setitem__(self,n,value):
                self.data[n] = value

        self.__dict__['_data_']         = RecordData(recordset,rowData)
        self.__dict__['_columns_']      = recordset.columns
        self.__dict__['_map_']          = recordset.columnMap
        self.__dict__['_column_names_'] = recordset.columns.names()

    def __getattr__(self, name):
         return self._data_[self._map_[name.upper()]]

    def __eq__(self,rec):
        if rec==None:
           return 0
        if self.__dict__['_data_'] == rec.__dict__['_data_'] and  \
           self.__dict__['_map_'] == rec.__dict__['_map_'] and  \
           self.__dict__['_column_names_'] == rec.__dict__['_column_names_'] :
            return 1
        else:
            return 0

    def __ne__(self,rec):
        return not self.__eq__(rec)

    def __setattr__(self, name, value):
        try:
            n = self._map_[name]
        except KeyError:
            self.__dict__[name] = value
        else:
            self._data_[n] = value

    def __getitem__(self, n):
        return self._data_[n]

    def __setitem__(self, n, value):
        self._data_[n] = value

    def __getslice__(self, i, j):
        return self._data_[i:j]

    def __setslice__(self, i, j, slice):
        self._data_[i:j] = slice

    def __len__(self):
        return len(self._data_)

    def __iter__(self):
        for name in self._columns_:
            yield (name,self._data_[self._map_[name]])

    def __str__(self):
        t = [ (name,self._data_[self._map_[name]])  for name in self._column_names_ ]
        return '%s: %s' % (self.__class__, t)

    def column_names(self):
        return [name for name in self._column_names_]

    def keys(self):
        return self.column_names()

    def value_by_name(self,name):
        return self._data_[self._map_[name]]

    def columns(self):
        return self.__dict__['_columns_']

    def as_dict(self):
        t = {}
        for name in self.column_names():
            t[name] = self.value_by_name(name)
        return t

    def as_obj(self):
        class obj: pass
        instance = obj()
        instance.__dict__ = self.as_dict()
        return instance

    def __nonzero__(self):
        return 1

def test_database():
    import MySQLdb
    return Database(MySQLdb.Connect,host='localhost',user='testuser',passwd='password',db='test')


