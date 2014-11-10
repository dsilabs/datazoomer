
import datetime
import uuid
from zoom import *
from zoom.user import activate_user, deactivate_user, add_user, get_username, User as ZoomUser
from zoom.fill import viewfill
from zoom.log import audit, logger

db = system.database

def email_unknown_test(email):
    userid = route[1]
    return not bool(db('select * from dz_users where userid<>%s and email=%s', userid, email))

def username_available_test(username):
    userid = route[1]
    return not bool(db('select * from dz_users where userid<>%s and loginid=%s', userid, username))

username_available = Validator('taken', username_available_test)
not_registered = Validator('already registered', email_unknown_test)

personal_fields = Section('Personal',[
    TextField('First Name', required, valid_name),
    TextField('Last Name', required, valid_name),
    TextField('Email', required, valid_email, not_registered),
    PhoneField('Phone', valid_phone, hint='optional'),
    ])

account_fields = Section('Account',[
    TextField('Username', required, valid_username, username_available),
    ])

new_user_button_fields = Fields(
        CheckboxField('Send invitation'),
        ButtonField('Add This User', name='add_user_button', cancel='cancel'),
        )
    
password_fields = Fields([
    TextField('New Password', required, valid_password, name='PASSWORD', size=30),
    TextField('Confirm New Password', required, valid_password, name='CONFIRM', size=30),
    CheckboxField('Resend Invitation'),
    ])
    
user_fields = Fields(personal_fields, account_fields)
new_user_form = Form(user_fields, new_user_button_fields)

def gen_password():
    return uuid.uuid4().get_hex()[-10:]

class User:
    def __init__(self,*a,**k):
        self.__dict__ = k

    def __getitem__(self,name):
        return self.__dict__.get(name)

    def get_full_name(self):
        return '%(first_name)s %(last_name)s' % self

    def delete(self):
        msg = '<a href="/users/%s">%s</a> deleted user %s' 
        logger.activity('users', msg % (user.id, user.username, self.username))
        audit('delete user account', self.username, '')
        return Users.delete(self.id) 

    def activate(self):
        logger.log('I','user activated by %s' % user.username, username=self.username)
        audit('activate user account', self.username, '')
        return activate_user(self.username)
        
    def deactivate(self):
        audit('deactivate user account', self.username, '')
        return deactivate_user(self.username)
        
class Users:

    @classmethod
    def all(cls):
        t = db('create temporary table last_seen select user, max(timestamp) timestamp from log group by user')
        return db('select a.*, timestamp from dz_users a left join last_seen b on (a.loginid=b.user) order by loginid')

    @classmethod
    def recent(cls):
        return db('select dz_users.*, max(timestamp) timestamp from dz_users, log where loginid=user group by loginid order by timestamp desc limit 10')

    @classmethod
    def get(cls,id):
        result = db('select * from dz_users where userid=%s',id)
        if result:
            user = User(
                first_name=result[0].firstname,
                last_name=result[0].lastname,
                email=result[0].email,
                phone=result[0].phone,
                username=result[0].loginid,
                status=result[0].status,
                id=result[0].userid)
            return user
        result = db('select * from dz_users where loginid=%s',id)
        if result:
            user = User(
                first_name=result[0].firstname,
                last_name=result[0].lastname,
                email=result[0].email,
                phone=result[0].phone,
                username=result[0].loginid,
                status=result[0].status,
                id=result[0].userid)
            return user

    @classmethod
    def delete(self,id):
        result = db('delete from dz_members where userid=%s',id)
        result = db('delete from dz_users where userid=%s',id)

    @classmethod
    def update(cls,id,**keywords):
        user_fields.update(**keywords)
        values = user_fields.evaluate()
        values['USERID'] = id
        values['FIRSTNAME'] = values['FIRST_NAME']
        values['LASTNAME'] = values['LAST_NAME']
        values['LOGINID'] = values['USERNAME'].lower()
        values['DTUPD'] = datetime.datetime.now()
        values['STATUS'] = 'A'
        table = db.table('dz_users','USERID')
        rec = table.seek(id)
        table.update(values)
    
    @classmethod
    def insert(cls, form):
        values = form.evaluate()
        username = values['USERNAME'].lower()
        password = gen_password()

        values['FIRSTNAME'] = values['FIRST_NAME']
        values['LASTNAME'] = values['LAST_NAME']
        values['LOGINID'] = username
        values['PASSWORD'] = ''
        values['DTUPD'] = values['DTADD'] = datetime.datetime.now()
        values['STATUS'] = 'A'

        users = db.table('dz_users','USERID')
        id = users.insert(values)

        db('delete from dz_members where userid=%s', id) # make sure new users have no memberships
        add_user(values['LOGINID'], 'users')

        new_user = ZoomUser(username)
        new_user.set_password(password)

        msg = '<a href="/users/%s">%s</a> added new user <a href="/users/%s">%s</a>' 
        logger.activity('users', msg % (user.id, user.username, new_user.id, new_user.username))
        audit('created user account', new_user.username)

        if values['SEND_INVITATION'] == True:
            recipients = [values['EMAIL']]
            tpl = load('welcome.md')
            t = dict(
                    first_name = values['FIRST_NAME'],
                    username = username,
                    password = password,
                    site_name = site_name(),
                    site_url = site_url(),
                    admin_email = 'support@dynamic-solutions.com',
                    owner_name = owner_name(),
                    )
            body = markdown(viewfill(tpl, t.get))
            subject = 'Welcome - ' + site_name()
            send(recipients, subject, body)
            message('invitation sent')

    

if __name__ == '__main__':
    print 'done'
    
    users = Users()
    print users.all()
