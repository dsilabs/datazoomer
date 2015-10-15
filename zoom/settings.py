"""
    settings.py

    manages system and application settings
"""

from utils import Record


class SystemSettings(Record):
    @classmethod
    def defaults(cls, config):
        return dict(
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

class ApplicationSettings(Record):
    @classmethod
    def defaults(cls, config):
        negative = ['NO', 'No', 'nO', 'no', 'N', 'n', False, '0', 0]
        return dict(
            title   = config.get('settings','title',''),
            icon    = config.get('settings','icon','blank_doc'),
            version = config.get('settings','version',0.0),
            enabled = config.get('settings','enabled',True) not in negative,
            visible = config.get('settings','visible',True) not in negative,
            theme   = config.get('settings','theme',''),
            description = config.get('settings','description',''),
            categories = config.get('settings','categories',''),
            tags =config.get('settings','tags',''),
            keywords = config.get('settings','keywords',''),
            in_development = config.get('settings','in_development',False) not in negative,
        )


class Settings(object):
    """manage settings

        >>> from system import system
        >>> from store import EntityStore
        >>> from application import Application

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

        >>> app_store = EntityStore(system.database, ApplicationSettings)
        >>> myapp = Application('myapp', 'apps/activity/app.py')
        >>> myapp.get = myapp.read_config
        >>> myapp_settings = Settings(app_store, myapp, 'myapp')
        >>> myapp_settings.get('visible', False)
        True
        >>> myapp_settings.get('title', 'testing')
        'Activity'
        >>> myapp_settings.get('theme', 'came_out_blank')
        'came_out_blank'
    """

    def __init__(self, store, config, context):
        self.store = store
        self.klass = store.klass
        self.context = context
        self.config = config
        self.refresh()

    def app(self, app_name):
        """ return an app settings object from the site settings """
        from zoom import manager, EntityStore
        return Settings(
            EntityStore(self.store.db, ApplicationSettings),
            manager.get_app(app_name),
            app_name
          )

    def refresh(self):
        config = self.config
        self.defaults = self.klass.defaults(config)
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
        #return self.values.get(k, self.defaults.get(key, default))
        return self.values.get(k, self.defaults.get(key, default) or default)

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

