
import time
import uuid
from model import *
from zoom.fill import viewfill
from zoom.user import User, add_user

welcome_messages = dict(
    none = '',
    one = '<B>Thanks for choosing <dz:site_name>!<b> You\'re 60 seconds away from new your <dz:site_name> account.',
    two = 'You\'re 60 seconds away from new your <dz:site_name> account.',
    three = 'You\'re 60 seconds away from new your <dz:site_name> account.  <B>Thanks for choosing <dz:site_name>!',
    )

def experiment(test):
    return test in user.groups

def gen_password():
    return uuid.uuid4().get_hex()[-10:]

def insert_user(data):
    user_rec = dict(
        FIRSTNAME = data.first_name,
        LASTNAME = data.last_name,
        LOGINID = data.username,
        EMAIL = data.email,
        PHONE = data.phone,
        PASSWORD = gen_password(),
        DTUPD = now,
        DTADD = now,
        STATUS = 'A',
        )
    db = system.database
    table = db.table('dz_users', 'USERID')
    new_id = table.insert(user_rec)

    # set user password
    user = User(data.username)
    user.set_password(data.password)

    # make sure new users don't accidentally get access
    db('delete from dz_members where userid=%s', new_id)

    # add default group
    add_user(user.username, 'users')
    return new_id

def app():
    if user.is_admin:
        if len(route) == 1:
            labels = 'First Name','Last Name','Username','Password','Token','Expiry','Action'
            content = browse([
                dict(
                    username = i.username,
                    token = i.token,
                    password = i.password,
                    expiry = i.expiry,
                    first_name = i.first_name,
                    last_name = i.last_name,
                    action = link_to('activate', '/'+system.app.name, i.username, 'activate'),
                    )
                for i in Registration.all()],
                labels=labels)
            return page(content, title='Registrations')

        elif len(route) == 3 and route[2]=='activate':
            username = route[1]
            r = Registration.find(username=username)
            if r:
                insert_user(r[0])
                r[0].delete()
                return page('registration activated for <strong>%s</strong>' % username, title='Registrations')

    if len(route)==3 and route[:2] == ['register','confirm']:
        rlist = Registration.find(token=route[2])
        if rlist:
            r = rlist[0]
            if r.expiry < time.time():
                return Page('expired.txt', dict(register_link=url_for('/register')))

            elif email_registered(r.email):
                return Page('already_register')

            elif not username_available(r.username):
                return Page('name_taken')

            else:
                insert_user(r)
                return Page('register_complete')

        return Page('<H1>Register</H1><dz:form>%s</form>'%fields.edit())

    elif data:

        fields.update(**data)
        if fields.valid():
            err = get_errors(data)
            if not err:
                r = Registration(**data)
                r.token = token = str(uuid.uuid4().hex)
                r.expiry = time.time() + 3600 # one hour
                r.put()

                tpl = markdown(open('activate.txt').read())
                activation_link = abs_url_for('/register/confirm',token)
                callback = dict(link=activation_link,site_name=site_name()).get
                recipient = data['EMAIL']
                msg = viewfill(tpl,callback)
                try:
                    if recipient <> 'testuser@datazoomer.com':
                        send(recipient, site_name()+' registration',msg)
                except:
                    logger.error('Registration error sending %s to %s' % (token, recipient))
                    msg = 'fail'
                    raise
                else:
                    logger.info('Registration sent to %s with token %s' % (recipient, token))
                    msg = markdown(open('step2.txt').read())
                return Page(msg)

            else:
               error(*err) 

    if experiment('welcome_message'):
        msg = 'You\'re just seconds from your new <dz:site_name> account.  <strong>Thanks for choosing <dz:site_name>!</strong>'
    else:
        msg = ''

    return Page('<H1>Register</H1>%s<br><dz:form>%s</form>'%(msg,fields.edit()))




