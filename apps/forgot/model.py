
import uuid
import time

from zoom import *
from zoom.storage import Model
from zoom.fill import fill
from zoom.validators import valid_new_password
from zoom.user import User

db = system.database

class ForgotToken(Model): 
    
    def get_expired(self):
        return time.time() > self.expiry

def valid_email(email):
    return re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$", email)
    
def user_by_email(email):
    cmd = "SELECT * FROM dz_users WHERE email=%s and status='A'"
    dataset = db(cmd,email)
    if len(dataset):
        return dataset[0]

def valid_token(token):
    rec = ForgotToken.find(token=token)
    if len(rec):
        return not rec[0].expired

def user_by_token(token):
    rec = ForgotToken.find(token=token)
    if len(rec):
        return user_by_email(rec[0].email)

def process_reset_request(token):
    if not valid_token(token):
        return Page('expired')

    rec = ForgotToken.find(token=token)
    if len(rec):
        user = user_by_email(rec[0].email)
        if user:
            user_name = user['LOGINID']
            first_name = user['FIRSTNAME']
            return Page('reset',dict(user_name=user_name,first_name=first_name,token=token).get)
        else:                        
            error('invalid request')
            return redirect_to('/')
    else:
        error('invalid reset request')
        return redirect_to('/')
    
def reset_password(token,password,confirm):
        if not valid_token(token):
            return Page('expired')
        elif not valid_new_password(password):
            error('Invalid password ({})'.format(valid_new_password.msg))
        elif password <> confirm:
            error('Passwords do not match')
        else:
            user = user_by_token(token)
            if not user:
                error('Invalid request')
            else:                
                user = User(user['LOGINID'])
                user.set_password(password)
                rec = ForgotToken.find(token=token)[0]
                rec.expiry = time.time()
                rec.put()
                return home('complete')
    
def initiate_password_reset(email):
    if valid_email(email) and user_by_email(email):
        token = uuid.uuid4().hex
        expiry = time.time() + 3600
        ForgotToken(token=token, expiry=expiry, email=email).put()
        reset_link = redirect_to('/forgot/reset?token=%s' % token).headers['Location']

        t1 = file('activate.txt','r').read()
        t2 = fill('{{','}}',t1,dict(reset_link=reset_link).get)
        t = fill('<dz:','>',t2,dict(site_name=site_name()).get)
        send(email,'Password reset',markdown(t))
    else:    
        return 'invalid email address'

txt_missing_user = 'Email address is incorrect.  Please try again.'

