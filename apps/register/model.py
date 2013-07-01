
import re 

from zoom import *
from zoom.storage import Model

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
        Section('The Basics',[
            TextField('First Name', required, maxlength=40),
            TextField('Last Name', required, maxlength=40),
            EmailField('Email', required, valid_email, maxlength=60),
            PhoneField('Phone',hint='optional', maxlength=30),
        ]),
        Section('Now, choose a username and password',[
            TextField('Username', required, valid_username, name_available, maxlength=50, size=30),
            PasswordField('Password', required, valid_password, maxlength=16, size=20),
            PasswordField('Confirm',required, maxlength=16, size=20),
        ]),
        ButtonField('Register Now')
    ])

def get_errors(data):
    def verify(message,valid):
        if not valid:
            errors.append(message)
    errors = []
    verify('passwords must match', data['PASSWORD'] == data['CONFIRM'])
    return errors

class Registration(Model): pass

