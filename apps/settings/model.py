

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
    #Section('Users',[
    #    TextField('Default', default='guest'),
    #    TextField('Administrator Group', default='administrators'),
    #    TextField('Developer Group', default='developers'),
    #    TextField('Managers Group', default='managers'),
    #]),
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

system_settings_form

def get_defaults():
    return system.settings.defaults

def initialize():
    # put field values back to what is in the system config files
    system_settings_form.initialize(get_defaults())

def load():
    system_settings_form.initialize(get_defaults())
    system_settings_form.update(system.settings.load())

def save(values):
    values = dict((k.lower(),v) for k,v in values if v <> None)
    system.settings.save(values)


