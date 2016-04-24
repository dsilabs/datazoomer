
import re 
import time
import uuid
import datetime

from zoom import *
from zoom.user import User, add_user
from zoom.fill import viewfill


REGISTRATION_TIMEOUT = 3600 # one hour


class Registration(Record):

    @property
    def action(self):
        activate_link = link_to('activate', system.app.url, self.token, 'confirm')
        delete_link = link_to('delete', system.app.url, self.token, 'delete')
        return activate_link + ' ' + delete_link

    @property
    def expires(self):
        diff = self.expiry - time.time()
        if diff > 0:
            suffix = 'from now'
        else:
            suffix = 'ago'
            diff = -diff
        now = datetime.datetime.now()
        then = datetime.datetime.now() + datetime.timedelta(seconds=diff)
        return '{} {}'.format(how_long(now, then), suffix)


registrations = EntityStore(system.db, Registration)


def gen_password():
    return uuid.uuid4().get_hex()[-10:]


def is_test_account(data):
    email = data.EMAIL
    return 'test' in email and (
        email.endswith('@datazoomer.com') or
        email.endswith('@testco.com')
    )


def get_errors(fields):

    messages = []

    sections = fields.fields
    for section in sections:
        for field in section.fields:
            field.placeholder = field.label
            if field.msg:
                field.css_class += ' invalid'
                messages.append('Invalid {f.label} - {f.msg}'.format(f=field))

    values = fields.evaluate()
    if values['PASSWORD'] != values['CONFIRM']:
        sections[1].fields[1].css_class += ' invalid'
        sections[1].fields[2].css_class += ' invalid'
        messages.append('passwords must match')

    return set(messages)


def email_registered(email):
    registered = bool(system.database('select * from dz_users where email=%s',email))
    return registered


def username_available(username):
    taken = bool(system.database('select * from dz_users where loginid=%s',username))
    return not taken


def username_valid(username):
    return re.match(r'^[a-zA-Z0-9.@]+$',username)


def email_valid(email):
    return re.match(r'^([^@\s]+)@((?:[-a-z0-9]+\.)+[a-z]{2,})$',email)


not_registered = Validator("already registered", email_registered)
name_available = Validator("already taken", username_available)
valid_username = Validator('letters and numbers only', username_valid)
valid_password = Validator('minimum length 6', lambda a: not len(a)<6)
valid_email    = Validator('invalid email address', email_valid)


fields = Fields([
        Section('First, the basics',[
            TextField('First Name', required, valid_name, maxlength=40, placeholder='First Name'),
            TextField('Last Name', required, maxlength=40, placeholder="Last Name"),
            EmailField('Email', required, valid_email, maxlength=60,
                       placeholder='Email'),
        ]),
        Section('Next, choose a username and password',[
            TextField('Username', required, valid_username, name_available, maxlength=50, size=30),
            PasswordField('Password', required, valid_password, maxlength=16, size=20),
            PasswordField('Confirm',required, maxlength=16, size=20),
        ]),
    ])


def submit_registration(data):
    """receive data submitted via registration form"""
    rec = Registration(**data)
    rec.token = token = uuid.uuid4().hex
    rec.expiry = time.time() + REGISTRATION_TIMEOUT

    if is_test_account(rec):
        logger.warning('no email sent to test account')
        warning('test account - registration email will not be sent')
        rec.token = '1234'

    else:
        try:
            recipient = rec.EMAIL
            tpl = load_content('activate.txt')
            activation_link = abs_url_for('/register/confirm',token)
            callback = dict(link=activation_link,site_name=site_name()).get
            body = viewfill(tpl,callback)

            send(recipient, site_name()+' registration', body)
            logger.info('registration sent to %s with token %s' % (recipient, token))
        except:
            logger.error('Registration error sending %s to %s' % (token, recipient))
            raise

    registrations.put(rec)

    return True


def delete_registration(token):
    registration = registrations.first(token=token)
    if registration:
        registrations.delete(registration)


def confirm_registration(token):
    registration = registrations.first(token=token)
    if registration:
        if registration.expiry < time.time():
            # happens if the users waits too long
            result = Page('expired.txt', dict(register_link=url_for('/register')))

        elif email_registered(registration.email):
            # can happen if someone registers using the same email address
            # between the time that we issue the token and when the user gets
            # around to confirming.
            result = Page('already_register')

        elif not username_available(registration.username):
            # can happen if someone registers using the same username
            # between the time that we issue the token and when the user gets
            # around to confirming.
            result = Page('name_taken')

        else:
            # good to go
            register_user(registration)
            registrations.delete(registration)
            result = Page('register_complete')

        if user.is_admin:
            message('registration activated for {}'.format(registration.username))

        return result


def register_user(data):
    user_rec = dict(
        FIRSTNAME=data.first_name,
        LASTNAME=data.last_name,
        LOGINID=data.username,
        EMAIL=data.email,
        PASSWORD=gen_password(),
        DTUPD=now,
        DTADD=now,
        STATUS='A',
    )

    db = system.database
    table = db.table('dz_users', 'USERID')
    new_id = table.insert(user_rec)

    # set user password
    new_user = User(data.username)
    new_user.set_password(data.password)

    # make sure new users don't accidentally get access
    db('delete from dz_members where userid=%s', new_id)

    # add default group
    add_user(new_user.username, 'users')
    return new_id

