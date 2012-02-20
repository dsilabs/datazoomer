

from zoom.database import *

def test_database():
    import MySQLdb
    return Database(MySQLdb.Connect,host='localhost',user='testuser',passwd='password',db='test')

import unittest

from datetime import date, time, datetime

class DBTest(unittest.TestCase):
    def test_Column(self):
        col = Column('ID','CHAR',15,0,2)
        self.assertEquals(col.position,2)
        self.assertEquals(col.name,'ID')
        self.assertEquals(col.type,'CHAR')
        self.assertEquals(col.size,15)
        self.assertEquals(col.precision,0)
        col = Column('ID','DATE')

    def test_Columns(self):
        cols = Columns([Column('ID','CHAR',15),Column('Number','NUMERIC',15,1),Column('Comm','TEXT')])
        self.assertEquals(cols.names(),['ID','Number','Comm'])
        cols = cols.drop(['ID'])
        self.assertEquals(cols.names(),['Number','Comm'])
        cols.append(Column('ID','CHAR',15))
        cols = cols.keep(['ID'])
        self.assertEquals(cols.names(),['ID'])

    def test_RecordSet(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        db('insert into dzdb_test_table values ("1234",50,"2005-01-14","Hello there")')
        db('insert into dzdb_test_table values ("5678",60,"2035-01-24","New notes")')
        recordset = db('select * from dzdb_test_table')
        self.assertEquals(recordset[0][0],'1234')
        self.assertEquals(recordset[1][3],'New notes')
        recordset[1][3]='Changed again'
        self.assertEquals(recordset[1][3],'Changed again')
        self.assertEquals(len(recordset),2)
        db('drop table dzdb_test_table')
        #Need Get and Set Slice test

    #def test_qlookup(self):
    #    db = test_database()
    #    db('drop table if exists dzdb_test_table')
    #    db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
    #    db('insert into dzdb_test_table values ("1234",50,"2005-01-14","Hello there")')
    #    db('insert into dzdb_test_table values ("5678",60,"2035-01-24","New notes")')
    #    dict = qlookup(db,'select * from dzdb_test_table','ID','AMOUNT')
    #    self.assert_(dict.has_key('1234') and dict.has_key('5678'))
    #    self.assert_(dict['1234']==50 and dict['5678']==60)
    #    db('drop table dzdb_test_table')

    #def test_qlist(self):
    #    db = test_database()
    #    db('drop table if exists dzdb_test_table')
    #    db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
    #    db('insert into dzdb_test_table values ("1234",50,"2005-01-14","Hello there")')
    #    db('insert into dzdb_test_table values ("5678",60,"2035-01-24","New notes")')
    #    list = qlist(db,'select * from dzdb_test_table')
    #    self.assertEqual(len(list),2)
    #    self.assert_(list[1][0]=='5678')
    #    self.assert_(list[0][1]==50)
    #    list = qlist(db,'select * from dzdb_test_table','AMOUNT')
    #    self.assertEqual(len(list),2)
    #    self.assert_(list[0]==50 and list[1]==60)
    #    db('drop table dzdb_test_table')

    def test_Database_tablenames(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.table_names())
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        self.assert_('dzdb_test_table' in db.table_names())
        db('drop table dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.table_names())

        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        db('insert into dzdb_test_table values ("1234",50,"2005-01-14","Hello there")')
        try:
            t = db.table('dzdb_test_table')
            self.assert_(isinstance(t,Table))
        finally:
            db('drop table dzdb_test_table')
        #self.assert_('dzdb_test_table' in db)

    def test_Database_getattr(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.table_names())
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        self.assert_('dzdb_test_table' in db.table_names())
        db('drop table dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.table_names())

    def test_Database_create_drop_table(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        cols = Columns()
        cols.append(Column('ID','CHAR',10))
        cols.append(Column('NAME','CHAR',25))
        cols.append(Column('AMOUNT','NUMERIC',10,2))
        cols.append(Column('DTADD','DATE'))
        cols.append(Column('NOTES','TEXT'))
        self.assert_(db.create_table('dzdb_test_table',cols)==0)
        self.assert_('dzdb_test_table' in db.table_names())
        db.drop_table('dzdb_test_table')
        self.assert_('dzdb_test_table' not in db.table_names())

    def test_Database_insert_update_record(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        cols = Columns()
        cols.append(Column('ID','CHAR',10))
        cols.append(Column('NAME','CHAR',25))
        cols.append(Column('AMOUNT','NUMERIC',10,2))
        cols.append(Column('DTADD','DATE'))
        cols.append(Column('NOTES','TEXT'))
        db.create_table('dzdb_test_table',cols)
        dt = datetime(2005,01,02)
        db.insert_record('dzdb_test_table',cols,{'DTADD':dt,'ID':'1234','AMOUNT':50,'NOTES':'Testing'})
        self.assertEqual(db('select * from dzdb_test_table').cursor.rowcount,1)
        db.insert_record('dzdb_test_table',cols,{'ID':'4321','AMOUNT':10,'NOTES':'Testing 2'})
        self.assertEqual(db('select * from dzdb_test_table').cursor.rowcount,2)
        db.update_record('dzdb_test_table','ID',cols,{'ID':'4321','NOTES':"Updated"})
        self.assertEqual(db('select * from dzdb_test_table').cursor._rows[1][4],"Updated")
        db('drop table dzdb_test_table')
        db('drop table if exists dz_test_contacts')
        db('create table dz_test_contacts (contactid integer PRIMARY KEY AUTO_INCREMENT,userid    char(20) UNIQUE, key (userid),password  char(16),email     char(60), key (email))')
        db('insert into dz_test_contacts values (1,"testuser","pass","test@datazoomer.net")')
        self.assertEqual(db.lastrowid,1)
        db('insert into dz_test_contacts values (4,"2testuser","pass","test@datazoomer.net")')
        self.assertEqual(db.lastrowid,4)
        db('drop table dz_test_contacts')

    def test_Record(self):
        db = test_database()
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        db('insert into dzdb_test_table values ("1234",50,"2005-01-14","Hello there")')
        recordset = db('select * from dzdb_test_table')
        for rec in recordset:
            self.assertEqual(rec.ID,'1234')
            rec.ID = '4556'
            self.assertEqual(rec.ID,'4556')
            self.assertEqual(rec.as_dict()['ID'],'4556')
            self.assertEqual(rec.as_obj().ID,'4556')
            self.assertEqual(rec[0],'4556')
        db('drop table dzdb_test_table')

    def test_Record_metadata(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        db('insert into dzdb_test_table values ("1234",50,"2005-01-14","Hello there")')
        recordset = db('select * from dzdb_test_table')
        rec = recordset[0]
        self.assert_(rec._columns_[0].name == 'ID')
        db('drop table dzdb_test_table')

    def test_Table(self):
        db = test_database()
        db('drop table if exists dzdb_test_table')
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT)')
        table = db.table('dzdb_test_table','ID')
        record = table.new_record()
        record.ID='1234'
        record.AMOUNT=90
        record.DTADD = datetime(1998,02,11)
        record.NOTES="Testing Testing"
        table.insert_record(record)
        table.insert({'ID':'2345','DTADD':datetime(1998,12,25),'AMOUNT':23,'NOTES':'Hello'})
        table.reset()
        for rec in table:
            self.assert_(rec.ID=='1234' or rec.ID=='2345')
            self.assert_(rec.DTADD==date(1998,02,11) or rec.DTADD==date(1998,12,25))
            self.assert_(rec.AMOUNT==23 or rec.AMOUNT==90)
            self.assert_(rec.NOTES=='Testing Testing' or rec.NOTES=='Hello')
            rec = table.seek('1234')
        self.assert_(rec.AMOUNT==90 and rec.NOTES=='Testing Testing')
        rec = table.seek('2345')
        self.assert_(rec.AMOUNT==23 and rec.NOTES=='Hello')
        table.indexname = 'AMOUNT'
        rec = table.seek(90)
        self.assert_(rec.ID=='1234' and rec.NOTES=='Testing Testing')
        rec.ID = 'New ID'
        table.update(rec)
        table.reset()
        rec = table.seek(90)
        self.assert_(rec.ID == 'New ID' and rec.NOTES=='Testing Testing' and rec.DTADD==date(1998,02,11))
        table.update({'AMOUNT':23,'NOTES':'Updated Notes'})
        table.reset()
        rec = table.seek(23)
        self.assert_(rec.NOTES=='Updated Notes' and rec.ID=='2345')
        rec.DTADD = datetime(2004,11,22)
        table.update(rec)
        table.reset()
        rec = table.seek(23)
        self.assert_(rec.DTADD==date(2004,11,22) and rec.ID=='2345')
        table.delete(23)
        table.reset()
        rec = table.seek(23)
        self.assert_(rec==None)
        db('drop table dzdb_test_table')
        db('drop table if exists dz_test_contacts')
        db('create table dz_test_contacts (contactid integer PRIMARY KEY AUTO_INCREMENT,userid    char(20) UNIQUE, key (userid),password  char(16),email     char(60), key (email))')
        table = db.table('dz_test_contacts')
        table.insert_record({"contactid":1,"userid":"testuser","password":"pass","email":"test@datazoomer.net"})
        self.assertEqual(table.lastrowid,1)
        table.insert_record({"contactid":4,"userid":"2testuser","password":"pass","email":"test@datazoomer.net"})
        self.assertEqual(table.lastrowid,2)
        db('drop table dz_test_contacts')

    def test_Database_decimal(self):
        db = test_database()

        db('drop table if exists dzdb_test_table')
        db('create table dzdb_test_table (ID CHAR(10),AMOUNT NUMERIC(10,2),DTADD DATE,NOTES TEXT,BUCKS DECIMAL(8,2))')
        cols = db.table('dzdb_test_table').columns

        db.insert_record('dzdb_test_table',cols,{'DTADD':datetime(2005,1,2),'ID':'1234','AMOUNT':50,'NOTES':'Testing','BUCKS':12.54})
        db.insert_record('dzdb_test_table',cols,{'ID':'4321','AMOUNT':10,'NOTES':'Testing 2','BUCKS':32.54})
        db.insert_record('dzdb_test_table',cols,{'ID':'4322','AMOUNT':10,'NOTES':'Testing 3','BUCKS':62.54})

        rs = db.table('dzdb_test_table')
        t = '%(BUCKS)9.2f' % rs[0]

        db('drop table dzdb_test_table')

    def test_Table_seek(self):
        db = test_database()

        db('drop table if exists dzdb_test_table')
        cols = Columns([
            Column('ID','NUMERIC',10),
            Column('NAME','CHAR',25),
            Column('AMOUNT','NUMERIC',10,2)])
        db.create_table('dzdb_test_table',cols)
        t = db.table('dzdb_test_table')
        from decimal import Decimal
        t.insert_record({'ID':1,'NAME':'Andy','AMOUNT':Decimal('10')})
        db.insert_record('dzdb_test_table',t.columns,{'ID':2,'NAME':'Alex','AMOUNT':Decimal('100.24')})
        t = db.table('dzdb_test_table','ID')
        rec = t.seek(1)
        self.assert_(rec.ID==1 and rec.NAME=='Andy' and rec.AMOUNT==Decimal('10.00'))
        rec = t.seek(2)
        self.assert_(rec.ID==2 and rec.NAME=='Alex' and rec.AMOUNT==Decimal('100.24'))
        db('drop table dzdb_test_table')

    def test_Table_locate(self):
        db = test_database()

        db('drop table if exists dzdb_test_table')
        cols = Columns([
            Column('ID','NUMERIC',10),
            Column('NAME','CHAR',25),
            Column('AMOUNT','NUMERIC',10,2)])
        db.create_table('dzdb_test_table',cols)
        t = db.table('dzdb_test_table')
        from decimal import Decimal
        t.insert_record({'ID':1,'NAME':'Andy','AMOUNT':Decimal('10')})
        db.insert_record('dzdb_test_table',t.columns,{'ID':2,'NAME':'Alex','AMOUNT':Decimal('100.24')})
        t = db.table('dzdb_test_table','ID')
        rec = t.locate(ID=1)[0]
        self.assert_(rec.ID==1 and rec.NAME=='Andy' and rec.AMOUNT==Decimal('10.00'))
        rec = t.locate(NAME='Alex')[0]
        self.assert_(rec.ID==2 and rec.NAME=='Alex' and rec.AMOUNT==Decimal('100.24'))
        db('drop table dzdb_test_table')


