
import os 
from zoom import system, manager, page, markdown

def status_info():
    """Returns various system status variables for debugging purposes."""
    return '<pre>%s</pre>' % '<br>'.join([
        'user.............: %s' % user_id(),
        'username.........: %s' % username(),
        'nt_username......: %s' % system.nt_username,
        'ip...............: %s' % remote_addr(),
        'theme............: %s' % theme(),
        'roles............: %s' % user.roles,
        'apps.............: %s' % user.apps,
        'default..........: %s' % user.default_app,
        'date.............: %s' % tools.today,
        'now..............: %s' % tools.now,
        'route............: %s' % route,
        'webvars..........: %s' % webvars,
        'session..........: %s' % session,
        'authentication...: %s' % system.authentication,
        'user.is_anonymous: %s' % user.is_anonymous,
        'user.is_authenticated: %s' % user.is_authenticated,
        '\nrequest: %s'%str(request),
    ])

def view():
    d = system.__dict__

    lib_path = system.lib_path
    instance_path = system.instance_path
    site_path = system.config.site_path
    theme_path = system.themes_path
    app_paths = manager.app_paths

    return page(markdown("""
Paths
----
<pre>
lib_path......: %(lib_path)s
instance_path.: %(instance_path)s
site_path.....: %(site_path)s
theme_path....: %(theme_path)s
app_path......: %(app_paths)s
</pre>

Context
----
<dz:status_info>
    """) % locals(), title='Overview')
    
    
