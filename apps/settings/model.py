

from zoom import *

class MyModel(Record):
    pass

system_settings_form = Form(
    Section('Site',[
        TextField('Site Name', required),
        TextField('Site Slogan', size=60, maxlength=80),
        TextField('Owner Name', required),
        URLField('Owner URL'),
        EmailField('Owner Email', required),
        EmailField('Admin Email', required),
    ]),
    Section('Theme',[
        TextField('Name', name='THEME_NAME'),
        TextField('Template', name='THEME_TEMPLATE'),
    ]),
    Section('Mail',[
        TextField('SMTP Host'),
        TextField('SMTP Port'),
        TextField('SMTP User'),
        TextField('SMTP Password'),
        EmailField('From Address'),
        URLField('Logo URL'),
        TextField('GNUPG Home'),
    ]),
    Section('Monitoring',[
        CheckboxField('Application Database Log', options=['on','off']),
    ]),
    Buttons(['Save', 'Set to Defaults'], cancel='/settings'),
    )

user_settings_form = Form(
    Section('Apps',[
        TextField('Home'),
        TextField('Icon'),
    ]),
    Section('Theme',[
        TextField('Name', name='THEME_NAME'),
        TextField('Template', name='THEME_TEMPLATE'),
    ]),
    Section('System',[
        TextField('Profile'),
    ]),
    Buttons(['Save'], cancel='/settings/user'),
    )

system_settings_form

def get_defaults():
    return system.settings.defaults

def initialize():
    # put field values back to what is in the system config files
    system_settings_form.initialize(get_defaults())

def load():
    system_settings_form.initialize(get_defaults())
    system_settings_form.update(system.settings.load())

def load_user():
    user_settings_form.initialize(user.settings.defaults)
    user_settings_form.update(user.settings.load())

def save(values):
    values = dict((k.lower(),v) for k,v in values if v <> None)
    system.settings.save(values)

def save_user(values):
    values = dict((k.lower(),v) for k,v in values if v <> None)
    user.settings.save(values)
