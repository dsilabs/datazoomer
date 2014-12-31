"""
    settings.py

    manages system and application settings
"""

from utils import Record #zoom.store import Record, EntityStore

class SystemSettings(Record): pass

class Settings(object):
    """manage settings
        
        >>> from system import system
        >>> from store import EntityStore

        >>> system.setup_test()
        >>> settings_store = EntityStore(system.database, SystemSettings)
        >>> settings = Settings(settings_store, system.config, 'system')

        >>> settings.reset('site_name')
        >>> settings.get('site_name', 'no_site')
        'Zoom'
        
        >>> settings.get('no_such_setting', 'no_setting')
        'no_setting'
        
        >>> settings.set('site_name', 'datazoomer.com')
        >>> settings.get('site_name', 'no_site')
        'datazoomer.com'
    """

    def __init__(self, store, config, context):
        self.store = store
        self.context = context
        self.config = config
        self.refresh()

    def refresh(self):

        config = self.config

        self.defaults = dict(

            site_name     = config.get('site','name','Your Site'),
            site_slogan   = config.get('site','slogan','Ridiculously Rapid Application Development'),
            owner_name    = config.get('site','owner_name','Your Company'),
            owner_email   = config.get('site','owner_email','owner@yourcompany.com'),
            owner_url     = config.get('site','owner_url','http://www.yourcompanysite.com'),
            admin_email   = config.get('site','admin_email','admin@yourcompany.com'),

            smtp_host     = config.get('mail','smtp_host','mail.yourcompany.com'),
            smtp_port     = config.get('mail','smtp_port','587'),
            smtp_user     = config.get('mail','smtp_user','noreply@yourcompany.com'),
            smtp_password = config.get('mail','smtp_passwd','yourpassword'),
            from_address  = config.get('mail','from_addr',''),
            logo_url      = config.get('mail','logo',''),
            gnugp_home    = config.get('mail','gnugp_home',''),

            )

        self.values = dict((r['key'],r['value']) for r in self.store)

    def set(self, key, value):
        k = '.'.join((self.context,key))
        r = self.store.first(key=k)
        if not r:
            r = SystemSettings(key=k)
        r['value'] = value
        self.store.put(r)
        self.values[k] = value

    def get(self, key, default=None):
        k = '.'.join((self.context,key))
        return self.values.get(k, self.defaults.get(key, default))

    def defaults(self):
        return self.defaults

    def reset(self, key):
        k = '.'.join((self.context,key))
        self.store.delete(self.store.first(key=k))
        self.refresh()

    def save(self, settings):
        for key, value in settings.items():
            if value <> None:
                self.set(key, value)

    def load(self):
        prefix = self.context + '.'
        return dict(
                (r['key'][len(prefix):],r['value']) 
                for r in self.store if r['key'].startswith(prefix))

