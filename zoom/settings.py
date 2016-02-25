"""
    settings.py

    manages system and application settings
"""

from utils import Record

NEGATIVE = ['NO', 'No', 'nO', 'no', 'N', 'n', False, '0', 0]
POSTITIVE = ['yes', 'y', True, '1', 1]

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

            theme_name    = config.get('theme','name','default'),
            theme_template= config.get('theme','template','default'),

            smtp_host     = config.get('mail','smtp_host','mail.yourcompany.com'),
            smtp_port     = config.get('mail','smtp_port','587'),
            smtp_user     = config.get('mail','smtp_user','noreply@yourcompany.com'),
            smtp_password = config.get('mail','smtp_passwd','yourpassword'),
            from_address  = config.get('mail','from_addr',''),
            logo_url      = config.get('mail','logo',''),
            gnugp_home    = config.get('mail','gnugp_home',''),
        )

class UserSystemSettings(Record):
    """ Per user System settings/context """
    @classmethod
    def defaults(cls, config):
        return dict(
            home            = config.get('apps','home','home'),
            icon            = config.get('apps','icon',''),
            theme_name      = config.get('theme','name',''),
            theme_template  = config.get('theme','template',''),
            profile         = config.get('system','profile',''),
        )

class ApplicationSettings(Record):
    @classmethod
    def defaults(cls, config):
        return dict(
            title   = config.get('settings','title',''),
            icon    = config.get('settings','icon','blank_doc'),
            version = config.get('settings','version',0.0),
            enabled = config.get('settings','enabled',True) not in NEGATIVE,
            visible = config.get('settings','visible',True) not in NEGATIVE,
            theme   = config.get('settings','theme',''),
            description = config.get('settings','description',''),
            categories = config.get('settings','categories',''),
            tags =config.get('settings','tags',''),
            keywords = config.get('settings','keywords',''),
            in_development = config.get('settings','in_development',False) not in NEGATIVE,
        )


class SettingsManager(object):

    def __init__(self, context):
        self.context = context

    def get_bool(self, key, default=''):
        return self.get(key, default).lower() in ['1','y','yes','on']

    def load(self):
        prefix = self.context + '.'
        return dict(
                (r['key'][len(prefix):],r['value'])
                for r in self.store if r['key'].startswith(prefix))

    def put(self, key, value):
        k = '.'.join((self.context, key))
        r = self.store.first(key=k)
        if not r:
            r = SystemSettings(key=k)
        r['value'] = value
        self.store.put(r)
        self.values[k] = value

    def set(self, key, value):
        return self.put(key, value)

    def save(self, settings):
        for key, value in settings.items():
            if value <> None:
                self.set(key, value)


class AppSettingsManager(SettingsManager):

    def __init__(self, settings, app, defaults):
        SettingsManager.__init__(self, app.name)
        self.app = app
        self.store = settings.application_settings_store
        self.values = settings._application_dict
        self.defaults = defaults
        self.context = app.name

    def get(self, key, default=None):
        read = self.app.read_config
        get = self.values.get
        k = '.'.join([self.app.name, key])
        return get(k, read('settings', key, self.defaults.get(key,default or '')))

class UserSettingsManager(SettingsManager):

    def __init__(self, settings, user, config):
        SettingsManager.__init__(self, user.username)
        self.user = user
        self.store = settings.user_settings_store
        self.values = settings._user_dict
        self.defaults = UserSystemSettings.defaults(config)

    def get(self, key, default=None):
        k = '.'.join([self.user.username, key])
        return self.values.get(k, self.defaults.get(k, default or ''))

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
        >>> myapp_settings.reset('theme')
        >>> myapp_settings.get('theme', 'came_out_blank')
        'came_out_blank'
        >>> myapp_settings.put('theme', 'sometheme')
        >>> myapp_settings.get('theme', 'came_out_blank')
        'sometheme'
        >>> myapp_settings.reset('theme')
        >>> myapp_settings.get('theme', 'came_out_blank')
        'came_out_blank'


    """

    def __init__(self, store, config, context):
        from .store import EntityStore
        self.db = store.db

        self.application_settings_store = EntityStore(self.db, ApplicationSettings)
        self._application_dict = {p.key: p.value for p in self.application_settings_store}

        self.user_settings_store = EntityStore(self.db, UserSystemSettings)
        self._user_dict = {p.key: p.value for p in self.user_settings_store}

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

    def app_settings(self, app, defaults):
        return AppSettingsManager(self, app, defaults)

    def user_settings(self, user, config):
        return UserSettingsManager(self, user, config)

    def refresh(self):
        config = self.config
        self.defaults = self.klass.defaults(config)
        self.values = dict((r['key'],r['value']) for r in self.store)

    def put(self, key, value):
        k = '.'.join((self.context,key))
        r = self.store.first(key=k)
        if not r:
            r = SystemSettings(key=k)
        r['value'] = value
        self.store.put(r)
        self.values[k] = value

    def set(self, key, value):
        return self.put(key, value)

    def get(self, key, default=None):
        k = '.'.join((self.context,key))
        return self.values.get(k, self.defaults.get(key, default) or default)

    def get_bool(self, key, default=''):
        return self.get(key, default).lower() in POSITIVE

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

