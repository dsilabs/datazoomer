
from zoom import *
import zoom.storage as storage
from zoom.user import authenticate

db = system.database

thumbnail_size = 100, 100

password_fields = Fields([
        PasswordField('Old Password', required),
        PasswordField('New Password', required, valid_new_password),
        PasswordField('Confirm', required, valid_new_password),
    ])

main_form = Fields([
        Section('Basic',[
            TextField('First Name'),
            TextField('Last Name'),
            TextField('Login ID',size=15),
            TextField('Email',size=40),
            TextField('Phone',size=20),
            TextField('City',size=20),
        ]),
        Section('Social',[
            TextField('Web'),
            TextField('Blog'),
            TextField('Twitter',size=20),
        ]),
        Section('Bio',[
            MemoField('About You', cols=40, name="ABOUT"),
        ]),
        ButtonField('Update Profile'),
    ])
    

def make_thumbnail(picture_name,picture_data):
    picture_type = picture_name.rsplit('.')[-1:][0].lower()

    from PIL import Image
    if picture_type in ['jpg','gif','png']:
        import StringIO
        picture_file = StringIO.StringIO()
        picture_file.write(picture_data)
        picture_file.seek(0)

        picture_data = StringIO.StringIO()
        
        im = Image.open(picture_file)
        square_size = min(im.size)
        left_offset = (im.size[0] - square_size) / 2
        top_offset  = (im.size[1] - square_size) / 2
        im2 = im.crop((left_offset,top_offset,square_size+left_offset,square_size+top_offset))
        im2.thumbnail(thumbnail_size, Image.ANTIALIAS)
        im2.save(picture_data, "PNG")
        return picture_data.getvalue()            


class InvalidPassword(Exception): pass

class profile3_Profile(storage.Model):

    def validate(self):
        def missing(fname):
            return not (hasattr(self,fname) and getattr(self,fname))
        
        errors = []
        if missing('first_name'): errors.append('please provide first name')
        if missing('last_name'): errors.append('please provide last name')
        if missing('email'): errors.append('please provide email address')
        return errors

    def put(self):
        id = user.user_id
        values = main_form.evaluate()
        values['USERID'] = id
        values['FIRSTNAME'] = values['FIRST_NAME']
        values['LASTNAME'] = values['LAST_NAME']
        values['LOGINID'] = values['LOGIN_ID']
        values['DTUPD'] = datetime.datetime.now()
        values['STATUS'] = 'A'
        table = db.table('dz_users','USERID')
        rec = table.seek(id)
        table.update(values)
        storage.Model.put(self)

    def valid(self):
        return self.validate() == []

    # update
    def update(self,values):
        main_form.update(**values)
                
        storage.Model.update(self,
            first_name = values.get('FIRST_NAME'),
            last_name  = values.get('LAST_NAME'),
            email      = values.get('EMAIL'),
            web        = values.get('WEB',''),
            blog       = values.get('BLOG',''),
            twitter    = values.get('TWITTER',''),
            phone      = values.get('PHONE',''),
            city       = values.get('CITY',''),
            about      = values.get('ABOUT',''))
        
    # Password methods
    def authentic(self,password):
        return authenticate(user.login_id, password)
        
    def set_password(self,new_password):
        if valid_new_password(new_password):
            user.set_password(new_password)
        else:
            raise InvalidPassword;           
        
    # Photo methods
    def update_photo(self,name,data):
        thumbnail = make_thumbnail(name,data)
        if thumbnail:
            self.photo = thumbnail
            storage.Model.put(self)
            return 1

    def delete_photo(self):
        if hasattr(self,'photo'):
            del self.photo
        self.put()
        
    def has_photo(self):
        return 'photo' in self.__dict__        

    def get_photo(self):
        return open('no_photo.png','rb').read()
            
Profile = profile3_Profile

def current_user():
    
    profile = Profile.find(user_id=user.user_id)
    if profile:
        return profile[0]
    else:
        return Profile(USER_ID=user.user_id,LOGIN_ID=user.login_id,first_name=user.first_name,last_name=user.last_name,email=user.email,phone=user.phone)
    return 


if __name__ == '__main__':
    import unittest
    
    # don't use system database
    del zoomer.db

    # connect to test database
    import MySQLdb
    from dzdb import Database
    dbhost  = zoomer.config.get('database','dbhost')
    dbuser  = 'dzdev'
    dbname  = 'dz_test'
    dbpass  = 'password'
    zoomer.db = dzstore.db = Database(MySQLdb.Connect,host=dbhost,user=dbuser,passwd=dbpass,db=dbname)
    print 'model test\nconnected to %s on %s as %s' % (dbname,dbhost,dbuser)
    
    class ProfileEmptyTest(unittest.TestCase):
        def setUp(self):
            Profile.zap()
            self.assertEqual(len(Profile.all()),0)
        
        def test_current_user_empty_profile_table(self):
            assert current_user()
            self.assertEqual(len(Profile.all()),0)
            
        def test_current_user_add_first_profile_to_empty_table(self):
            user = current_user()
            user.first_name = 'Joe'
            user.last_name  = 'Smith'
            user.email      = 'joe@smith.com'
            user.put()
            self.assertEqual(len(Profile.all()),1)
            
        def test_current_user_failed_attempt_to_add_first_profile_to_empty_table(self):
            user = current_user()
            user.first_name = 'Joe'
            user.last_name  = 'Smith'
            # email required but missing so should not post
            user.put()
            self.assertEqual(len(Profile.all()),0)


    class ProfileTest(unittest.TestCase):
    
        def setUp(self):
            Profile.zap()
            user = current_user()
            user.first_name = 'Joe'
            user.last_name  = 'Smith'
            user.email      = 'joe@smith.com'
            user.put()
            self.assertEqual(len(Profile.all()),1)
        
        def test_update_name(self):
            user = current_user()
            self.assertEqual(user.first_name,'Joe')
            user.first_name = 'Gerry'
            user.put()
            user2 = current_user()
            self.assertEqual(user2.first_name,'Gerry')

        def test_update_photo(self):
            photo_data = open('P1010201.JPG','rb').read()
            no_photo   = open('no_photo.png','rb').read()
            user = current_user()
            self.assertEqual(user.photo,no_photo)
            user.update_photo('P1010201.JPG',photo_data)
            self.assertEqual(user.photo,make_thumbnail('P1010201.JPG',open('P1010201.JPG','rb').read()))
            

            
    unittest.main()
    
                        
    
    
    
    


