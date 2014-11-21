"""
    settings.py

    manages system and application settings
"""

from utils import Record #zoom.store import Record, EntityStore

default_system_settings = dict(
        site_name = 'Your Site',
        )

            #system.config.get('site','name','Your Site')

class SystemSettings(Record): pass

class Settings(object):
    """manage settings
        
        #>>> from zoom.store import set_mysql_log_state
        #>>> set_mysql_log_state(

        >>> from system import system
        >>> from store import EntityStore

        >>> system.setup_test()
        >>> settings_store = EntityStore(system.database, SystemSettings)
        >>> settings = Settings(settings_store, 'system')

        >>> settings.reset('site_name')
        >>> settings.get('site_name', 'no_site')
        'no_site'
        
        >>> settings.set('site_name', 'datazoomer.com')
        >>> settings.get('site_name', 'no_site')
        'datazoomer.com'

    """

    def __init__(self, store, context):
        self.store = store
        self.context = context

    def set(self, key, value):
        k = '.'.join((self.context,key))
        r = self.store.first(key=k)
        if not r:
            r = SystemSettings(key=k)
        r['value'] = value
        self.store.put(r)

    def get(self, key, default=None):
        k = '.'.join((self.context,key))
        r = self.store.first(key=k)
        if r:
            return r['value']
        return default or default_system_settings.get(key, None)

    def reset(self, key):
        k = '.'.join((self.context,key))
        self.store.delete(self.store.first(key=k))

    def save(self, settings):
        for key, value in settings.items():
            if value:
                self.set(key, value)

    def load(self):
        prefix = self.context + '.'
        return dict(
                (r['key'][len(prefix):],r['value']) 
                for r in self.store if r['key'].startswith(prefix))

