

from zoom import *

class MyModel(Record):
    pass

system_settings_form = Form(
    Section('Site',[
        TextField('Site Name', required),
        TextField('Site Slogan'),
        TextField('Owner Name', required),
        EmailField('Admin Email', required),
        EmailField('Register Email'),
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
    Buttons(['Save', 'Set to Defaults'], cancel='/settings'),
    )

system_settings_form

def get_defaults():
    return dict(
        site_name     = system.config.get('site','name'),
        site_slogan   = system.config.get('site','slogan'),
        owner_name    = system.config.get('site','owner_name'),
        owner_email   = system.config.get('site','owner_email'),
        admin_email   = system.config.get('site','admin_email'),
        smtp_host     = system.config.get('mail','smtp_host'),
        smtp_port     = system.config.get('mail','smtp_port'),
        smtp_user     = system.config.get('mail','smtp_user'),
        smtp_password = system.config.get('mail','smtp_passwd'),
        from_address  = system.config.get('mail','from_addr'),
        logo_url      = system.config.get('mail','logo'),
        gnugp_home    = system.config.get('mail','gnugp_home',''),
        )

def initialize():
    # put field values back to what is in the system config files
    system_settings_form.initialize(get_defaults())

def load():
    system_settings_form.initialize(get_defaults())
    system_settings_form.update(system.settings.load())

def save(values):
    values = dict((k.lower(),v) for k,v in values if v)
    system.settings.save(values)


